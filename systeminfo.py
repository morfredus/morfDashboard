import socket
import shutil
import subprocess
from datetime import datetime

import psutil

import monitor_client

from config import (
    PROJECT_DIR,
    SERVICE_LABELS,
    NETWORK_SERVICES,
    NETWORK_PROBE_GRACE,
    BEACON_APPS,
    GREEN, RED, ORANGE, YELLOW, GRAY,
    CPU_WARNING, CPU_CRITICAL, CPU_ELEVATED,
    RAM_WARNING, RAM_CRITICAL,
    SWAP_WARNING, SWAP_CRITICAL,
    SSD_WARNING, SSD_CRITICAL,
    TEMP_WARNING, TEMP_CRITICAL,
    LOAD_WARNING, LOAD_CRITICAL,
    MONITOR_ENABLED, MONITOR_URL, MONITOR_TIMEOUT,
    health_color,
)

from beacon_listener import local_status as beacon_local_status

try:
    from reboot_alert import get_reboot_alert
except Exception:
    def get_reboot_alert():
        return {"active": False, "count": 0, "latest": None}


def _read_version():
    try:
        return (PROJECT_DIR / "VERSION").read_text().strip() or "dev"
    except Exception:
        return "dev"


VERSION = _read_version()


def _get_ip(interface: str):
    try:
        result = subprocess.check_output(
            ["ip", "-4", "addr", "show", interface],
            text=True
        )

        for line in result.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                return line.split()[1].split("/")[0]

    except Exception:
        pass

    return None


def _cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(float(f.read()) / 1000, 1)
    except Exception:
        return None


def _uptime_seconds():
    """Uptime système en secondes. Fail-open (grand nombre) si illisible."""
    try:
        with open("/proc/uptime") as f:
            return float(f.readline().split()[0])
    except Exception:
        return float("inf")


def _uptime():
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.readline().split()[0])

        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)

        if days:
            return f"{days}j {hours}h"

        return f"{hours}h {minutes}m"

    except Exception:
        return "?"
def _service_running(service: str):
    try:
        subprocess.check_output(
            ["systemctl", "is-active", "--quiet", service]
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _network_service_online(config: dict):
    """Vrai si une connexion TCP aboutit (ex. serveur web de l'ESP32)."""
    try:
        with socket.create_connection(
            (config["host"], config["port"]),
            timeout=config.get("timeout", 1.0),
        ):
            return True
    except OSError:
        return False


def _service_state(name: str, network_ready: bool = True):
    """État d'un service : sonde réseau si déclaré, sinon systemd.

    La sonde réseau résout un nom mDNS (« .local »), ce qui émet des
    requêtes multicast sur wlan0. On ne sonde que lorsque le réseau est
    « prêt » : une IP est présente ET l'uptime dépasse le délai de grâce.
    Cela évite de perturber la connexion WiFi pendant qu'elle s'établit
    au démarrage (au prix d'une puce MeteoHub qui verdit avec un léger
    délai après le boot).
    """
    if name in NETWORK_SERVICES:
        if not network_ready:
            return False
        return _network_service_online(NETWORK_SERVICES[name])
    return _service_running(name)


def _beacon_color(online: bool, state):
    """Couleur de la pastille d'une application supervisee par heartbeat."""
    if not online:
        return RED
    if state == "warning":
        return ORANGE
    if state == "error":
        return RED
    return GREEN


def _short_host(name):
    """Nom d'hôte comparable : minuscules, sans point final ni suffixe mDNS.

    `pi4fred`, `pi4fred.`, `pi4fred.local` désignent la même machine. On les
    ramène à `pi4fred` avant comparaison, sinon une sonde locale déclarée en
    `.local` passerait pour distante.
    """
    n = str(name).strip().lower().rstrip(".")
    return n[:-6] if n.endswith(".local") else n


def _is_local_host(host, local_host):
    """La sonde réseau vise-t-elle CETTE machine, ou un autre poste du parc ?

    morfMonitor sonde des services par nom d'hôte : certains pointent sur cette
    machine (`localhost`, son propre nom), d'autres sur des postes distants
    (pi4dev depuis pi4fred, par exemple). Le Dashboard étant exclusivement local,
    on ne garde que les sondes visant cette machine.

      - hôte vide          -> local par convention (une sonde sans hôte vise le
                              poste courant) ;
      - localhost / boucle -> local ;
      - même nom court que `local_host` (suffixe `.local` ignoré) -> local ;
      - tout le reste (autre nom, IP d'un autre poste) -> distant, écarté.
    """
    if not host:
        return True
    h = _short_host(host)
    if h in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return True
    if not local_host:
        return False
    return h == _short_host(local_host)


def _is_local_beacon(entry, local_host):
    """L'entrée beacon appartient-elle à CETTE installation locale ?

    morfDashboard est exclusivement local : il montre l'état de SA machine et des
    équipements du parc, jamais les services d'un autre poste. La distinction vient
    du champ `role` du protocole morfBeacon :

      - `host`   : un service tournant sur une machine généraliste. Il n'est local
                   que s'il tourne sur CETTE machine (host == hostname local).
      - `device` : un équipement autonome (MeteoHub, capteur ESP32). Il fait partie
                   du système local où qu'il soit vu, et reste donc affiché.

    Ainsi, sur le Dashboard de pi4fred, les services de pi4dev disparaissent (c'est
    à morfMonitor, pas au Dashboard, d'avoir la vue d'ensemble du parc), mais
    MeteoHub reste présent. Un poste éteint n'encombre plus l'écran local d'alertes
    qui ne le concernent pas.
    """
    if entry.get("role", "host") == "device":
        return True
    host = entry.get("host")
    return bool(host) and bool(local_host) and host.lower() == str(local_host).lower()


def _service_colors(services_section, local_host=None):
    """Traduit l'état fourni par morfMonitor en pastilles colorées.

    La couleur relève de la PRÉSENTATION : morfMonitor fournit des faits
    (actif / inactif / en attente), le Dashboard décide comment les montrer.
    C'est ce partage qui permet à d'autres interfaces d'afficher les mêmes
    données autrement, sans que morfMonitor ait à les connaître.

    `local_host` (nom d'hôte de cette machine, rapporté par morfMonitor) sert à
    ne garder que ce qui est LOCAL : les sondes réseau visant cette machine (voir
    `_is_local_host`) et, parmi les applications beacon, les services de cette
    machine et les équipements du parc (voir `_is_local_beacon`). Les services
    systemd, eux, sont collectés localement par morfMonitor : ils sont déjà tous
    locaux. Un autre poste du parc n'apparaît donc jamais sur cet écran ; c'est
    à morfMonitor d'avoir la vue d'ensemble.

    Dédoublonnage : un service morfSystem est déclaré À LA FOIS comme unité
    systemd ET comme application beacon dans morfsystem.json (les deux nourrissent
    la vue parc de morfMonitor). Sans filtrage, il apparaîtrait deux fois sur cet
    écran. On privilégie la ligne BEACON — nom d'app canonique (« morfDashboard »
    plutôt que le libellé systemd « DashBoard ») et état auto-rapporté par le
    service (un service qui se déclare dégradé passe en orange, ce que systemd,
    binaire actif/inactif, ne sait pas dire) — et on masque l'unité systemd
    qu'elle recouvre. Un service sans beacon (morfUpdate) garde sa ligne systemd ;
    un équipement sans unité (MeteoHub) garde sa ligne beacon. Convention du parc
    utilisée pour l'appariement : l'unité systemd est le nom d'app en minuscules
    (« morfdashboard » <-> « morfDashboard »).
    """
    out = []

    # Identités montrées via leur beacon (local, déclaré, activé) : les unités
    # systemd correspondantes seront masquées pour éviter le doublon.
    beacon_shown = set()
    for entry in services_section.get("beacon", []):
        if not entry.get("declared") or not entry.get("enabled", True):
            continue
        if not _is_local_beacon(entry, local_host):
            continue
        app = entry.get("app")
        if app:
            beacon_shown.add(str(app).strip().lower())

    for entry in services_section.get("systemd", []):
        if not entry.get("enabled", True):
            continue
        # Doublon avec une application beacon montrée : on garde la ligne beacon.
        if str(entry.get("unit", "")).strip().lower() in beacon_shown:
            continue
        out.append({
            "label": entry.get("label", entry.get("unit", "?")),
            "color": GREEN if entry.get("active") else RED,
        })
    for entry in services_section.get("network", []):
        if not entry.get("enabled", True):
            continue
        # Exclusivement local : une sonde réseau vers un AUTRE poste du parc ne
        # concerne pas cet écran (c'est le rôle de morfMonitor). On ne garde que
        # les sondes visant cette machine.
        if not _is_local_host(entry.get("host"), local_host):
            continue
        state = entry.get("state")
        # « pending » n'est pas « hors ligne » : la sonde attend simplement que
        # le WiFi se stabilise. L'afficher en rouge serait une fausse alerte.
        color = GREEN if entry.get("online") else (ORANGE if state == "pending" else RED)
        out.append({"label": entry.get("label", entry.get("name", "?")), "color": color})
    for entry in services_section.get("beacon", []):
        # Les applications entendues mais non déclarées ne sont pas affichées :
        # l'écran est petit, et la configuration reste la source de vérité de ce
        # qui mérite une pastille. Elles restent visibles dans l'API.
        if not entry.get("declared") or not entry.get("enabled", True):
            continue
        # Exclusivement local : on écarte les services des autres postes. Un poste
        # éteint (ses services) ne vient donc plus rougir l'écran local.
        if not _is_local_beacon(entry, local_host):
            continue
        out.append({
            "label": entry.get("label", entry.get("app", "?")),
            "color": GREEN if entry.get("online") else RED,
        })
    return out


def _get_system_info_local():

    disk = shutil.disk_usage("/")

    # Résolues une seule fois : servent aussi de feu vert à la sonde réseau.
    # On ne sonde (mDNS) que si une IP est présente ET que le système est
    # démarré depuis assez longtemps pour ne pas gêner l'association WiFi.
    eth = _get_ip("eth0")
    wifi = _get_ip("wlan0")
    network_ready = bool(eth or wifi) and _uptime_seconds() >= NETWORK_PROBE_GRACE

    # Services affiches : d'abord les services systeme/reseau (systemd + sondes
    # ESP32), puis les applications de bureau vues par heartbeat morfBeacon.
    # Chaque entree porte deja son libelle et sa couleur de pastille -> l'affichage
    # n'a plus qu'a les disposer.
    # Dedoublonnage systemd/beacon (voir `_service_colors`) : un service morf*
    # est declare comme unite systemd ET comme application beacon dans le fichier
    # partage. On privilegie la ligne beacon et on masque l'unite systemd de meme
    # identite (unite = nom d'app en minuscules). morfUpdate, sans beacon, garde
    # sa ligne systemd.
    beacon_shown = {str(app).strip().lower() for app in BEACON_APPS}
    services = []
    for key in SERVICE_LABELS:
        if str(key).strip().lower() in beacon_shown:
            continue
        online = _service_state(key, network_ready)
        services.append({
            "label": SERVICE_LABELS[key],
            "color": GREEN if online else RED,
        })
    # Exclusivement local, meme en mode degrade : on ne montre que l'instance
    # LOCALE d'une application beacon (service sur cette machine, ou equipement du
    # parc), jamais celle d'un autre poste. Un poste distant eteint ne rougit donc
    # pas l'ecran local. `local_status` filtre sur le nom d'hote de cette machine.
    local_host = socket.gethostname()
    for app, label in BEACON_APPS.items():
        online, state = beacon_local_status(app, local_host)
        services.append({
            "label": label,
            "color": _beacon_color(online, state),
        })

    return {

        "hostname": socket.gethostname(),

        "version": VERSION,

        "time": datetime.now().strftime("%H:%M:%S"),

        "eth": eth,

        "wifi": wifi,

        "cpu": psutil.cpu_percent(),

        "cpu_cores": psutil.cpu_count() or 1,

        "load": psutil.getloadavg(),

        "temp": _cpu_temp(),

        "ram_percent": psutil.virtual_memory().percent,

        "swap_percent": psutil.swap_memory().percent,

        "disk_percent": round(disk.used / disk.total * 100, 1),

        "disk_used_gb": round(disk.used / (1024**3), 1),

        "disk_free_gb": round(disk.free / (1024**3), 1),

        "disk_total_gb": round(disk.total / (1024**3), 1),

        "uptime": _uptime(),

        "reboot_alert": get_reboot_alert(),

        "services": services,
    }




def _monitor_answer_is_usable(data):
    """Une réponse de morfMonitor est-elle exploitable, ou faut-il replier ?

    Répondre n'est pas savoir. Si morfMonitor n'a pas chargé sa configuration
    (fichier partagé absent au démarrage, par exemple), il répond correctement
    mais ne supervise RIEN : ni service systemd, ni sonde réseau. L'accepter
    telle quelle vidait l'écran de ses pastilles — un affichage vide, sans la
    moindre alerte, alors que la collecte locale aurait très bien fonctionné.

    Une machine réellement dépourvue de composant supervisé n'existe pas en
    pratique : zéro service est donc le signe d'une réponse dégénérée, pas d'un
    état normal. On préfère le mode local, qui affiche au moins quelque chose.
    """
    services = data.get("services") or {}
    declared = len(services.get("systemd") or []) + len(services.get("network") or [])
    return declared > 0


def get_system_info():
    """Informations système, depuis morfMonitor si possible, sinon localement.

    Le repli est AUTOMATIQUE dans les deux sens : si morfMonitor est arrêté, en
    cours de démarrage, ou injoignable, le Dashboard reprend la collecte locale
    ; dès que le service répond de nouveau, il redevient la source. Aucun
    redémarrage du Dashboard n'est nécessaire, ce qui compte : c'est justement
    pendant un incident qu'on regarde l'écran.

    Le champ « source » permet de savoir d'un coup d'œil d'où viennent les
    données — indispensable au diagnostic, et discret à l'affichage.
    """
    if MONITOR_ENABLED:
        data = monitor_client.fetch_all(MONITOR_URL, MONITOR_TIMEOUT)
        if data and _monitor_answer_is_usable(data):
            # Le nom d'hôte local vient de morfMonitor lui-meme (il tourne sur
            # cette machine) : c'est l'autorite sur « qui suis-je », et il sert a
            # ne garder que les applications beacon locales.
            local_host = (data.get("system") or {}).get("hostname")
            info = monitor_client.to_dashboard_shape(
                data, lambda sec: _service_colors(sec, local_host))
            # Champs qui restent la propriété du Dashboard : sa version, son
            # horloge d'affichage, et son suivi d'accusé de redémarrage.
            info["version"] = VERSION
            info["time"] = datetime.now().strftime("%H:%M:%S")
            info["cpu_cores"] = psutil.cpu_count() or 1
            info["reboot_alert"] = get_reboot_alert()
            info["source"] = "morfMonitor"
            return info

    info = _get_system_info_local()
    info["source"] = "local"
    if MONITOR_ENABLED:
        info["source_error"] = monitor_client.last_error()
    return info


def overall_status(info):
    """État de santé global du système : 'ok', 'warning' ou 'critical'.

    Agrège les métriques système (via les mêmes seuils que l'affichage) et
    l'état des services/applications supervisés. Sert de pastille unique en
    mode veille : un coup d'œil suffit à savoir si tout va bien.
    """
    reds = oranges = 0

    checks = [
        (info.get("cpu"), CPU_WARNING, CPU_CRITICAL),
        (info.get("ram_percent"), RAM_WARNING, RAM_CRITICAL),
        (info.get("swap_percent"), SWAP_WARNING, SWAP_CRITICAL),
        (info.get("disk_percent"), SSD_WARNING, SSD_CRITICAL),
        (info.get("temp"), TEMP_WARNING, TEMP_CRITICAL),
    ]

    load = info.get("load")
    cores = info.get("cpu_cores", 1) or 1
    if load:
        checks.append((load[0] / cores * 100, LOAD_WARNING, LOAD_CRITICAL))

    for value, warning, critical in checks:
        color = health_color(value, warning, critical)
        if color == RED:
            reds += 1
        elif color == ORANGE:
            oranges += 1

    for svc in info.get("services", []):
        if svc.get("color") == RED:
            reds += 1
        elif svc.get("color") == ORANGE:
            oranges += 1

    if info.get("reboot_alert", {}).get("active"):
        oranges += 1  # reboot inattendu : attention, sans être critique

    if reds:
        return "critical"
    if oranges:
        return "warning"
    return "ok"


def _cpu_load_color(value):
    """Pastille de charge CPU à 4 niveaux : vert / jaune / orange / rouge."""
    if value is None:
        return GRAY
    if value >= CPU_CRITICAL:
        return RED
    if value >= CPU_WARNING:
        return ORANGE
    if value >= CPU_ELEVATED:
        return YELLOW
    return GREEN


def _services_color(services):
    """Pastille des services : vert si tous actifs, sinon orange (jamais rouge).

    Le service « Dashboard » lui-même est exclu : il tourne forcément puisque
    c'est lui qui affiche l'écran, donc son état n'apporte rien.
    """
    dashboard_label = SERVICE_LABELS.get("morfdashboard")
    relevant = [s for s in services if s.get("label") != dashboard_label]
    if all(s.get("color") == GREEN for s in relevant):
        return GREEN
    return ORANGE


def screensaver_status(info):
    """Trois couleurs de pastille pour l'écran de veille.

    Renvoie (thermique, charge CPU, services) — dans l'ordre d'affichage.
    """
    return (
        health_color(info.get("temp"), TEMP_WARNING, TEMP_CRITICAL),
        _cpu_load_color(info.get("cpu")),
        _services_color(info.get("services", [])),
    )


if __name__ == "__main__":

    from pprint import pprint

    info = get_system_info()
    pprint(info)
    print("État global :", overall_status(info))
    print("Pastilles veille (thermique, CPU, services) :", screensaver_status(info))

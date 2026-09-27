"""Client de morfMonitor : source privilégiée des informations système.

Pourquoi ce module existe
-------------------------
Le Dashboard interrogeait lui-même le système (psutil, /proc, systemctl, sondes
réseau). Cette logique vit désormais dans morfMonitor, qui la centralise pour
tout l'écosystème : plusieurs interfaces peuvent afficher les mêmes données sans
que chacune réimplémente la collecte.

Le Dashboard devient donc un consommateur. Mais il ne doit **jamais** dépendre de
morfMonitor pour fonctionner : un écran de supervision qui s'éteint parce que le
superviseur est arrêté est un contresens. D'où le mode dégradé, qui rebascule
automatiquement sur la collecte locale - et revient tout aussi automatiquement
au mode normal, sans redémarrage.

Ce module ne fait qu'une chose : récupérer les données de morfMonitor et les
traduire dans la forme attendue par l'affichage. Il ne décide pas du repli ;
c'est `systeminfo.get_system_info()` qui arbitre.
"""

import json
import time
import urllib.error
import urllib.request

# Adresse locale : morfMonitor tourne sur la même machine que le Dashboard.
# Passer par le réseau plutôt que par un appel direct est délibéré - c'est la
# même API que consommeront un dashboard web ou un ESP32, donc elle est
# exercée en permanence par le client le plus exigeant.
DEFAULT_URL = "http://127.0.0.1:8790"

# Court à dessein : on préfère basculer en mode local que faire attendre
# l'affichage. Le Dashboard rafraîchit souvent ; un blocage se verrait.
DEFAULT_TIMEOUT = 1.5

# Après un échec, on ne réessaie pas à chaque rafraîchissement : marteler un
# service arrêté ne le rallume pas et gèle l'affichage à chaque tentative.
RETRY_AFTER_S = 10.0

_last_failure = 0.0
_last_error = ""


def available_after_failure() -> bool:
    """Faut-il retenter, après un échec récent ?"""
    return (time.monotonic() - _last_failure) >= RETRY_AFTER_S


def last_error() -> str:
    return _last_error


def _fetch(url: str, timeout: float):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        if response.status != 200:
            raise OSError(f"HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def fetch_all(base_url: str = DEFAULT_URL, timeout: float = DEFAULT_TIMEOUT):
    """Récupère tout l'état en UNE requête, ou None si morfMonitor est injoignable.

    Une seule requête plutôt que cinq : le Dashboard veut un instantané cohérent,
    et cinq allers-retours donneraient des données prises à des instants
    différents en plus d'être plus lents.
    """
    global _last_failure, _last_error

    if not available_after_failure():
        return None

    try:
        data = _fetch(f"{base_url.rstrip('/')}/api/all", timeout)
        _last_error = ""
        return data
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        _last_failure = time.monotonic()
        _last_error = str(exc)
        return None


def _bytes_to_gb(value) -> float:
    try:
        return round(float(value) / (1024 ** 3), 1)
    except (TypeError, ValueError):
        return 0.0


def to_dashboard_shape(data, service_colors):
    """Traduit la réponse de morfMonitor dans la forme attendue par l'affichage.

    `service_colors(services_section)` est fourni par l'appelant : la couleur des
    pastilles relève de la présentation, qui reste au Dashboard. morfMonitor
    fournit des faits (actif / inactif), pas des choix graphiques - c'est
    précisément la séparation des responsabilités visée.
    """
    system = data.get("system", {})
    resources = data.get("resources", {})
    network = data.get("network", {})
    memory = resources.get("memory", {})
    swap = resources.get("swap", {})
    disk = resources.get("disk", {})
    temperature = resources.get("temperature", {})

    # Adresses IPv4 par interface, telles que le Dashboard les affiche.
    ips = {"eth0": None, "wlan0": None}
    for interface in network.get("interfaces", []):
        name = interface.get("name")
        addresses = interface.get("ipv4") or []
        if name in ips and addresses:
            ips[name] = addresses[0]

    uptime_s = int(system.get("uptime_s") or 0)
    days, rest = divmod(uptime_s, 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    uptime = f"{days}j {hours:02d}:{minutes:02d}" if days else f"{hours:02d}:{minutes:02d}"

    return {
        "hostname": system.get("hostname", "?"),
        "eth": ips["eth0"],
        "wifi": ips["wlan0"],
        "cpu": resources.get("cpu_percent", 0.0),
        "load": tuple(resources.get("load", [0, 0, 0])),
        "temp": temperature.get("cpu_c"),
        "ram_percent": memory.get("percent", 0.0),
        "swap_percent": swap.get("percent", 0.0),
        "disk_percent": disk.get("percent", 0.0),
        "disk_used_gb": _bytes_to_gb(disk.get("used_b")),
        "disk_free_gb": _bytes_to_gb(disk.get("free_b")),
        "disk_total_gb": _bytes_to_gb(disk.get("total_b")),
        "uptime": uptime,
        "services": service_colors(data.get("services", {})),
        # Cause du dernier redémarrage, que le Dashboard seul ne savait pas établir.
        "reboot_cause": data.get("reboot", {}),
    }

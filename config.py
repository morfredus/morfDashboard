import json
import os
import runpy
from pathlib import Path

# ---------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_DIR / "assets"
LOGO_FILE = ASSETS_DIR / "logo.png"
FONTS_DIR = ASSETS_DIR / "fonts"

# ---------------------------------------------------------------------
# Polices
# ---------------------------------------------------------------------
# DejaVu Sans Mono : police monospace nette, fournie dans le dépôt pour un
# rendu identique quel que soit l'OS. Le monospace garde les colonnes
# alignées (libellés/valeurs). Repli sur la police PIL par défaut si absente.

FONT_REGULAR = FONTS_DIR / "DejaVuSansMono.ttf"
FONT_BOLD = FONTS_DIR / "DejaVuSansMono-Bold.ttf"

FONT_SIZE = 14        # texte courant
TITLE_FONT_SIZE = 12  # bandeau supérieur (en gras)

# Rendu du texte — à juger sur l'écran réel.
FONT_ANTIALIAS = False  # False = bords nets sans lissage (parfois plus lisible en petit)
FONT_BODY_BOLD = True  # True = texte courant en gras (souvent plus lisible sur petit LCD)


def load_font(size=FONT_SIZE, bold=False):
    """Charge une police TrueType du dépôt ; repli sur la police par défaut."""
    from PIL import ImageFont
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()

# ---------------------------------------------------------------------
# Affichage
# ---------------------------------------------------------------------

WIDTH = 240
HEIGHT = 320

UPDATE_INTERVAL = 2

# Zone des services (bas de l'écran) : 6 emplacements. Au-delà, l'affichage
# défile automatiquement. Durée d'affichage d'une page, en secondes. Les
# services en alerte restent épinglés en tête (voir display.py).
SERVICES_ROTATE_SECONDS = 6

# Pilote d'écran : "ili9341", "st7789" ou "mock".
# "mock" ne touche aucun matériel : il écrit chaque image dans un PNG (et, en
# option, l'affiche dans une fenêtre). Utile pour développer sur un PC ou faire
# tourner le service sur une machine Linux SANS écran SPI, sans dépendre de
# spidev / RPi.GPIO (dont l'absence ferait planter le service en boucle).
# Surchargé par la variable d'environnement MORFDASHBOARD_DISPLAY_DRIVER : on
# peut ainsi forcer le mock sans éditer ce fichier (ex. sur un poste de dev).
# Enfin, screen.py bascule automatiquement sur le mock si le pilote matériel
# choisi ne peut pas s'importer (spidev/RPi.GPIO absents) : le service tourne
# quand même, au lieu de planter et redémarrer sans fin.
DISPLAY_DRIVER = os.environ.get("MORFDASHBOARD_DISPLAY_DRIVER", "st7789")

# --- Pilote mock (écran simulé) --------------------------------------
# Chemin du PNG où le mock écrit la dernière image affichée. Un client peut le
# lire pour voir « ce qu'il y aurait à l'écran ». Surchargeable par
# MORFDASHBOARD_MOCK_PNG. Repli sur un fichier temporaire si non inscriptible.
MOCK_PNG_PATH = Path(os.environ.get(
    "MORFDASHBOARD_MOCK_PNG",
    "/var/lib/morfsystem/morfdashboard/screen.png"))

# Fenêtre live du mock (Tkinter). Éteinte par défaut : un service tourne sans
# serveur graphique. Mettre MORFDASHBOARD_MOCK_WINDOW=1 pour l'activer sur un
# poste de dev avec écran. Sans interface graphique disponible, l'option est
# ignorée sans erreur (le PNG reste écrit).
MOCK_WINDOW = os.environ.get("MORFDASHBOARD_MOCK_WINDOW", "0") == "1"

# Décalage de la dalle ST7789 (0 pour un panneau 240 × 320 plein cadre ;
# certaines dalles 240 × 240 demandent un offset, ex. Y = 80).
ST7789_X_OFFSET = 0
ST7789_Y_OFFSET = 0

# Orientation ST7789 (registre MADCTL 0x36). Les panneaux diffèrent : si
# l'image est tête-bêche et/ou en miroir, essayer une de ces valeurs.
#   0x00  portrait
#   0xC0  portrait à 180° (tête-bêche)   ← essai n°1 si tête-bêche
#   0x80  miroir vertical (MY)
#   0x40  miroir horizontal (MX)
# Ajouter 0x08 (bit BGR) si le rouge et le bleu sont intervertis, ex. 0xC8.
ST7789_MADCTL = 0x00

# Inversion d'affichage ST7789. True = INVON (0x21), False = INVOFF (0x20).
# Si les couleurs sortent « en négatif », basculer cette valeur.
ST7789_INVERT = True

# ---------------------------------------------------------------------
# GPIO
# ---------------------------------------------------------------------

DC_PIN = 24
RST_PIN = 25
# CS = CE0 (GPIO 8) : géré en MATÉRIEL par le driver SPI (spidev, device 0).
# Ne pas le piloter via RPi.GPIO sous Bookworm/lgpio -> « GPIO not allocated ».
CS_PIN = 8
LED_PIN = 18

SPI_BUS = 0
SPI_DEVICE = 0
SPI_SPEED = 40_000_000

# ---------------------------------------------------------------------
# Rétroéclairage (backlight sur LED_PIN / GPIO18)
# ---------------------------------------------------------------------
# Le rétroéclairage est piloté par LED_PIN (GPIO18). En PWM on fait varier sa
# luminosité (0 = éteint, 100 = plein) ; sinon c'est du tout-ou-rien. Ici PWM
# LOGICIEL (RPi.GPIO), largement suffisant pour des paliers fixes. GPIO18 sait
# aussi faire du PWM MATÉRIEL (canal PWM0), mais y passer imposerait un pilote
# sysfs et « dtoverlay=pwm-2chan » dans /boot : à n'envisager que si un
# scintillement apparaît, inutile pour de simples niveaux discrets.
BACKLIGHT_PWM = True         # False = tout-ou-rien (>0 allumé, 0 éteint)
BACKLIGHT_FREQ_HZ = 1000     # fréquence du PWM logiciel

# Niveaux de rétroéclairage (%), librement paramétrables. Trois paliers
# couvrent tous les cas : présence, veille, et extinction volontaire.
BL_ACTIVE = 100    # présence détectée (ou forçage « on » via screenctl.py)
BL_STANDBY = 15    # veille (écran de veille anti-marquage)
BL_OFF = 0         # extinction manuelle (forçage « off » via screenctl.py)

# Ancien nom conservé pour compatibilité : les pilotes (st7789/ili9341)
# initialisent le PWM sur BACKLIGHT_FULL. Le garder aligné sur BL_ACTIVE.
BACKLIGHT_FULL = BL_ACTIVE

# ---------------------------------------------------------------------
# Mise en veille (écran de veille anti-marquage / économie d'énergie)
# ---------------------------------------------------------------------
# Sans capteur physique, la présence est déduite de l'activité SSH (voir
# activity.py). Après SCREENSAVER_IDLE_SECONDS sans activité, l'écran bascule
# sur un cadre minimal mobile (heure, uptime, état global du système) et le
# rétroéclairage descend à BL_STANDBY. La moindre activité SSH (frappe ou
# sortie d'une commande) réveille l'écran immédiatement.
SCREENSAVER_ENABLED = True       # False = dashboard permanent, jamais de veille
SCREENSAVER_IDLE_SECONDS = 60    # délai d'inactivité SSH avant la veille
SCREENSAVER_BACKLIGHT = BL_STANDBY  # compat : niveau (%) du rétroéclairage en veille

# ---------------------------------------------------------------------
# Commande manuelle du rétroéclairage (forçage auto / on / off)
# ---------------------------------------------------------------------
# En plus de la gestion automatique (présence -> BL_ACTIVE, veille -> BL_STANDBY),
# le rétroéclairage accepte un FORÇAGE manuel persistant, piloté hors ligne par
# la petite commande screenctl.py :
#     auto -> morfDashboard décide     on -> toujours allumé     off -> éteint
# Le mode vit dans ce fichier d'état (une ligne : auto|on|off), source de vérité
# relue à chaque tour de boucle. Doctrine FS morfSystem : l'état éditable vit
# sous /var/lib (StateDirectory systemd), jamais dans /etc (lecture seule) ni
# dans le code. Surchargeable par la variable d'environnement
# MORFDASHBOARD_BACKLIGHT_STATE (utile pour tester hors du Raspberry).
if os.name == "nt":
    _BACKLIGHT_STATE_DEFAULT = (
        Path(os.environ.get("ProgramData", r"C:\ProgramData"))
        / "morfsystem" / "morfdashboard" / "backlight.state"
    )
else:
    _BACKLIGHT_STATE_DEFAULT = Path("/var/lib/morfsystem/morfdashboard/backlight.state")

BACKLIGHT_STATE_FILE = Path(
    os.environ.get("MORFDASHBOARD_BACKLIGHT_STATE", str(_BACKLIGHT_STATE_DEFAULT))
)

# ---------------------------------------------------------------------
# Détection de présence par capteur (service morfSensor)
# ---------------------------------------------------------------------
# Source de réveil SUPPLÉMENTAIRE à l'activité SSH : un capteur de présence
# (radar LD2410C, etc.) géré par le service autonome « morfSensor ». Le dashboard
# ne pilote PAS le capteur : il interroge l'API HTTP de morfSensor à l'URL
# ci-dessous et lit le champ booléen « present ». Une présence détectée réveille
# l'écran comme le ferait une frappe SSH (voir presence_sensor.py + dashboard.py).
#
# morfSensor tourne en local sur le Raspberry (service systemd « morfsensor »).
# Si le service est absent ou injoignable, la détection est simplement ignorée :
# le comportement historique (réveil SSH seul) reste intact.
PRESENCE_SENSOR_ENABLED = True                              # False = ignorer le capteur
PRESENCE_SENSOR_URL = "http://127.0.0.1:8788/presence"     # endpoint /presence de morfSensor
PRESENCE_SENSOR_TIMEOUT = 0.5                              # s ; borne le temps d'attente HTTP

# ---------------------------------------------------------------------
# Bouton d'alimentation matériel (facultatif)
# ---------------------------------------------------------------------
# Un bouton-poussoir câblé entre POWER_BUTTON_PIN et la masse (pull-up interne)
# permet, sans clavier ni SSH :
#     appui COURT -> extinction propre (systemctl poweroff)
#     appui LONG  -> redémarrage propre (systemctl reboot)
# Voir power_button.py pour la logique, et docs/fr/CABLAGE.md pour le câblage et
# le sudoers requis.
#
# Le bouton est FACULTATIF et tout est tolérant à son absence. En logique
# active-basse avec pull-up interne, une ligne SANS bouton reste au niveau haut
# (« non pressé ») : rien ne se déclenche, donc aucun risque de redémarrage en
# boucle au départ, quand le bouton n'est pas encore monté. Par sécurité
# supplémentaire, power_button.py refuse d'agir sur une ligne déjà « pressée » au
# démarrage (câblage flottant ou bloqué) tant qu'un relâchement n'a pas été vu.
#
# GPIO3 (broche physique 5) est retenu par défaut : c'est une entrée libre sur
# pi4fred (voir CONVENTIONS-CABLAGE-PI4.md) et c'est le pin « réveil » du
# Raspberry Pi -> le MÊME bouton rallume le Pi après une extinction. Ce pin porte
# un pull-up matériel fixe (ligne I2C SDA au repos), ce qui renforce encore la
# sécurité anti-déclenchement au repos.
POWER_BUTTON_ENABLED = True            # False = fonction désactivée, aucun GPIO revendiqué
POWER_BUTTON_PIN = 3                   # BCM ; GPIO3 = broche physique 5 (réveil du Pi)
POWER_BUTTON_ACTIVE_LOW = True         # bouton entre le GPIO et la masse (pull-up interne)
POWER_BUTTON_LONG_PRESS_SECONDS = 3.0  # >= ce seuil = redémarrage ; en dessous = extinction
POWER_BUTTON_DEBOUNCE_SECONDS = 0.05   # anti-rebond : ignore les micro-parasites
POWER_BUTTON_POLL_SECONDS = 0.02       # granularité de lecture de l'état du bouton
# Le service tourne en utilisateur non-root : `sudo -n` échoue proprement (au lieu
# d'attendre un mot de passe) si le sudoers NOPASSWD n'est pas en place.
POWER_BUTTON_SHUTDOWN_CMD = ["sudo", "-n", "systemctl", "poweroff"]
POWER_BUTTON_REBOOT_CMD = ["sudo", "-n", "systemctl", "reboot"]

# ---------------------------------------------------------------------
# Alertes importantes via morfNotify
# ---------------------------------------------------------------------
# Le dashboard reste autonome : il POSTe vers morfNotify si disponible, avec
# timeout court et erreurs ignorees. morfNotify distribue ensuite vers la
# destination configuree (par defaut "email"). Une alerte n'est envoyee que si
# l'etat critique dure assez longtemps, ou si un service reste defaillant.

ALERT_NOTIFY_ENABLED = True
ALERT_NOTIFY_URL = "http://127.0.0.1:8789/notify"
ALERT_NOTIFY_TARGETS = ["email"]
ALERT_NOTIFY_TIMEOUT = 1.0

# Metriques critiques : attendre avant de prevenir pour eviter les pics brefs.
ALERT_MIN_DURATION_SECONDS = 5 * 60

# Services/applications hors ligne : alerte plus rapide, mais pas instantanee.
ALERT_SERVICE_MIN_DURATION_SECONDS = 2 * 60

# Rappel si le probleme persiste longtemps.
ALERT_REPEAT_COOLDOWN_SECONDS = 6 * 60 * 60

# Envoie un message de retour a la normale apres une alerte deja envoyee.
ALERT_RECOVERY_NOTIFY = True

# ---------------------------------------------------------------------
# Couleurs
# ---------------------------------------------------------------------

BLACK = "black"
WHITE = "white"
GRAY = "gray"
GREEN = "lightgreen"
RED = "red"
BLUE = "#0055A5"
ORANGE = "orange"
YELLOW = "yellow"
CYAN = "lightblue"

# ---------------------------------------------------------------------
# Seuils de santé (en %, sauf température en °C)
# ---------------------------------------------------------------------

CPU_WARNING = 70
CPU_CRITICAL = 90
CPU_ELEVATED = 50   # charge modérée (jaune) — pastille « charge CPU » de la veille

RAM_WARNING = 80
RAM_CRITICAL = 95

SWAP_WARNING = 20
SWAP_CRITICAL = 50

TEMP_WARNING = 65
TEMP_CRITICAL = 75

SSD_WARNING = 85
SSD_CRITICAL = 95

# Charge système, en % des cœurs (100 % = tous les cœurs pleinement occupés)
LOAD_WARNING = 100
LOAD_CRITICAL = 150

# ---------------------------------------------------------------------
# Alerte reboot non demandé
# ---------------------------------------------------------------------
# Le script de surveillance cree un dossier par reboot inattendu, par exemple :
# /home/morfredus/Logs/Boot_2026-07-12T15-19-07+02-00_pi4fred_d3ff81ab
# L'alerte ne tient compte que du dossier Boot_* correspondant au boot actuel.

REBOOT_ALERT_LOG_DIR = Path("/home/morfredus/Logs")
REBOOT_ALERT_PATTERNS = ("Boot_*",)
REBOOT_ALERT_BOOT_WINDOW_SECONDS = 10 * 60
REBOOT_ALERT_ACK_FILE = Path("/home/morfredus/Logs/.dashboard_reboot_ack")


def health_color(value, warning, critical):
    """Retourne la couleur de la pastille selon la valeur et ses seuils."""
    if value is None:
        return GRAY
    if value >= critical:
        return RED
    if value >= warning:
        return ORANGE
    return GREEN


# ---------------------------------------------------------------------
# Libellés d'affichage des services (clé -> nom lisible)
# ---------------------------------------------------------------------

SERVICE_LABELS = {
    "morfdashboard": "DashBoard",  # service systemd local (systemctl is-active)
    "morfsync": "morfSync",        # service systemd local (Syncronisation de données)
    "morfsensor": "morfSensor",    # service systemd local (Ecoute de capteurs)
    "morfnotify": "morfNotify",  # service systemd local (Notifications)
    "morfanalytics": "morfAnalytics",  # service systemd local (Analyse de données)
}

# Services surveillés par sonde réseau plutôt que par systemd.
# MeteoHub tourne sur un ESP32 : on ne peut pas l'interroger avec
# « systemctl », on teste donc l'accès à son serveur web.
NETWORK_SERVICES = {
#    "gatewaylab": {
#        "host": "gatewaylab.local",  # nom mDNS ou IP fixe de l'ESP32
#        "port": 80,
#        "timeout": 1.0,            # secondes ; borne le temps d'attente si hors ligne
#    },
#    "meteohub": {
#        "host": "meteohub.local",  # nom mDNS ou IP fixe de l'ESP32
#        "port": 80,
#        "timeout": 1.0,            # secondes ; borne le temps d'attente si hors ligne
#    },
}

# Délai de grâce avant la première sonde réseau (secondes d'uptime système).
# La sonde résout un nom mDNS (requêtes multicast sur wlan0) : on attend que
# le WiFi soit associé et stabilisé pour ne pas perturber sa connexion au
# démarrage. La puce MeteoHub reste rouge tant que ce délai n'est pas écoulé.
NETWORK_PROBE_GRACE = 45

# ---------------------------------------------------------------------
# Supervision des applications de bureau par heartbeat (morfBeacon)
# ---------------------------------------------------------------------
# Les applications de bureau (ComponentHub, SiteWatch, et les futurs outils)
# diffusent un petit datagramme UDP « je suis actif » en broadcast sur le LAN
# (protocole morfBeacon). Le dashboard se contente d'ECOUTER : aucune IP a
# connaitre, aucune sonde, decouverte automatique. Une application qui n'emet
# plus pendant BEACON_OFFLINE_AFTER secondes est consideree hors ligne.

# Port UDP commun a tout le parc (identique cote applications).
BEACON_PORT = 45454

# Delai sans heartbeat avant de declarer une application hors ligne (secondes).
BEACON_OFFLINE_AFTER = 60

# Le dashboard s'annonce lui-meme (protocole morfbeacon/1) et sert un /status
# minimal sur ce port. Attribue par le registre d'adressage du parc :
# 'ports.allocations' dans morfTools/ecosystem.json. Voisin de morfMonitor
# (8790), avec qui il forme une paire : l'un collecte, l'autre affiche.
BEACON_ANNOUNCE = True
BEACON_STATUS_PORT = 8791

# Applications a surveiller : cle = nom annonce dans le heartbeat (champ "app"),
# valeur = libelle affiche a l'ecran.
# POUR AJOUTER UN FUTUR PROJET : ajouter une ligne ici, rien d'autre a modifier.
# (Le libelle est tronque a l'affichage s'il est trop long -> le garder court.)
BEACON_APPS = {
    #"ComponentHub": "ComponentHub",
    #"SiteWatch":    "SiteWatch",
    # "GatewayLab": "GatewayLab",
    # "MonOutil":   "Mon outil",
}


# ---------------------------------------------------------------------
# Configuration PARTAGEE avec morfMonitor
# ---------------------------------------------------------------------
# Les listes ci-dessus (SERVICE_LABELS, NETWORK_SERVICES, BEACON_APPS) sont
# desormais des VALEURS DE REPLI. La source de verite est le fichier partage
# /etc/morfsystem/morfsystem.json, lu aussi bien par morfMonitor (C++) que par
# ce Dashboard (Python).
#
# Pourquoi : tant que chaque programme portait sa propre liste, ajouter un
# service demandait de modifier du code a deux endroits, avec la certitude
# qu'ils finiraient par diverger. Desormais, ajouter un composant ne demande
# QUE d'editer ce fichier.
#
# Le repli reste indispensable : si le fichier partage est absent (installation
# partielle, machine sans morfMonitor), le Dashboard doit continuer d'afficher
# quelque chose plutot que de se retrouver sans aucun service a surveiller.

_MORFSYSTEM_DEFAULT_CONFIG = (
    Path(os.environ.get("ProgramData", r"C:\ProgramData"))
    / "morfsystem" / "morfsystem.json"
    if os.name == "nt"
    else Path("/etc/morfsystem/morfsystem.json")
)
MORFSYSTEM_CONFIG = os.environ.get(
    "MORFSYSTEM_CONFIG", str(_MORFSYSTEM_DEFAULT_CONFIG))

# Acces a morfMonitor. Mettre MONITOR_ENABLED a False force le mode local.
MONITOR_ENABLED = True
MONITOR_URL = "http://127.0.0.1:8790"
MONITOR_TIMEOUT = 1.5


def _load_shared_config():
    """Remplace les listes locales par celles du fichier partage, s'il existe."""
    global SERVICE_LABELS, NETWORK_SERVICES, BEACON_APPS
    global BEACON_PORT, BEACON_OFFLINE_AFTER, NETWORK_PROBE_GRACE

    path = Path(MORFSYSTEM_CONFIG)
    if not path.is_file():
        return False
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        print(f"Configuration partagee ignoree ({path}) : {exc}")
        return False

    services = data.get("systemd_services")
    if isinstance(services, list):
        SERVICE_LABELS = {
            entry["unit"]: entry.get("label", entry["unit"])
            for entry in services
            if entry.get("unit") and entry.get("enabled", True)
        }

    network = data.get("network_services")
    if isinstance(network, list):
        NETWORK_SERVICES = {
            entry["name"]: {
                "host": entry.get("host", ""),
                "port": entry.get("port", 80),
                # Le fichier partage exprime les delais en millisecondes ; le
                # Dashboard raisonne en secondes.
                "timeout": entry.get("timeout_ms", 1000) / 1000.0,
            }
            for entry in network
            if entry.get("name") and entry.get("enabled", True)
        }

    apps = data.get("beacon_apps")
    if isinstance(apps, list):
        BEACON_APPS = {
            entry["app"]: entry.get("label", entry["app"])
            for entry in apps
            if entry.get("app") and entry.get("enabled", True)
        }

    beacon = data.get("beacon") or {}
    BEACON_PORT = beacon.get("port", BEACON_PORT)
    BEACON_OFFLINE_AFTER = beacon.get("offline_after_s", BEACON_OFFLINE_AFTER)
    NETWORK_PROBE_GRACE = data.get("network_probe_grace_s", NETWORK_PROBE_GRACE)
    return True


SHARED_CONFIG_LOADED = _load_shared_config()


def _load_local_config():
    """Charge des surcharges locales sans modifier le fichier versionne."""
    candidates = []
    env_path = os.environ.get("MORFDASHBOARD_CONFIG")
    if env_path:
        candidates.append(Path(env_path))
    candidates.append(Path("/etc/morfsystem/morfdashboard/config.local.py"))
    candidates.append(PROJECT_DIR / "config.local.py")

    for path in candidates:
        if not path.is_file():
            continue
        try:
            values = runpy.run_path(str(path))
        except Exception as exc:
            print(f"Configuration locale ignoree ({path}) : {exc}")
            return
        for key, value in values.items():
            if not key.isupper():
                continue

            # Les listes de services sont extensibles localement : une ancienne
            # config locale ne doit pas masquer les services ajoutés au défaut
            # lors d'une mise à jour. Une clé locale existante garde néanmoins
            # la priorité, pour permettre de personnaliser son libellé/sa sonde.
            default = globals().get(key)
            if isinstance(default, dict) and isinstance(value, dict):
                globals()[key] = {**default, **value}
            else:
                globals()[key] = value
        return


_load_local_config()

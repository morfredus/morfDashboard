"""
backlight_control.py
Forçage manuel du rétroéclairage (mode auto / on / off).

morfDashboard pilote normalement le rétroéclairage tout seul : plein (BL_ACTIVE)
en présence, réduit (BL_STANDBY) en veille. Ce module ajoute par-dessus une
COMMANDE MANUELLE persistante, indépendante de cette logique automatique :

    auto -> morfDashboard décide (présence -> BL_ACTIVE, veille -> BL_STANDBY)
    on   -> forçage allumé  (BL_ACTIVE) : la veille n'éteint plus l'écran
    off  -> forçage éteint  (BL_OFF = 0) : écran volontairement noir

Le mode vit dans un petit fichier texte (une seule ligne : auto|on|off), source
de vérité persistante et lisible/éditable à la main. Pas de serveur, pas de
port : la commande de l'écran est strictement locale à la machine. La CLI
screenctl.py écrit ce fichier, la boucle de dashboard.py le relit à chaque tour.

Robuste par construction : toute erreur de lecture retombe sur « auto », pour
qu'un fichier absent, vide ou corrompu ne laisse jamais l'écran coincé éteint.
"""

from config import BL_ACTIVE, BL_STANDBY, BL_OFF, BACKLIGHT_STATE_FILE

# Les trois modes de forçage. « auto » est le comportement historique.
MODE_AUTO = "auto"
MODE_ON = "on"
MODE_OFF = "off"
VALID_MODES = (MODE_AUTO, MODE_ON, MODE_OFF)


def read_mode(path=BACKLIGHT_STATE_FILE):
    """Retourne le mode de forçage courant.

    Retombe sur « auto » dès que le fichier est absent, illisible ou contient
    une valeur inattendue : un état corrompu ne doit jamais laisser l'écran
    éteint sans issue. Ne lève jamais d'exception (sûr dans la boucle).
    """
    try:
        mode = path.read_text(encoding="utf-8").strip().lower()
    except OSError:
        return MODE_AUTO
    return mode if mode in VALID_MODES else MODE_AUTO


def set_mode(mode, path=BACKLIGHT_STATE_FILE):
    """Écrit le mode de forçage dans le fichier d'état.

    Crée le dossier d'état au besoin. Lève ValueError si le mode est inconnu, et
    laisse remonter les erreurs d'écriture (permissions, disque) pour que la CLI
    les signale clairement plutôt que d'échouer en silence.
    """
    mode = mode.strip().lower()
    if mode not in VALID_MODES:
        raise ValueError(
            f"mode inconnu : {mode!r} (attendu : {', '.join(VALID_MODES)})"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(mode + "\n", encoding="utf-8")


def effective_backlight(asleep, mode=None):
    """Niveau de rétroéclairage (0-100) résultant du mode et de l'état de veille.

    - off  -> BL_OFF, quelle que soit la veille (écran volontairement noir)
    - on   -> BL_ACTIVE, la veille n'atténue pas
    - auto -> BL_STANDBY en veille, BL_ACTIVE sinon (comportement historique)

    `asleep` : True si la logique de veille (inactivité SSH) est active.
    `mode`   : forcé explicitement pour les tests ; sinon relu du fichier d'état.
    """
    if mode is None:
        mode = read_mode()
    if mode == MODE_OFF:
        return BL_OFF
    if mode == MODE_ON:
        return BL_ACTIVE
    return BL_STANDBY if asleep else BL_ACTIVE

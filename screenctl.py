#!/usr/bin/env python3
"""
screenctl.py
Commande manuelle du rétroéclairage de morfDashboard.

    screenctl.py on       forçage allumé (l'écran reste à pleine lumière)
    screenctl.py off      forçage éteint (écran volontairement noir)
    screenctl.py auto     rend la main à la gestion automatique (présence/veille)
    screenctl.py status   affiche le mode courant

Écrit une seule ligne (auto|on|off) dans le fichier d'état partagé avec le
service (voir backlight_control.py + config.BACKLIGHT_STATE_FILE). Le service
relit ce fichier à chaque tour de boucle : la commande prend effet en moins de
UPDATE_INTERVAL secondes, sans redémarrer le service.

Strictement local : aucune requête réseau, aucun port ouvert. Pilotable depuis
le Raspberry en SSH, ou via un alias shell. Le forçage « off » persiste tant
que « on » ou « auto » n'a pas été demandé, y compris après un redémarrage.
"""

import sys

from config import BACKLIGHT_STATE_FILE, BL_ACTIVE, BL_STANDBY, BL_OFF
from backlight_control import (
    read_mode,
    set_mode,
    MODE_AUTO,
    MODE_ON,
    MODE_OFF,
    VALID_MODES,
)

USAGE = "usage : screenctl.py {on|off|auto|status}"

# Description lisible de chaque mode, avec le niveau concret associé.
_DESCRIPTIONS = {
    MODE_AUTO: f"gestion automatique (présence {BL_ACTIVE}% / veille {BL_STANDBY}%)",
    MODE_ON: f"forçage allumé ({BL_ACTIVE}%)",
    MODE_OFF: f"forçage éteint ({BL_OFF}%)",
}


def _print_status():
    """Affiche le mode courant et l'emplacement du fichier d'état."""
    mode = read_mode()
    print(f"mode : {mode} - {_DESCRIPTIONS[mode]}")
    print(f"état : {BACKLIGHT_STATE_FILE}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(USAGE, file=sys.stderr)
        return 2

    action = argv[0].strip().lower()

    if action == "status":
        _print_status()
        return 0

    if action not in VALID_MODES:
        print(f"commande inconnue : {action!r}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return 2

    try:
        set_mode(action)
    except PermissionError:
        # Le dossier d'état appartient au user du service (StateDirectory).
        # Si la CLI tourne sous un autre compte, l'écriture est refusée.
        print(f"Écriture refusée sur {BACKLIGHT_STATE_FILE}.", file=sys.stderr)
        print("Réessayer avec sudo, ou vérifier le propriétaire du dossier "
              "d'état (StateDirectory du service morfdashboard).", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Impossible d'écrire l'état ({BACKLIGHT_STATE_FILE}) : {exc}",
              file=sys.stderr)
        return 1

    print(f"mode : {action} - {_DESCRIPTIONS[action]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

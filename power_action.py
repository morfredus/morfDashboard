"""
power_action.py
Passage de consigne entre le thread du bouton d'alimentation et l'affichage.

Le bouton (power_button.py) tourne dans un thread dédié, mais l'écran SPI est la
propriété EXCLUSIVE de la boucle principale (dashboard.py) : deux threads qui
écrivent sur le même bus SPI se corrompraient. Le bouton ne dessine donc jamais ;
il DEMANDE l'affichage d'un avis (« Arrêt » / « Redémarrage »), que la boucle
principale rend, puis il attend confirmation d'affichage avant de couper.

Contrat minimal, sans dépendance :
  - request(action)      : le bouton pose la consigne ("shutdown" | "reboot").
  - pending()            : la boucle lit la consigne courante (ou None).
  - mark_displayed()     : la boucle signale que l'avis est à l'écran.
  - wait_displayed(t)    : le bouton attend cet affichage (borné par un timeout).
"""

import threading

_lock = threading.Lock()
_action = None                       # None | "shutdown" | "reboot"
_displayed = threading.Event()


def request(action):
    """Le bouton demande l'affichage d'un avis d'arrêt/redémarrage."""
    global _action
    with _lock:
        _action = action
    _displayed.clear()


def pending():
    """Consigne courante pour la boucle d'affichage, ou None."""
    with _lock:
        return _action


def mark_displayed():
    """La boucle principale a affiché l'avis : le bouton peut couper."""
    _displayed.set()


def wait_displayed(timeout):
    """Le bouton attend que l'avis soit à l'écran, sans jamais bloquer trop longtemps."""
    return _displayed.wait(timeout)

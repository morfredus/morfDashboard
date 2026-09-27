"""
presence_sensor.py
Détection de présence déléguée au service morfSensor.

Le dashboard ne gère AUCUN capteur directement : il interroge l'API HTTP du
service autonome morfSensor (endpoint /presence) et lit le champ booléen
« present ». C'est la source de réveil « en plus » de l'activité SSH
(voir activity.py) : passer devant le capteur LD2410C rallume l'écran.

Conçu pour être appelé dans la boucle du dashboard : robuste et non bloquant au
sens où toute erreur (service arrêté, timeout, JSON inattendu) est avalée et
renvoie False - jamais d'exception qui casserait l'affichage. Aucune dépendance
externe (bibliothèque standard seule).
"""

import json
import urllib.request

from config import (
    PRESENCE_SENSOR_ENABLED,
    PRESENCE_SENSOR_URL,
    PRESENCE_SENSOR_TIMEOUT,
)


def presence_detected(url=PRESENCE_SENSOR_URL, timeout=PRESENCE_SENSOR_TIMEOUT):
    """True si morfSensor rapporte une présence, False sinon (ou si injoignable).

    N'effectue aucune requête si la détection est désactivée globalement
    (PRESENCE_SENSOR_ENABLED = False).
    """
    if not PRESENCE_SENSOR_ENABLED:
        return False
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return bool(data.get("present", False))
    except Exception:
        # Service absent, timeout, réseau, JSON invalide... : on ignore
        # silencieusement et on retombe sur le seul réveil SSH.
        return False


if __name__ == "__main__":
    if not PRESENCE_SENSOR_ENABLED:
        print("Détection de présence désactivée (PRESENCE_SENSOR_ENABLED = False).")
    elif presence_detected():
        print(f"Présence détectée via {PRESENCE_SENSOR_URL}")
    else:
        print(f"Aucune présence (ou morfSensor injoignable) sur {PRESENCE_SENSOR_URL}")

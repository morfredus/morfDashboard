
"""
dashboard.py
Point d'entrée du Dashboard Raspberry.
"""

import time

from boot import BootScreen
from display import DashboardDisplay
from screensaver import ScreenSaver
from screen import Display
from systeminfo import get_system_info, screensaver_status, VERSION
from activity import last_terminal_activity
from presence_sensor import presence_detected
from beacon_listener import start as start_beacon
import beacon_emitter
from alert_notifier import AlertNotifier
from backlight_control import read_mode, effective_backlight
from config import (
    UPDATE_INTERVAL,
    SCREENSAVER_ENABLED,
    SCREENSAVER_IDLE_SECONDS,
    PRESENCE_SENSOR_ENABLED,
    BEACON_PORT,
    BEACON_ANNOUNCE,
    BEACON_STATUS_PORT,
)


def main():

    lcd = Display()
    ui = DashboardDisplay()
    saver = ScreenSaver()
    alerts = AlertNotifier()

    # Evite de renvoyer la meme consigne de luminosite a chaque tour de boucle :
    # on ne pilote le retroeclairage que lorsque le niveau change reellement.
    current_backlight = None

    def set_backlight(level):
        nonlocal current_backlight
        if level != current_backlight:
            lcd.set_backlight(level)
            current_backlight = level

    # Ecoute des heartbeats morfBeacon (ComponentHub, SiteWatch, futurs outils)
    # en tache de fond, des le demarrage : la presence est prete des le 1er rendu.
    start_beacon()

    # Le dashboard s'annonce a son tour : il etait le seul service du parc a
    # n'exister que comme consommateur, donc invisible dans l'Ecosysteme de
    # morfMonitor. Emetteur + /status minimal, non bloquant.
    if BEACON_ANNOUNCE:
        beacon_emitter.start(VERSION, BEACON_STATUS_PORT, BEACON_PORT)

    try:
        # Animation de démarrage
        BootScreen().play(lcd)
        # Applique tout de suite le niveau effectif (au boot on n'est pas en
        # veille) : un forçage « off » posé avant un redémarrage éteint l'écran
        # dès la fin de l'animation, sans attendre le premier tour de boucle.
        set_backlight(effective_backlight(asleep=False))

        # Grace au demarrage : on part comme si une activite venait d'avoir lieu,
        # pour afficher le dashboard des le boot et ne basculer en veille qu'apres
        # SCREENSAVER_IDLE_SECONDS reels sans activite SSH.
        last_active = time.time()

        # Boucle principale
        while True:

            info = get_system_info()
            alerts.process(info)

            # Tout mtime de pseudo-terminal plus recent que notre dernier releve
            # = quelqu'un travaille en SSH -> le systeme est actif maintenant.
            activity_ts = last_terminal_activity()
            if activity_ts > last_active:
                last_active = activity_ts

            # Source de reveil SUPPLEMENTAIRE : le capteur de presence (LD2410C)
            # expose par le service morfSensor. Une presence detectee compte
            # comme une activite -> l'ecran se rallume. Non bloquant, tolerant a
            # l'absence du service (voir presence_sensor.py).
            if PRESENCE_SENSOR_ENABLED and presence_detected():
                last_active = time.time()

            idle = time.time() - last_active

            # Mise en veille : declenchee par l'inactivite SSH (voir activity.py).
            # Desactivable globalement via SCREENSAVER_ENABLED.
            asleep = SCREENSAVER_ENABLED and idle >= SCREENSAVER_IDLE_SECONDS

            # Le CONTENU reste piloté par la veille (dashboard vs cadre mobile
            # anti-marquage), indépendamment du forçage manuel : même en forçage
            # « on », l'écran de veille continue de bouger pour éviter le
            # marquage. Le forçage n'agit que sur la LUMINOSITE.
            if asleep:
                image = saver.render(info, screensaver_status(info))
            else:
                image = ui.render(info)

            lcd.display_image(image)

            # Niveau effectif = combinaison du mode manuel (auto/on/off, relu du
            # fichier d'état à chaque tour) et de l'état de veille. La commande
            # screenctl.py prend donc effet en un tour de boucle, sans redémarrage.
            set_backlight(effective_backlight(asleep, read_mode()))

            time.sleep(UPDATE_INTERVAL)

    except KeyboardInterrupt:
        print("Arrêt demandé.")

    finally:
        lcd.clear("black")
        lcd.close()


if __name__ == "__main__":
    main()

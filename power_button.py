"""
power_button.py
Bouton d'alimentation matériel optionnel du Dashboard.

Un bouton-poussoir câblé entre un GPIO et la masse (pull-up interne) permet, sans
clavier ni SSH :
  - appui COURT -> extinction propre du système (systemctl poweroff) ;
  - appui LONG  -> redémarrage propre du système (systemctl reboot).

Le bouton est FACULTATIF. Tout est tolérant à son absence :
  - POWER_BUTTON_ENABLED = False -> fonction désactivée, aucun GPIO revendiqué ;
  - RPi.GPIO absent (machine de dev, Windows) -> module inerte, jamais d'exception ;
  - bouton non câblé alors que la fonction est active -> la ligne reste au repos
    (tirée au niveau haut), donc il ne se passe rien : activer la fonction sans
    bouton branché est sans effet, jamais dangereux.

L'action (court/long) est décidée au RELÂCHEMENT, d'après la durée d'appui : c'est
déterministe et sans ambiguïté (un maintien n'enchaîne jamais les deux actions).
La surveillance tourne dans un thread démon dédié : la boucle d'affichage
(dashboard.py, cadencée à UPDATE_INTERVAL) est bien trop lente pour chronométrer
un appui, et ne doit jamais être bloquée par une lecture de bouton.

Le système est éteint/redémarré via `sudo -n systemctl poweroff|reboot`. Le
service tourne en utilisateur non-root : autoriser ces deux commandes précises
sans mot de passe via un fichier sudoers dédié (voir docs/fr/CABLAGE.md).
"""

import subprocess
import threading
import time

from config import (
    POWER_BUTTON_ENABLED,
    POWER_BUTTON_PIN,
    POWER_BUTTON_ACTIVE_LOW,
    POWER_BUTTON_LONG_PRESS_SECONDS,
    POWER_BUTTON_DEBOUNCE_SECONDS,
    POWER_BUTTON_POLL_SECONDS,
    POWER_BUTTON_SHUTDOWN_CMD,
    POWER_BUTTON_REBOOT_CMD,
)

_PREFIX = "[power_button]"


def _run_system_action(command, label):
    """Lance une commande système (extinction/redémarrage) et journalise un échec.

    Ne lève jamais : un bouton qui n'arrive pas à éteindre doit laisser une trace
    lisible dans le journal, pas planter le thread ni le dashboard.
    """
    print(f"{_PREFIX} {label} demandé : {' '.join(command)}", flush=True)
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except Exception as exc:  # exécutable introuvable, etc.
        print(f"{_PREFIX} échec du {label} : {exc}", flush=True)
        return
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        print(f"{_PREFIX} échec du {label} (code {result.returncode}) : {detail}", flush=True)
        print(f"{_PREFIX} vérifier le sudoers NOPASSWD (voir docs/fr/CABLAGE.md).", flush=True)


class _PowerButton:
    """Surveille l'état d'un GPIO d'entrée et déclenche l'action au relâchement."""

    def __init__(self, gpio):
        self._gpio = gpio
        # Une seule action par vie du service : une fois l'extinction ou le
        # redémarrage lancé, le système part de toute façon.
        self._fired = False

    def _pressed(self):
        """True quand le bouton est enfoncé, selon la logique câblée."""
        low = self._gpio.input(POWER_BUTTON_PIN) == self._gpio.LOW
        return low if POWER_BUTTON_ACTIVE_LOW else not low

    def run(self):
        # Garde-fou anti-boucle : ne JAMAIS agir sur un bouton déjà « pressé » au
        # démarrage. Sans bouton branché (cas initial), la ligne est tirée au
        # niveau de repos et cette garde passe aussitôt. Mais si la ligne est
        # flottante, bloquée ou mal câblée, elle pourrait sembler « pressée » en
        # continu : on n'arme la détection qu'APRÈS avoir observé un relâchement,
        # sinon chaque redémarrage relancerait aussitôt une extinction/redémarrage.
        if self._pressed():
            print(f"{_PREFIX} ligne active au démarrage (bouton bloqué ou mal câblé ?) : "
                  f"en attente d'un relâchement avant d'armer.", flush=True)
            while self._pressed():
                time.sleep(POWER_BUTTON_POLL_SECONDS)

        while not self._fired:
            if not self._pressed():
                time.sleep(POWER_BUTTON_POLL_SECONDS)
                continue
            # Anti-rebond : confirmer que l'appui tient au-delà du bruit.
            time.sleep(POWER_BUTTON_DEBOUNCE_SECONDS)
            if not self._pressed():
                continue
            start = time.monotonic()
            # Attendre le relâchement, en restant réactif.
            while self._pressed():
                time.sleep(POWER_BUTTON_POLL_SECONDS)
            held = time.monotonic() - start
            self._fired = True
            if held >= POWER_BUTTON_LONG_PRESS_SECONDS:
                _run_system_action(list(POWER_BUTTON_REBOOT_CMD), "redémarrage")
            else:
                _run_system_action(list(POWER_BUTTON_SHUTDOWN_CMD), "extinction")


def start():
    """Démarre la surveillance du bouton dans un thread démon.

    Retourne le thread, ou None si la fonction est désactivée ou si le GPIO n'est
    pas disponible (machine sans RPi.GPIO, GPIO déjà pris...). Ne lève jamais :
    l'absence de bouton ne doit jamais empêcher le dashboard de démarrer.
    """
    if not POWER_BUTTON_ENABLED:
        return None
    try:
        import RPi.GPIO as GPIO
    except Exception:
        # Machine de dev / Windows : pas de GPIO, fonction simplement absente.
        print(f"{_PREFIX} RPi.GPIO indisponible : bouton d'alimentation ignoré.", flush=True)
        return None
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        pull = GPIO.PUD_UP if POWER_BUTTON_ACTIVE_LOW else GPIO.PUD_DOWN
        GPIO.setup(POWER_BUTTON_PIN, GPIO.IN, pull_up_down=pull)
    except Exception as exc:
        print(f"{_PREFIX} configuration du GPIO {POWER_BUTTON_PIN} impossible : {exc}", flush=True)
        return None
    thread = threading.Thread(target=_PowerButton(GPIO).run, name="power-button", daemon=True)
    thread.start()
    print(f"{_PREFIX} actif sur GPIO{POWER_BUTTON_PIN} (appui court = extinction, "
          f"appui long >= {POWER_BUTTON_LONG_PRESS_SECONDS:g}s = redémarrage).", flush=True)
    return thread


if __name__ == "__main__":
    if start() is None:
        print("Bouton d'alimentation désactivé ou GPIO indisponible.")
    else:
        print("Surveillance du bouton d'alimentation... Ctrl-C pour quitter.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

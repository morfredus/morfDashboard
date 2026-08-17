
"""
screen.py
Sélection du pilote d'écran selon la configuration.

Le reste du projet importe « Display » depuis ce module et ignore quel pilote
matériel (ILI9341, ST7789) ou simulé (mock) est réellement utilisé.

Repli automatique : si le pilote matériel choisi ne peut pas s'importer (spidev
ou RPi.GPIO absents, cas d'une machine Linux sans écran SPI), on bascule sur le
pilote « mock » plutôt que de laisser le service planter et redémarrer en boucle.
Un ImportError signale précisément l'absence des bibliothèques matérielles :
c'est exactement le cas « pas d'écran ici », où le mock est le bon comportement.
"""

from config import DISPLAY_DRIVER


def _load_hardware(driver):
    """Importe le pilote matériel demandé. Lève ImportError si indisponible."""
    if driver == "st7789":
        from st7789 import Display
        return Display
    if driver == "ili9341":
        from ili9341 import Display
        return Display
    raise ValueError(
        f"DISPLAY_DRIVER inconnu : {driver!r} "
        "(valeurs possibles : 'ili9341', 'st7789', 'mock')"
    )


if DISPLAY_DRIVER == "mock":
    from mock_display import Display
else:
    try:
        Display = _load_hardware(DISPLAY_DRIVER)
    except ImportError as exc:
        # Bibliothèques matérielles absentes : ne pas planter, simuler l'écran.
        print(f"[screen] pilote '{DISPLAY_DRIVER}' indisponible ({exc}); "
              "repli sur le pilote mock (aucun écran SPI détecté).")
        from mock_display import Display

__all__ = ["Display"]

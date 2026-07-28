# HARDWARE

## Raspberry Pi

-   Raspberry Pi 4
-   Debian 13 (Trixie)

## Écran

-   ILI9341 **ou** ST7789 SPI
-   240 × 320 pixels

Le pilote est sélectionné par `DISPLAY_DRIVER` dans `config.py`
(`"ili9341"` ou `"st7789"`). Le brochage, le bus SPI et la vitesse sont
communs aux deux écrans. Les dalles ST7789 240 × 240 peuvent nécessiter un
décalage (`ST7789_X_OFFSET` / `ST7789_Y_OFFSET`).

## Brochage

  Signal        GPIO
  ----------- ------
  DC              24
  RESET           25
  CS               8
  Backlight       18

Brochage détaillé de l'écran (SPI0 complet) et sa cohabitation avec le capteur
de présence LD2410C (UART) sur le même Pi : voir [Câblage](CABLAGE.md). Les deux
périphériques ne partagent aucun GPIO.

## Capteur de présence (optionnel)

Le dashboard peut réveiller l'écran quand quelqu'un passe devant, en interrogeant
le service **morfSensor** (radar HLK-LD2410C en UART) sur son endpoint HTTP
`/presence`. Le capteur est câblé sur le même Pi que l'écran :

  Signal     GPIO (BCM)   Broche physique
  --------- ------------ -----------------
  VCC (5 V)  -            2 (ou 4)
  GND        -            9
  TX → RXD   GPIO15       10
  RX ← TXD   GPIO14       8

Détail et configuration UART : `morfSensor/docs/fr/CABLAGE.md`. Activation via
`PRESENCE_SENSOR_ENABLED` / `PRESENCE_SENSOR_URL` dans `config.py`.

## SPI

-   Bus : SPI0
-   Device : 0
-   Vitesse : 40 MHz

Le CS (GPIO 8 / CE0) est piloté **automatiquement par le contrôleur SPI**,
sans gestion logicielle via `RPi.GPIO`. Le revendiquer manuellement provoque
l'erreur « GPIO not allocated » sous `lgpio`.

Les paramètres matériels sont centralisés dans `config.py`.

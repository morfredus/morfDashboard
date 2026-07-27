# CÂBLAGE DES ÉCRANS

Guide de raccordement des écrans **ILI9341** et **ST7789** au Raspberry Pi.

> ⚠️ **Logique 3,3 V.** `VCC` se raccorde au **3,3 V** du Raspberry Pi.
> Ne jamais alimenter les broches de données en 5 V : cela peut détruire
> le contrôleur de l'écran.

Le brochage est **identique** pour les deux dalles (même bus SPI0, mêmes
GPIO). Passer de l'un à l'autre se fait uniquement par logiciel :
`DISPLAY_DRIVER = "ili9341"` ou `"st7789"` dans `config.py`. Aucun fil à
déplacer. Seule différence : le ST7789 n'a pas de sortie MISO (SDO).

---

## Correspondance des GPIO (source : `config.py`)

| Fonction        | GPIO (BCM) | Broche physique | Constante `config.py` |
| --------------- | ---------- | --------------- | --------------------- |
| Alimentation    | 3,3 V      | 1               | -                     |
| Masse           | GND        | 6               | -                     |
| Chip Select     | GPIO8 / CE0| 24              | `CS_PIN` (SPI matériel)|
| Reset           | GPIO25     | 22              | `RST_PIN`             |
| Data/Command    | GPIO24     | 18              | `DC_PIN`              |
| MOSI (données)  | GPIO10     | 19              | bus SPI0              |
| SCLK (horloge)  | GPIO11     | 23              | bus SPI0              |
| MISO (retour)   | GPIO9      | 21              | bus SPI0 (ILI9341)    |
| Rétroéclairage  | GPIO18     | 12              | `LED_PIN`             |

> Le **CS (CE0 / GPIO8)** est piloté **en matériel** par le contrôleur SPI.
> Il ne faut pas le gérer via `RPi.GPIO` (erreur « GPIO not allocated »
> sous `lgpio`).

---

## ST7789

Sérigraphie typique (bord du module) : `GND · VCC · SCL · SDA · RES · DC · CS · BL`

| Sérigraphie ST7789 | Signal          | GPIO (BCM) | Broche physique |
| ------------------ | --------------- | ---------- | --------------- |
| **GND**            | Masse           | -          | 6               |
| **VCC**            | Alimentation 3,3 V | -       | 1               |
| **SCL**            | Horloge (SCLK)  | GPIO11     | 23              |
| **SDA**            | Données (MOSI)  | GPIO10     | 19              |
| **RES**            | Reset           | GPIO25     | 22              |
| **DC**             | Data/Command    | GPIO24     | 18              |
| **CS**             | Chip Select (CE0)| GPIO8     | 24              |
| **BL**             | Rétroéclairage  | GPIO18     | 12              |

> `SCL`/`SDA` sont des signaux **SPI** malgré leur nom façon I²C.
> Le ST7789 est en **écriture seule** : pas de broche SDO/MISO.

```
        ST7789 (vue de face, connecteur en haut)
    ┌───────────────────────────────────────────┐
    │  GND  VCC  SCL  SDA  RES  DC   CS   BL      │
    │   │    │    │    │    │    │    │    │       │
    └───┼────┼────┼────┼────┼────┼────┼────┼──────┘
        │    │    │    │    │    │    │    │
       GND  3V3  G11  G10  G25  G24  G8   G18
       (6)  (1) (23) (19) (22) (18) (24) (12)   ← broches physiques Pi
```

---

## ILI9341

Sérigraphie typique (bord du module) :
`VCC · GND · CS · RESET · DC · SDI(MOSI) · SCK · LED · SDO(MISO)`

| Sérigraphie ILI9341 | Signal          | GPIO (BCM) | Broche physique |
| ------------------- | --------------- | ---------- | --------------- |
| **VCC**             | Alimentation 3,3 V | -       | 1               |
| **GND**             | Masse           | -          | 6               |
| **CS**              | Chip Select (CE0)| GPIO8     | 24              |
| **RESET**           | Reset           | GPIO25     | 22              |
| **DC**              | Data/Command    | GPIO24     | 18              |
| **SDI (MOSI)**      | Données (MOSI)  | GPIO10     | 19              |
| **SCK**             | Horloge (SCLK)  | GPIO11     | 23              |
| **LED**             | Rétroéclairage  | GPIO18     | 12              |
| **SDO (MISO)**      | Données retour (MISO) | GPIO9| 21              |

> `SDO (MISO)` n'est pas indispensable à l'affichage (le projet n'écrit
> que vers l'écran). On peut le laisser non connecté si l'entrée est libre.

```
              ILI9341 (vue de face, connecteur en haut)
    ┌────────────────────────────────────────────────────────┐
    │ VCC  GND  CS  RESET  DC  SDI  SCK  LED  SDO              │
    │  │    │   │    │     │   │    │    │    │                │
    └──┼────┼───┼────┼─────┼───┼────┼────┼────┼───────────────┘
       │    │   │    │     │   │    │    │    │
      3V3  GND  G8  G25   G24 G10  G11  G18  G9
      (1)  (6) (24) (22)  (18)(19) (23) (12) (21)   ← broches physiques Pi
```

---

## Rappel de l'en-tête GPIO (broches utilisées)

```
        Raspberry Pi - connecteur 40 broches (extrait)
    3V3  (1) ● ● (2)  5V
         (3) ● ● (4)  5V
         (5) ● ● (6)  GND      ◄ Masse écran
         (7) ● ● (8)
         (9) ● ● (10)
        (11) ● ● (12) GPIO18   ◄ BL / LED (rétroéclairage)
        (13) ● ● (14)
        (15) ● ● (16)
    3V3 (17) ● ● (18) GPIO24   ◄ DC
   MOSI (19) ● ● (20) GND
   MISO (21) ● ● (22) GPIO25   ◄ RES / RESET
   SCLK (23) ● ● (24) GPIO8    ◄ CS (CE0)
        (25) ● ● (26)
   ...
   (19) GPIO10 = MOSI  ◄ SDA / SDI
   (21) GPIO9  = MISO  ◄ SDO (ILI9341 uniquement)
   (23) GPIO11 = SCLK  ◄ SCL / SCK
```

---

## Après câblage

1. Activer le SPI : `sudo raspi-config` → *Interface Options* → *SPI* → *Enable*.
2. Choisir le pilote dans `config.py` : `DISPLAY_DRIVER = "ili9341"` ou `"st7789"`.
3. Tester l'écran seul :
   - ILI9341 : `python ili9341.py`
   - ST7789  : `python st7789.py`
   (cycle navy → vert foncé → noir sur l'écran).
4. Si l'image ST7789 est décalée (dalle 240×240), ajuster
   `ST7789_X_OFFSET` / `ST7789_Y_OFFSET` dans `config.py`.
5. Réglages d'orientation / couleurs ST7789, dans `config.py` :
   - **Tête-bêche / miroir** → `ST7789_MADCTL` (registre 0x36) :
     `0x00` portrait · `0xC0` 180° · `0x80` miroir vertical ·
     `0x40` miroir horizontal. Ajouter `0x08` si rouge/bleu intervertis.
   - **Couleurs en négatif** → basculer `ST7789_INVERT` (True = INVON,
     False = INVOFF).

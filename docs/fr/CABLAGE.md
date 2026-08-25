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
| Bouton alim. (option) | GPIO3 | 5              | `POWER_BUTTON_PIN`    |

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
  GPIO3  (5) ● ● (6)  GND      ◄ (5) bouton alim. (option) · (6) masse écran
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

## Cohabitation avec le capteur de présence (LD2410C / morfSensor)

Sur le même Raspberry Pi, l'écran (bus **SPI**) et le capteur de présence
**HLK-LD2410C** (liaison **UART**) partagent le connecteur 40 broches sans
conflit : ils n'utilisent aucun GPIO en commun. Le dashboard ne lit pas le
capteur directement, il interroge le service **morfSensor** en HTTP ; côté
matériel, les deux périphériques sont simplement câblés sur le même en-tête.

Détail complet du capteur : `morfSensor/docs/fr/CABLAGE.md`. Rappel du
raccordement, pour la vue d'ensemble :

| LD2410C | Signal        | GPIO (BCM)   | Broche physique | Remarque |
| ------- | ------------- | ------------ | --------------- | -------- |
| `VCC`   | Alimentation 5 V | -         | 2 (ou 4)        | module alimenté en 5 V, E/S en 3,3 V |
| `GND`   | Masse         | -            | 9               | une masse distincte de celle de l'écran (broche 6) |
| `TX`    | UART          | GPIO15 / RXD | 10              | **TX capteur → RX du Pi** (trames de présence) |
| `RX`    | UART          | GPIO14 / TXD | 8               | RX capteur ← TX du Pi (non requis en lecture seule) |
| `OUT`   | Présence T/R  | GPIO23 (entrée)| 16            | sortie tout-ou-rien (3,3 V) : GPIO libre, sans conflit avec l'écran |

> ⚠️ Les E/S du LD2410C sont en **3,3 V** : relier `TX`/`RX`/`OUT` directement aux
> GPIO du Pi. Alimenter en 5 V (broche 2/4), signaux en 3,3 V.

> ℹ️ `OUT` est la présence brute (haut/bas) du module. morfSensor lit l'UART
> (plus riche) et ne s'en sert pas encore ; elle est câblée sur **GPIO23 (broche
> 16), en entrée**, pour un repli rapide ou un usage futur. Brochage de référence
> du parc : `docs/fr/CONVENTIONS-CABLAGE-PI4.md`.

### Pas de recouvrement de broches

| Périphérique | GPIO (BCM) utilisés | Broches physiques |
| ------------ | ------------------- | ----------------- |
| Écran (SPI0 + contrôle) | 8, 9, 10, 11, 18, 24, 25 | 12, 18, 19, 21, 22, 23, 24 |
| Capteur (UART + OUT) | 14, 15, 23 | 8, 10, 16 |
| Alimentation / masse | - | 1 (3,3 V écran), 2 (5 V capteur), 6 (GND écran), 9 (GND capteur) |

Aucun GPIO ni aucune broche physique n'est partagé : les deux montages
coexistent tels quels.

### En-tête 40 broches (écran + capteur)

```
        Raspberry Pi - connecteur 40 broches (écran SPI + capteur UART)
    3V3  (1) ● ● (2)  5V       ◄ (1) VCC écran 3,3 V   · (2) VCC capteur 5 V
  GPIO2  (3) ● ● (4)  5V
  GPIO3  (5) ● ● (6)  GND      ◄ (6) Masse écran
  GPIO4  (7) ● ● (8)  GPIO14   ◄ (8) TXD Pi → RX capteur (option, lecture seule)
    GND  (9) ● ● (10) GPIO15   ◄ (9) Masse capteur · (10) RXD Pi ← TX capteur
 GPIO17 (11) ● ● (12) GPIO18   ◄ (12) BL / rétroéclairage écran
 GPIO27 (13) ● ● (14) GND
 GPIO22 (15) ● ● (16) GPIO23   ◄ (16) OUT capteur (présence T/R, entrée)
    3V3 (17) ● ● (18) GPIO24   ◄ (18) DC écran
 GPIO10 (19) ● ● (20) GND      ◄ (19) MOSI écran (SDA/SDI)
  GPIO9 (21) ● ● (22) GPIO25   ◄ (21) MISO écran (SDO, ILI9341) · (22) RESET écran
 GPIO11 (23) ● ● (24) GPIO8    ◄ (23) SCLK écran (SCL/SCK) · (24) CS écran (CE0)
```

> Le capteur a besoin d'une masse propre : utiliser une **broche GND distincte**
> de celle de l'écran (par exemple la 9), la broche 6 étant déjà prise.

---

## Bouton d'alimentation (facultatif)

Un simple bouton-poussoir permet d'éteindre ou de redémarrer proprement le
Raspberry sans clavier ni SSH. Il est **facultatif** : tant qu'il n'est pas
monté, la fonction ne fait rien (voir plus bas).

| Fonction        | GPIO (BCM) | Broche physique | Constante `config.py` |
| --------------- | ---------- | --------------- | --------------------- |
| Bouton alim.    | GPIO3      | 5               | `POWER_BUTTON_PIN`    |
| Masse du bouton | GND        | 9 (par ex.)     | -                     |

Câblage : un contact du poussoir sur la **broche 5 (GPIO3)**, l'autre sur une
**masse** (broche 9 par exemple). Rien d'autre — pas de résistance externe : le
pull-up interne (renforcé, sur GPIO3, par le pull-up matériel de la ligne) tient
l'entrée au niveau haut au repos.

```
   Raspberry Pi
      broche 5 (GPIO3) ───────┐
                              [ ] poussoir
      broche 9 (GND) ─────────┘
```

Comportement (voir `power_button.py`) :

- **appui court** (< 3 s) → **extinction** propre (`systemctl poweroff`) ;
- **appui long** (≥ 3 s) → **redémarrage** propre (`systemctl reboot`).

L'action est décidée au **relâchement**, d'après la durée : un maintien
n'enchaîne jamais les deux. Le seuil est réglable
(`POWER_BUTTON_LONG_PRESS_SECONDS`), tout comme le pin (`POWER_BUTTON_PIN`) et
l'activation globale (`POWER_BUTTON_ENABLED`).

> **Pourquoi GPIO3 ?** C'est une entrée libre du poste (voir
> `CONVENTIONS-CABLAGE-PI4.md`) et c'est le pin de **réveil** du Raspberry Pi :
> une fois le Pi éteint, un appui sur ce **même bouton** le rallume. Aucun
> `dtoverlay` n'est nécessaire pour ce réveil.

### Absence de bouton : aucun risque de boucle

En logique active-basse avec pull-up, une ligne **sans bouton** reste au niveau
haut, donc lue « non pressée » : rien ne se déclenche. C'est le cas au départ,
avant montage du bouton — il n'y a **aucun** risque d'extinction ou de
redémarrage en boucle. Garde-fou supplémentaire : `power_button.py` refuse d'agir
sur une ligne déjà « pressée » au démarrage (câblage flottant, bloqué ou mal
branché) tant qu'un relâchement n'a pas été observé.

### Droits nécessaires (sudoers)

Le service tourne en utilisateur non-root. Il faut autoriser **uniquement** les
deux commandes d'arrêt/redémarrage sans mot de passe.

`scripts/linux/install-service.sh` le fait **automatiquement** : il pose
`/etc/sudoers.d/morfdashboard-power` pour l'utilisateur du service, après l'avoir
validé par `visudo -c` (jamais de sudoers invalide). La désinstallation
(`--uninstall`) le retire.

Pose manuelle si besoin (remplacer `morfredus` par l'utilisateur du service) :

```
# /etc/sudoers.d/morfdashboard-power  (valider avec « sudo visudo -cf »)
morfredus ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff, /usr/bin/systemctl reboot
```

Sans ce fichier, `sudo -n` échoue proprement (pas d'attente de mot de passe) et
le journal du service indique la commande refusée : le dashboard continue de
tourner normalement, seul le bouton reste sans effet.

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

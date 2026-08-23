# Convention de câblage GPIO --- pi4fred

## Objectif

Ce document fixe le câblage retenu pour remplacer la nappe GPIO
40 broches et le T-Cobbler actuellement utilisés sur pi4fred.

L'objectif n'est pas encore de figer un montage définitif. La breadboard
reste en place temporairement, mais ce prototype doit déjà préparer un
futur montage plus compact, propre et démontable.

Les trois éléments concernés sont :

-   l'écran ST7789 alimenté en 3,3 V ;
-   le ventilateur du boîtier alimenté en 3,3 V ;
-   le capteur de présence HLK-LD2410C alimenté en 5 V.

Le ventilateur reste **à l'intérieur du boîtier du Raspberry Pi**. Il
n'a donc plus besoin de sortir vers la breadboard.

------------------------------------------------------------------------

## 1. Principe général

Le montage doit respecter cette organisation :

``` text
                         RASPBERRY PI 4
                    ┌─────────────────────┐
                    │                     │
                    │  Ventilateur        │
                    │  3,3 V + GND        │
                    │  entièrement        │
                    │  dans le boîtier    │
                    │                     │
                    └─────────┬───────────┘
                              │
                              │ petit faisceau utile
                              │ uniquement
                              ▼
                        ┌────────────┐
                        │ BREADBOARD │
                        └─────┬──────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
                  ▼                       ▼
             Écran ST7789             LD2410C
             3,3 V + SPI              5 V + UART (+ OUT)
```

La nappe 40 broches et le T-Cobbler disparaissent.

------------------------------------------------------------------------

## 2. Convention du connecteur d'alimentation JST-XH 3 broches

La convention suivante s'applique à tous les montages du poste :

    Broche Fonction
  -------- -----------------
     **1** **3,3 V**
     **2** **GND / masse**
     **3** **5 V**

Soit :

``` text
            JST-XH 3 — ALIMENTATION

              1       2       3
            ┌─────┬─────┬─────┐
            │ 3V3 │ GND │  5V │
            └─────┴─────┴─────┘
```

### Pourquoi la masse au milieu ?

Le GND est volontairement placé entre le 3,3 V et le 5 V. Ce choix rend
le brochage plus facile à mémoriser et sépare physiquement les deux
tensions, ce qui limite le risque de contact accidentel entre elles.

**Cette disposition est une convention de câblage propre au poste ; elle
n'est pas une polarité imposée par le connecteur JST-XH lui-même.**

### Repérage de la broche 1

Pour éviter toute ambiguïté, ne pas se fier uniquement à « gauche » ou
« droite » : la vue s'inverse lorsqu'on retourne le connecteur.

Sur chaque connecteur ou adaptateur, repérer d'abord physiquement la
**broche 1** (marquage du boîtier, du PCB ou repère ajouté à la main),
puis appliquer :

``` text
Pin 1 = 3V3
Pin 2 = GND
Pin 3 = 5V
```

Pour le montage définitif, marquer explicitement le connecteur :

``` text
3V3 | GND | 5V
```

Avant la première mise sous tension, contrôler également les trois
broches au multimètre.

------------------------------------------------------------------------

## 3. Ventilateur --- câblage interne au boîtier

Le ventilateur est alimenté en 3,3 V et reste dans le boîtier.

Deux broches conviennent :

  Ventilateur   Raspberry Pi     Broche physique
  ------------- -------------- -----------------
  `+`           3,3 V                     **17**
  `-`           GND                       **14**

``` text
DANS LE BOÎTIER

Raspberry Pi
   pin 17 — 3V3 ─────► + ventilateur
   pin 14 — GND ─────► - ventilateur
```

Ces deux fils n'ont plus aucune raison de sortir du boîtier.

Un JST-XH 2 broches pourra être ajouté plus tard pour rendre le
ventilateur facilement remplaçable.

------------------------------------------------------------------------

## 4. Alimentation de la breadboard

Une seule arrivée de chaque tension est nécessaire depuis le Raspberry
Pi.

  Fonction   Raspberry Pi     Broche physique
  ---------- -------------- -----------------
  3,3 V      3V3                        **1**
  GND        masse                      **6**
  5 V        5V                         **2**

Ces trois lignes arrivent sur le JST-XH 3 broches selon la convention :

``` text
Pi pin 1  (3V3) ─────► JST pin 1
Pi pin 6  (GND) ─────► JST pin 2
Pi pin 2  (5V)  ─────► JST pin 3
```

La breadboard redistribue ensuite les alimentations aux périphériques.

``` text
                     BREADBOARD

3V3 ───────────────────────► écran ST7789 VCC
GND ────────────────┬──────► écran ST7789 GND
                    └──────► LD2410C GND
5V  ───────────────────────► LD2410C VCC
```

------------------------------------------------------------------------

## 5. Écran ST7789

L'écran fonctionne en **logique 3,3 V**. Son VCC est alimenté en 3,3 V
et ses signaux GPIO restent en 3,3 V.

### Brochage

  ST7789   Fonction               GPIO BCM       Broche physique Pi
  -------- -------------------- ---------- ------------------------
  GND      masse                       ---   **6 via distribution**
  VCC      alimentation 3,3 V          ---   **1 via distribution**
  SCL      SPI SCLK                 GPIO11                   **23**
  SDA      SPI MOSI                 GPIO10                   **19**
  RES      Reset                    GPIO25                   **22**
  DC       Data/Command             GPIO24                   **18**
  CS       Chip Select / CE0         GPIO8                   **24**
  BL       rétroéclairage           GPIO18                   **12**

Le ST7789 est utilisé en écriture seule : aucun MISO n'est nécessaire.

### Connecteurs envisagés

Les JST-XH disponibles vont jusqu'à 6 broches, ce qui permet de séparer
proprement l'écran en deux connecteurs.

#### JST-XH 6 --- signaux écran

``` text
1 — SCLK
2 — MOSI
3 — RESET
4 — DC
5 — CS
6 — BL
```

#### JST-XH 2 --- alimentation écran

``` text
1 — 3V3
2 — GND
```

Repérer cette convention sur les deux côtés du faisceau avant toute
soudure définitive.

------------------------------------------------------------------------

## 6. Capteur HLK-LD2410C

Le LD2410C est alimenté en **5 V**, mais ses signaux logiques (UART et
sortie de présence) sont en **3,3 V** et se raccordent directement aux
GPIO du Raspberry Pi.

Le module expose **cinq broches**. Les quatre premières servent à
l'alimentation et à la liaison UART ; la cinquième, **OUT**, est une
sortie de présence numérique qui n'est pas utilisée dans le pilotage
actuel par UART. Elle est néanmoins câblée dès maintenant pour préparer
le montage définitif (voir plus bas).

### Brochage

  LD2410C   Fonction                     Raspberry Pi            Broche physique
  --------- ---------------------------- -------------- ------------------------
  VCC       alimentation 5 V             5 V              **2 via distribution**
  GND       masse                        GND                **via distribution**
  TX        données capteur → Pi         GPIO15 / RXD                     **10**
  RX        données Pi → capteur         GPIO14 / TXD                      **8**
  OUT       présence détectée (niveau)   GPIO23                           **16**

Pour le fonctionnement actuel en lecture seule via UART, **TX du capteur
vers GPIO15 suffit**. Les broches RX et OUT restent facultatives.

### Broche OUT --- pourquoi la câbler malgré tout

La broche OUT passe à l'état haut lorsqu'une présence est détectée. Le
pilotage par UART fournit déjà une information de présence plus riche
(distance, énergie), donc OUT n'a aucun rôle dans le fonctionnement
actuel.

Elle est tout de même raccordée à **GPIO23 (broche physique 16)**, une
entrée libre proche des lignes UART, pour trois raisons :

-   figer dès le prototype un brochage complet et définitif ;
-   permettre plus tard un réveil ou une détection quasi instantanée
    sans passer par la trame UART ;
-   éviter de retoucher le faisceau soudé si OUT devient utile.

GPIO23 est configuré en **entrée**. Cette broche ne doit jamais être
pilotée en sortie tant qu'elle est reliée à OUT, sous peine de conflit
électrique. Le niveau logique de OUT (3,3 V annoncé) est à vérifier au
multimètre avant le premier raccordement au Pi.

### JST-XH 5 --- LD2410C

``` text
1 — 5V
2 — GND
3 — TX capteur → RX Pi
4 — RX capteur ← TX Pi
5 — OUT présence → GPIO23
```

------------------------------------------------------------------------

## 7. Faisceau entre le Raspberry Pi et la breadboard

Le ventilateur restant dans le boîtier, le faisceau extérieur ne
transporte plus que ce qui est réellement nécessaire.

### Alimentation

``` text
pin 1  — 3V3
pin 2  — 5V
pin 6  — GND
```

### Signaux écran

``` text
pin 12 — GPIO18 — BL
pin 18 — GPIO24 — DC
pin 19 — GPIO10 — MOSI
pin 22 — GPIO25 — RESET
pin 23 — GPIO11 — SCLK
pin 24 — GPIO8  — CS
```

### Signaux capteur

``` text
pin 10 — GPIO15 — RX Pi ← TX LD2410C
pin 8  — GPIO14 — TX Pi → RX LD2410C   (optionnel actuellement)
pin 16 — GPIO23 — OUT présence LD2410C (câblée, non utilisée)
```

### Décompte des fils extérieurs

  Configuration                                Fils
  -------------------------------------------- ------
  Lecture seule (TX seul)                      **10**
  Lecture seule + OUT câblée                   **11**
  UART complet (TX + RX) + OUT câblée          **12**

Le brochage définitif retenu correspond à la dernière ligne : les douze
fils sont câblés une fois pour toutes, même si RX et OUT ne sont pas
exploités aujourd'hui.

------------------------------------------------------------------------

## 8. Vue synthétique du GPIO

``` text
Raspberry Pi 4 — broches utilisées

3V3       (1) ● ● (2)  5V
GPIO2     (3) ● ● (4)  5V
GPIO3     (5) ● ● (6)  GND
GPIO4     (7) ● ● (8)  GPIO14 / TXD ──► RX LD2410C (option)
GND       (9) ● ● (10) GPIO15 / RXD ◄── TX LD2410C
GPIO17   (11) ● ● (12) GPIO18 ─────────► BL écran
GPIO27   (13) ● ● (14) GND ────────────► ventilateur -
GPIO22   (15) ● ● (16) GPIO23 ◄──────── OUT LD2410C
3V3      (17) ● ● (18) GPIO24 ─────────► DC écran
GPIO10   (19) ● ● (20) GND
GPIO9    (21) ● ● (22) GPIO25 ─────────► RESET écran
GPIO11   (23) ● ● (24) GPIO8 ──────────► CS écran
              ...
```

Et :

``` text
pin 17 — 3V3 ───────────────────────────► ventilateur +
pin 19 — GPIO10 / MOSI ─────────────────► SDA écran
pin 23 — GPIO11 / SCLK ─────────────────► SCL écran
```

Broches physiques occupées : 1, 2, 6, 8, 10, 12, 14, 16, 17, 18, 19,
22, 23, 24.

------------------------------------------------------------------------

## 9. Règles à respecter avant mise sous tension

1.  **Ne jamais envoyer 5 V sur le VCC ou les GPIO du ST7789.**
2.  Le LD2410C reçoit **5 V sur VCC**, mais tous ses signaux logiques
    (UART et OUT) restent en **3,3 V**.
3.  Configurer **GPIO23 en entrée** : la broche est reliée à la sortie
    OUT du capteur et ne doit jamais être pilotée en sortie.
4.  Vérifier le niveau réel de OUT au multimètre avant de le relier au
    Pi.
5.  Vérifier le repérage réel de la **pin 1 de chaque JST** avant de
    sertir ou souder.
6.  Ne jamais se fier uniquement à la gauche/droite d'un dessin : la vue
    côté fils inverse visuellement le connecteur.
7.  Marquer les connecteurs d'alimentation `3V3 / GND / 5V`.
8.  Contrôler continuité et absence de court-circuit au multimètre avant
    branchement au Pi.
9.  Lors de la première alimentation, mesurer le JST d'alimentation
    avant d'y raccorder l'écran et le capteur.
10. Ne passer au montage soudé ou au PCB qu'après validation réelle du
    montage sur breadboard.

------------------------------------------------------------------------

## 10. Philosophie du futur montage

La breadboard reste temporaire, mais le câblage doit déjà préparer la
suite :

-   pas de nappe GPIO 40 broches ;
-   pas de T-Cobbler ;
-   ventilateur entièrement interne ;
-   uniquement les fils utiles sortent du boîtier ;
-   connecteurs détrompés et démontables ;
-   un périphérique doit pouvoir être retiré sans démonter les autres ;
-   brochage complet dès le prototype, y compris les broches en réserve
    (RX et OUT du capteur) ;
-   conventions de brochage documentées ;
-   alimentation clairement distinguée des signaux ;
-   passage au montage définitif seulement après validation physique du
    prototype.

Le but n'est pas encore de figer le montage, mais de faire de la
breadboard **le prototype du câblage définitif**, plutôt qu'un câblage
provisoire qu'il faudra entièrement repenser ensuite.

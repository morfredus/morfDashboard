# ARCHITECTURE

    morfDashboard/
    ├── assets/
    │   ├── fonts/            (DejaVu Sans Mono)
    │   └── logo.png
    ├── VERSION
    ├── activity.py
    ├── presence_sensor.py
    ├── boot.py
    ├── config.py
    ├── dashboard.py
    ├── dashboard.service
    ├── display.py
    ├── reboot_ack.py
    ├── reboot_alert.py
    ├── screen.py
    ├── screensaver.py
    ├── ili9341.py
    ├── st7789.py
    ├── systeminfo.py
    ├── beacon_listener.py
    ├── beacon_status.py
    ├── README.md
    ├── INSTALL.md
    ├── CHANGELOG.md
    ├── ROADMAP.md
    ├── ARCHITECTURE.md
    ├── HARDWARE.md
    └── CABLAGE.md

## Modules

-   `dashboard.py` : point d'entrée ; aiguille entre le dashboard et l'écran de
    veille selon l'inactivité, et pilote le niveau de rétroéclairage.
-   `boot.py` : animation de démarrage.
-   `display.py` : composition de l'interface.
-   `screensaver.py` : rendu de l'écran de veille (cadre mobile : heure, uptime,
    pastilles d'état G/P/S) - anti-marquage et économie d'énergie.
-   `activity.py` : détection d'activité (mtime des `/dev/pts/*` = activité SSH)
    pour déclencher la veille.
-   `presence_sensor.py` : source de réveil **supplémentaire** - interroge le
    service autonome **morfSensor** (`GET /presence`) et renvoie `present`. Le
    dashboard ne pilote aucun capteur ; une présence détectée (radar LD2410C)
    réveille l'écran comme une activité SSH. Tolérant à l'absence du service
    (retourne `False`, comportement historique préservé).
-   `reboot_alert.py` : détection du rapport `Boot_*` du démarrage courant
    et gestion de l'acquittement.
-   `reboot_ack.py` : commande CLI pour acquitter le badge `REBOOT!` sans
    supprimer les logs.
-   `systeminfo.py` : collecte des informations système.
-   `beacon_listener.py` : écoute des heartbeats morfBeacon (présence des
    applications de bureau ComponentHub / SiteWatch / futurs outils).
-   `beacon_status.py` : outil CLI (SSH) - découvre les applis vivantes,
    interroge leur `/status` et produit un rapport Markdown des métriques.
-   `screen.py` : sélection du pilote d'écran selon `config.py`.
-   `ili9341.py` : pilote matériel ILI9341.
-   `st7789.py` : pilote matériel ST7789.
-   `config.py` : paramètres et seuils.

# INSTALL.md

# morfDashboard - Installation

Ce document décrit la mise en place de morfDashboard en tant que
service systemd afin qu'il démarre automatiquement au démarrage du
Raspberry Pi.

## Prérequis

-   Debian 13 (Trixie)
-   Python 3, avec les modules `Pillow`, `numpy`, `psutil`, `RPi.GPIO`, `spidev`
    (installés au niveau système ; `requirements.txt` est vide)
-   SPI activé

## Vérifier le fonctionnement (sans installer)

Depuis le dépôt :

``` bash
python3 dashboard.py
```

## Installer le service (recommandé)

L'installation **copie l'application dans un dossier fixe**
(`/opt/morfdashboard`), indépendant de l'emplacement du dépôt git. Déplacer
ou renommer le dépôt (ou une synchronisation Syncthing) ne casse donc plus le
service.

``` bash
sudo ./scripts/linux/install-service.sh
```

Le script : arrête le service `morfdashboard` s'il tourne déjà, copie
l'application dans `/opt/morfdashboard`, installe le service (exécuté par
l'utilisateur courant, pointant vers le dossier fixe), l'active au démarrage et
le lance. Il signale aussi tout autre lancement automatique résiduel (crontab,
`rc.local`, autostart) à retirer à la main.

La configuration locale est séparée du code installé :
`/etc/morfdashboard/config.local.py`. Le script la crée depuis
`config.local.example.py` si elle n'existe pas encore, puis la conserve lors des
installations et mises à jour suivantes. Modifier ce fichier pour choisir les
canaux de notification, ajouter des services propres à la machine ou désactiver
une option locale. Les dictionnaires (dont `SERVICE_LABELS`) sont fusionnés avec
les valeurs standard : les services ajoutés par une mise à jour restent affichés.

> Le nom d'unité est **`morfdashboard`** - c'est celui que morfDashboard
> surveille (`config.py` → `systemctl is-active morfdashboard`).

### Mettre à jour

``` bash
sudo ./scripts/linux/update-service.sh
```

Le script arrête d'abord `morfdashboard`, lance `git pull`, recopie
l'application dans `/opt/morfdashboard`, préserve
`/etc/morfdashboard/config.local.py`, rafraîchit l'unité systemd puis redémarre
le service s'il tournait avant la mise à jour.

## Vérification

``` bash
systemctl status morfdashboard --no-pager
```

Le service doit être **active (running)**.

## Journaux

``` bash
journalctl -u morfdashboard -n 50 --no-pager
```

ou

``` bash
journalctl -u morfdashboard -f
```

## Gestion du service

Arrêter :

``` bash
sudo systemctl stop morfdashboard
```

Redémarrer :

``` bash
sudo systemctl restart morfdashboard
```

Désactiver le démarrage automatique :

``` bash
sudo systemctl disable morfdashboard
```

## Détection de présence par capteur (optionnel - morfSensor)

En plus du réveil par activité SSH, le dashboard peut rallumer l'écran quand un
**capteur de présence** (radar LD2410C, etc.) détecte quelqu'un. Le dashboard
n'accède **pas** au capteur : il interroge le service autonome **morfSensor**
(projet séparé) via HTTP.

1. Installer et lancer morfSensor sur le Raspberry (voir son dépôt :
   `scripts/linux/install-service.sh`, service systemd `morfsensor`, API sur le
   port 8788).
2. Dans `config.py` du dashboard, régler le bloc **Détection de présence** :
   ```python
   PRESENCE_SENSOR_ENABLED = True
   PRESENCE_SENSOR_URL = "http://127.0.0.1:8788/presence"
   PRESENCE_SENSOR_TIMEOUT = 0.5
   ```
3. Tester le lien sans le service graphique :
   ```bash
   python3 presence_sensor.py     # "Présence détectée…" ou "Aucune présence…"
```

Si morfSensor est absent ou injoignable, la détection est simplement ignorée :
le réveil par activité SSH continue de fonctionner. Mettre
`PRESENCE_SENSOR_ENABLED = False` pour désactiver complètement l'interrogation.
Pour une installation en service, préférer cette surcharge dans
`/etc/morfdashboard/config.local.py` afin qu'une mise à jour ne l'écrase pas.

## Commande d'acquittement du badge reboot

Le script `reboot_ack.py` permet d'acquitter le badge `REBOOT!` sans supprimer
les dossiers de logs. Il peut être lancé directement depuis le dossier du
dashboard :

``` bash
cd ~/Codage/Python/morfDashboard
python3 reboot_ack.py
```

Pour pouvoir l'utiliser depuis n'importe quel dossier avec la commande
`reboot-ack`, créer un petit lanceur dans `~/bin` :

``` bash
mkdir -p ~/bin
nano ~/bin/reboot-ack
```

Contenu du fichier `~/bin/reboot-ack` :

``` sh
#!/bin/sh
cd /home/morfredus/Codage/Python/morfDashboard || exit 1
exec python3 reboot_ack.py "$@"
```

Adapter le chemin `/home/morfredus/Codage/Python/morfDashboard` si le
projet est installé ailleurs.

Rendre le lanceur exécutable :

``` bash
chmod +x ~/bin/reboot-ack
```

Vérifier que `~/bin` est bien dans le `PATH` :

``` bash
command -v reboot-ack
```

Utilisation :

``` bash
reboot-ack
```

## Mise à jour

Utiliser le script (arrête le service, récupère le code, recopie dans
`/opt/morfdashboard`, conserve la config locale, redémarre le service) :

``` bash
sudo ./scripts/linux/update-service.sh
```

> Un simple `git pull` ne suffit pas : l'application s'exécute depuis
> `/opt/morfdashboard`, pas depuis le dépôt. La recopie est indispensable -
> c'est ce que fait `update-service.sh`.

## Vérification finale

``` bash
sudo reboot
```

Après le redémarrage, le dashboard doit se lancer automatiquement.

# Changelog

All notable changes to the project are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and the project follows [Semantic Versioning](https://semver.org/) (the `VERSION`
file at the repository root).

## [1.15.2] - 2026-08-23

### Corrigé

- `service.py` accepte désormais l'action `config` (`push` / `merge`) comme le
  reste du parc. Un déploiement `morf install --all` en mode `replace` échouait ici
  seul (`invalid choice: 'config'`) car morfTools appelle `config push --force`
  sur chaque `service.py`. `config push` délègue à `install-service.sh
  --refresh-config` (sauvegarde puis remplace `config.local.py` depuis le dépôt) ;
  `config merge` est sans objet pour une config Python et conserve la config
  locale en le signalant.

## [1.15.1] - 2026-08-17

### Ajouté

- **`service.py uninstall --dry-run`** : suit la croissance du contrat commun.
  morfDashboard expose l'interface du parc manuellement (mécanique propre dans
  `scripts/linux/`) ; il accepte désormais `--dry-run` sur `uninstall` et décrit
  ce qui serait retiré sans rien toucher, sur toute plateforme (un balayage
  `morf uninstall --all --dry-run` passe aussi par ici sous Windows, où il n'y a
  rien à retirer). Sans cela, un tel balayage échouait sur morfDashboard.

## [1.15.0] - 2026-08-17

### Ajouté

- **Pilote d'écran `mock` (écran simulé).** Nouveau `mock_display.py` : au lieu de
  piloter une dalle SPI, il écrit chaque image dans un PNG (`MOCK_PNG_PATH`, défaut
  `/var/lib/morfsystem/morfdashboard/screen.png`, repli sur un fichier temporaire si
  non inscriptible) et, en option, l'affiche dans une fenêtre Tkinter
  (`MORFDASHBOARD_MOCK_WINDOW=1`). Le rétroéclairage est simulé en assombrissant le
  PNG (on visualise veille et extinction). Ne dépend que de Pillow.
- **Repli automatique sans écran SPI.** `screen.py` bascule sur le pilote `mock` quand
  le pilote matériel choisi ne peut pas s'importer (spidev / RPi.GPIO absents) : sur une
  machine Linux sans écran, le service **tourne** au lieu de planter et redémarrer en
  boucle. Le pilote peut aussi être choisi explicitement (`DISPLAY_DRIVER = "mock"`) ou
  forcé par la variable d'environnement `MORFDASHBOARD_DISPLAY_DRIVER`.

## [1.14.0] - 2026-08-16

### Modifié

- **Affichage exclusivement local.** Le Dashboard ne montre plus que les services
  de SA machine et les équipements du parc, jamais les services d'un autre poste.
  Un poste distant éteint (souvent pi4dev) ne vient donc plus rougir l'écran
  d'alertes qui ne le concernent pas. La distinction s'appuie sur le nouveau champ
  `role` du protocole morfBeacon : `host` (service sur une machine, gardé si c'est
  cette machine) ou `device` (équipement autonome type MeteoHub, toujours gardé).
  S'applique aux deux modes : via morfMonitor (filtrage de la section beacon) et en
  repli local (l'écouteur beacon distingue désormais l'instance locale d'une
  instance distante, par instance `(app, hôte)`).

## [1.13.3] - 2026-08-14

### Ajouté

- **Installation des dépendances Python via apt** dans
  `scripts/linux/install-service.sh` : Pillow, numpy, RPi.GPIO, spidev et psutil
  (`python3-pil`, `python3-numpy`, `python3-rpi.gpio`, `python3-spidev`,
  `python3-psutil`). Sur Raspberry Pi OS, le Python système est « externally
  managed » (PEP 668), donc pas de pip : ces paquets rendent l'installation du
  service autosuffisante. Étape tolérante : un échec apt (hors ligne, nom de
  paquet variable, dépendances déjà présentes) avertit sans interrompre
  l'installation.

## [1.13.2] - 2026-08-14

### Corrigé

- Suppression du `requirements.txt` **vide**. Il ne déclarait aucune dépendance
  (celles de morfDashboard - PIL, numpy, RPi.GPIO, spidev, psutil - sont des
  paquets système, installés via apt sur le Raspberry Pi), mais suffisait à
  déclencher un `pip install` lors de `morf install` (mode générique), qui
  échouait sous PEP 668 (`externally-managed-environment`). Le déploiement réel
  passe par `service.py` (`morf install --services`), inchangé.

## [1.13.1] - 2026-08-14

### Ajouté

- **Déclaration de la commande `screenctl` pour `activate-cli.sh`** (`cli.manifest`,
  mode `direct`) : `screenctl` peut désormais être exposée dans `~/.local/bin` par
  le mécanisme commun de morfTools et appelée depuis n'importe quel dossier.
  `screenctl.py` reste la propriété de morfDashboard (le mécanisme n'en transfère
  pas la responsabilité).

## [1.13.0] - 2026-08-13

### Ajouté

- **Luminosité de l'écran en PWM à trois paliers + commande manuelle.** Le
  rétroéclairage (broche BL sur `GPIO18`) passe d'un simple allumé/éteint à trois
  niveaux paramétrables dans `config.py` : `BL_ACTIVE` (100 %, présence),
  `BL_STANDBY` (15 %, veille) et `BL_OFF` (0 %, extinction volontaire). Le PWM
  reste logiciel (RPi.GPIO), suffisant pour des paliers fixes.
- **Forçage manuel persistant via `screenctl.py`** (`on` / `off` / `auto` /
  `status`). Un mode `off` garde l'écran volontairement éteint sans couper le
  service ; `auto` rend la main à la gestion présence/veille. L'outil est
  strictement local (aucun réseau, aucun port) : il écrit le mode dans un fichier
  d'état relu par le service à chaque tour de boucle, effet en quelques secondes
  sans redémarrage.

### Modifié

- **État du forçage sous `/var/lib/morfsystem/morfdashboard/backlight.state`**
  (doctrine FS morfSystem : état éditable via `StateDirectory` systemd, ajouté à
  l'unité). Surchargeable par `MORFDASHBOARD_BACKLIGHT_STATE` pour les tests hors
  Raspberry. Le contenu (`auto`/`on`/`off`) survit aux redémarrages.
- **Nouvelles constantes `BL_ACTIVE` / `BL_STANDBY` / `BL_OFF`** dans `config.py`.
  Les anciens noms `BACKLIGHT_FULL` et `SCREENSAVER_BACKLIGHT` restent définis
  (alias) pour compatibilité descendante des pilotes et des configs locales.

## [1.12.1] - 2026-07-28

### Documentation

- **Brochage GPIO consolidé écran + capteur** dans [`docs/fr/CABLAGE.md`] : vue
  d'ensemble du connecteur 40 broches montrant l'écran (SPI) et le capteur de
  présence LD2410C (UART) sur le même Pi, avec la preuve qu'ils ne partagent
  aucun GPIO ni aucune broche physique. `docs/fr/HARDWARE.md` gagne une section
  « Capteur de présence » avec son brochage. Renvois croisés avec
  `morfSensor/docs/fr/CABLAGE.md`.

## [1.12.0] - 2026-07-28

### Modifié

- **Config locale sous `/etc/morfsystem/morfdashboard/config.local.py`** (au lieu
  de `/etc/morfdashboard`), pour un point d'entrée unique dans `/etc`. La config
  partagée reste `/etc/morfsystem/morfsystem.json`.


### Corrigé

- **Casse du chemin Windows de la configuration partagée alignée sur le
  déploiement.** Le Dashboard cherchait `%ProgramData%/morfSystem/morfsystem.json`
  (S majuscule) alors que le fichier est installé dans `%ProgramData%/morfsystem/`
  (minuscule, comme les dossiers de service du parc). Sans effet sur NTFS, mais
  aligné pour rester cohérent avec morfMonitor et la convention. Linux
  (`/etc/morfsystem/morfsystem.json`) était déjà correct.

## [1.11.1] - 2026-07-27

### Modifié

- **Cadence de rotation configurable.** La durée d'affichage d'une page de la zone
  des services est désormais réglable via `SERVICES_ROTATE_SECONDS` dans
  `config.py` (défaut 6 s), au lieu d'être codée en dur.

## [1.11.0] - 2026-07-27

### Ajouté

- **Rotation automatique de la zone des services (bas de l'écran).** Cette zone
  ne dispose que de six emplacements ; au-delà de six services surveillés, les
  suivants n'apparaissaient pas. Elle **défile désormais automatiquement** (une
  page toutes les six secondes), avec de petits points de pagination en bas de
  l'écran. Les services **en alerte** (pastille rouge ou orange) sont **épinglés**
  en tête et restent **toujours visibles** ; seuls les services sains défilent
  dans les emplacements restants. Si toutes les places sont occupées par des
  alertes, ce sont les alertes qui défilent.

## [1.10.2] - 2026-07-24

### Corrigé

- **L'écran n'est pas un OLED.** Plusieurs commentaires et une entrée de journal
  décrivaient « l'écran OLED » du dashboard, alors qu'il pilote une dalle **LCD
  SPI (ILI9341 / ST7789)** - ce que le README dit par ailleurs explicitement en
  rappelant que le burn-in est « essentiellement un phénomène OLED », donc sans
  objet ici. Corrigé dans `service.py`, `beacon_emitter.py`,
  `scripts/linux/install-service.sh` et l'entrée de la 1.8.0. Les deux mentions
  d'OLED du README et du journal qui parlent du burn-in sont, elles, exactes et
  conservées.

## [1.10.1] - 2026-07-24

### Corrigé

- **Une mise à jour sans changement ne redémarre plus le service.** Le script
  arrêtait, recopiait puis relançait sans jamais se demander s'il y avait
  quelque chose à déployer. `rsync` sait pourtant dire, à blanc, ce qu'il
  changerait : quand il ne changerait rien et que la configuration est en place,
  la mise à jour s'arrête en le disant - et en précisant que le service n'a
  **pas** été redémarré. `--force` passe outre. Sans `rsync`, on déploie comme
  avant : mieux vaut un redémarrage inutile qu'une mise à jour silencieusement
  omise. Le `git pull` passe avant l'arrêt, puisqu'il n'a jamais eu besoin que
  le service soit stoppé - et qu'il faut le code final pour savoir s'il y a
  quelque chose à faire.

## [1.10.0] - 2026-07-24

### Ajouté

- **`service.py` - morfDashboard expose enfin l'interface commune du parc**
  (`install`, `update`, `uninstall`, `status`, `is-installed`). Il restait le
  seul service piloté par ses scripts shell, et ce cas particulier avait un
  coût invisible : `morf.py upgrade` récupérait son nouveau code puis laissait
  le service tourner sur l'ancien, **sans un mot**, faute d'un `service.py` à
  interroger. morfTools peut désormais s'en tenir à une règle sans exception :
  un projet qui est un service porte un `service.py`.

  Ce fichier ne réimplémente rien - il traduit une interface. Le déploiement
  reste entièrement dans `scripts/linux/`, qui connaît le rsync, ses exclusions,
  la configuration locale et l'unité systemd : la connaissance du projet reste
  dans le projet. `update` délègue avec `--no-pull`, parce que récupérer le code
  est le travail de morfTools et déployer celui du projet - le même partage que
  pour les services morfdeploy, dont l'`update` ne fait pas de `git pull` non
  plus.

  `is-installed` répond par son code de retour (0 installé, 1 absent) en
  interrogeant systemd, pas en testant la présence d'un fichier : c'est le
  gestionnaire de services qui fait autorité. Sur une machine qui n'est pas sous
  Linux, la réponse est « absent » et les autres actions expliquent pourquoi.

## [1.9.0] - 2026-07-22

### Modifié

- **Le projet est renommé RaspberryDashboard → morfDashboard**, pour une cohérence
  totale avec le reste du parc (morfMonitor, morfSync…) et avec ce que le service
  fait déjà : l'unité systemd `morfdashboard` et le nom annoncé sur le réseau
  `morfDashboard` étaient déjà alignés. Le dépôt GitHub, le dossier, la
  documentation et les références du parc suivent. Aucun changement de
  comportement : mêmes fichiers, même service, même port 8791.

## [1.8.1] - 2026-07-22

### Corrigé

- **L'installation retire l'ancien service `dashboard`.** Le renommage en
  `morfdashboard` datait de la 1.6.1, mais rien ne désinstallait l'unité
  d'origine : sur une machine mise à jour depuis, `dashboard.service` et
  `morfdashboard.service` pilotaient tous deux le même écran SPI. L'étape 5
  vérifiait le crontab et l'autostart, jamais l'ancienne unité systemd, la plus
  probable.

- **`MORF_APP_DIR` remplace `RD_APP_DIR`**, la variable unique du parc.
  L'ancienne reste reconnue pour ne casser aucune note ni aucun script.

## [1.7.3] - 2026-07-20

### Corrigé

- **Numéro de version corrigé de `0.7.2` en `1.7.2`.** La version avait reculé
  sous une lignée déjà taguée (`v1.4.0`), ce qui aurait produit un tag
  s'ordonnant avant les releases existantes. `VERSION` et l'en-tête de
  l'entrée du 17/07/2026 sont alignés.

- **Les services disparaissaient de la partie basse de l'écran.** Ils
  s'affichaient brièvement puis laissaient la place à une liste vide. Le mode
  dégradé ne se déclenchait que si morfMonitor était **injoignable** ; un
  morfMonitor qui répond mais n'a chargé **aucune configuration** - donc ne
  supervise rien - passait pour une réponse valide, et l'écran se vidait sans la
  moindre alerte. Répondre n'est pas savoir : une réponse ne déclarant aucun
  service systemd ni aucune sonde est désormais jugée dégénérée, et le Dashboard
  replie sur sa collecte locale. Un superviseur muet est pire qu'un superviseur
  arrêté, puisque l'arrêt, lui, avait un repli.

### Ajouté

- **Consommation des API de morfMonitor** (`monitor_client.py`). Le Dashboard
  privilégie désormais morfMonitor comme source des informations système, au
  lieu de les collecter lui-même. Une seule requête (`/api/all`) fournit un
  instantané cohérent.
- **Mode dégradé automatique.** Si morfMonitor est arrêté, en cours de
  démarrage ou injoignable, le Dashboard reprend sa collecte locale, et revient
  au mode normal dès que le service répond. **Aucun redémarrage n'est
  nécessaire** - ce qui compte, puisque c'est pendant un incident qu'on regarde
  l'écran. Après un échec, le client attend 10 s avant de retenter : marteler un
  service arrêté ne le rallume pas et figerait l'affichage à chaque tentative.
- **Champ `source`** dans `get_system_info()` : vaut `morfMonitor` ou `local`,
  avec `source_error` en mode dégradé. Permet d'afficher discrètement l'origine
  des données et de diagnostiquer d'un coup d'œil.
- **Notifications de redémarrage enrichies.** Tous les redémarrages
  produisaient le même message générique (« Reboot non demandé détecté »), donc
  inexploitable. La notification envoyée à morfNotify précise désormais la cause
  fournie par morfMonitor, et son **niveau en découle** : `error` pour une
  coupure d'alimentation, un plantage noyau ou un chien de garde ; `info` pour
  un redémarrage demandé ou une mise à jour, qui sont attendus ; `warning` quand
  la cause reste indéterminée. Tout envoyer au même niveau revenait à n'en
  signaler aucun utilement.

  La détection étant faillible, une cause de faible confiance est annoncée comme
  **hypothèse** plutôt qu'affirmée : affirmer « coupure d'alimentation » à tort
  ferait chercher un problème électrique inexistant. La réserve ne s'applique
  pas à « cause inconnue », dont le libellé dit déjà qu'on ne sait pas.

  Sans morfMonitor (mode dégradé), aucune cause n'est disponible : le message
  générique d'origine est conservé, plutôt qu'une explication inventée.
- **Configuration partagée** `/etc/morfsystem/morfsystem.json`, lue aussi par
  morfMonitor. `SERVICE_LABELS`, `NETWORK_SERVICES` et `BEACON_APPS` en sont
  désormais dérivés ; les listes codées dans `config.py` deviennent des valeurs
  de repli, conservées pour qu'une machine sans fichier partagé continue
  d'afficher quelque chose.

### Modifié

- L'ancienne collecte locale est conservée intégralement sous
  `_get_system_info_local()` : elle n'est plus le chemin nominal, mais reste le
  filet de sécurité. La couleur des pastilles reste au Dashboard - morfMonitor
  fournit des faits (actif / inactif / en attente), pas des choix graphiques.

### Limitations connues

- L'**indicateur visuel** de source n'est pas encore dessiné à l'écran : la
  donnée est disponible, son affichage reste à faire.
- Le mode local affiche **8 pastilles contre 9** en mode normal : une sonde
  réseau n'y apparaît que si sa clé figure aussi dans `SERVICE_LABELS`,
  contrainte héritée de l'implémentation d'origine.

## [1.7.2] - 2026-07-17

### Changed - robust service config and update flow

- `config.py` now loads optional local overrides from
  `MORFDASHBOARD_CONFIG`, `/etc/morfdashboard/config.local.py`, then
  `config.local.py` next to the app. Only uppercase settings are imported.
- `install-service.sh` creates/preserves `/etc/morfdashboard/config.local.py`,
  excludes local config from the application copy, installs the systemd unit,
  enables it at boot and starts it immediately.
- `update-service.sh` now stops `morfdashboard` before updating, preserves the
  local config, refreshes the systemd unit, then restarts the service only if it
  was running before the update.
- Added `config.local.example.py` as the template for local overrides.

## [1.7.0] - 2026-07-16

### Added - presence sensor as an extra wake source (morfSensor)

- The screen can now be woken by a **presence sensor** (LD2410C radar, etc.)
  **in addition to** SSH activity. The dashboard does **not** drive any sensor:
  it queries the autonomous **morfSensor** service over HTTP and reads the
  `present` boolean.
- New module **`presence_sensor.py`** - `presence_detected()` does a short,
  non-blocking `GET` on morfSensor's `/presence`; any error (service down,
  timeout) returns `False`, so the historical SSH-only behaviour is preserved.
- **`config.py`** - new `PRESENCE_SENSOR_ENABLED`, `PRESENCE_SENSOR_URL`
  (`http://127.0.0.1:8788/presence`), `PRESENCE_SENSOR_TIMEOUT`.
- **`dashboard.py`** - in the main loop, a detected presence refreshes
  `last_active` just like SSH activity.
- morfSensor also announces itself via morfBeacon, so `beacon_status.py`
  discovers it with no configuration.

## [1.6.1] - 2026-07-15

### Changed - systemd unit renamed to `morfdashboard`

- The systemd service is now named **`morfdashboard`** (was `dashboard`), for
  ecosystem consistency. Updated: the unit file (`scripts/linux/morfdashboard.service`),
  the install/update scripts, the monitored-service key in `config.py`
  (`SERVICE_LABELS`) and its exclusion in `systeminfo.py` (so the dashboard keeps
  showing its own status correctly), and `docs/fr/INSTALL.md`.
- The **old `dashboard` service must be removed manually** before/after
  installing the new one (see chat / project notes).

## [1.6.0] - 2026-07-15

### Added - robust systemd install

- **`scripts/linux/install-service.sh`** installs the app into a **fixed location**
  (`/opt/morfdashboard`), independent of where the git clone lives. Moving or
  renaming the repository (or a Syncthing sync) no longer breaks the service. The
  script stops any previous `dashboard` service, copies the app, installs the unit
  (running as the current user, pointing at the fixed dir), enables and starts it,
  and flags any leftover autostart (crontab, `rc.local`, desktop autostart).
- **`scripts/linux/update-service.sh`**: `git pull`, re-copy to the fixed dir,
  restart - no compilation (Python).
- The unit name stays **`dashboard`** (the one the dashboard monitors).

### Changed

- Removed the repository-root `dashboard.service` with its hardcoded path (the
  source of the fragility). The parametrized unit now lives in `scripts/linux/`.

## [1.5.0] - 2026-07-14

### Added - standby (screensaver) mode

An anti-burn-in / power-saving standby screen that takes over from the dashboard
after a period of inactivity, with **software presence** detection (no sensor
yet). Numbered summary of the changes:

1. **Standby triggered by SSH inactivity.** After `SCREENSAVER_IDLE_SECONDS`
   (60 s) with no SSH terminal activity, the display switches to a minimal
   standby frame; any SSH activity wakes it immediately. Disable globally with
   `SCREENSAVER_ENABLED = False`. A start-up grace keeps the dashboard visible
   right after boot (no immediate standby when no one is connected yet).
2. **Presence from SSH activity (`activity.py`).** New module reading the most
   recent mtime of the `/dev/pts/*` pseudo-terminals - the same signal as the
   `IDLE` column of `w`. It does not depend on the utmp `host` field (sometimes
   empty), which makes detection reliable.
3. **Backlight dimming (software PWM).** `st7789.py` / `ili9341.py` now expose
   `set_backlight(0-100)` driven by PWM on `LED_PIN` (GPIO 18): the standby
   screen drops to `SCREENSAVER_BACKLIGHT` (15 %) and returns to `BACKLIGHT_FULL`
   when active. New `config.py` keys `BACKLIGHT_PWM`, `BACKLIGHT_FREQ_HZ`,
   `BACKLIGHT_FULL`; set `BACKLIGHT_PWM = False` for an on/off backlight.
4. **Three status dots on the standby frame (`systeminfo.screensaver_status`).**
   A row of three dots summarizing, left to right: **G** global/thermal
   (green/orange/red against `TEMP_*`), **P** CPU load on **4 levels**
   (green < `CPU_ELEVATED` 50 % · yellow · orange ≥ `CPU_WARNING` · red ≥
   `CPU_CRITICAL`), **S** services (green if all up, orange if at least one is
   down - never red; the `dashboard` service is excluded from the test since it
   is necessarily running). New threshold `CPU_ELEVATED` in `config.py`.
5. **Standby-frame legibility.** A letter (**G / P / S**) is drawn above each dot
   in an intermediate font size and in the uptime colour; the clock is softened
   (grey instead of pure white) and the uptime is slightly enlarged. The frame
   is repositioned at every refresh to avoid fixing the same pixels.
6. **`overall_status()` helper** in `systeminfo.py`: a single aggregated health
   verdict (`ok` / `warning` / `critical`) over the metrics and services.

These screens are LCD panels (ST7789 / ILI9341): true permanent burn-in is an
OLED phenomenon, so here the main gain is the reduced backlight (power draw and
LED lifespan), the moving frame guarding only against transient retention.

## [1.4.0] - 2026-07-13

### Added
- **`beacon_status.py`** - an SSH-run CLI that discovers the live morfBeacon apps
  on the LAN, queries their `/status` endpoint and prints their detailed metrics,
  producing a human-friendly **Markdown report** (`beacon_status.md`). The
  headless screen only shows presence; this tool gives the detail on demand.

### Changed
- `beacon_listener.py` now sets `SO_REUSEPORT` (best-effort) so the dashboard
  service and `beacon_status.py` can listen on port `45454` at the same time.

## [1.3.0] - 2026-07-13

### Changed
- **Documentation overhaul and bilingual layout.** Following the convention of
  the other repositories, the root documents are now in **English**
  (`README.md`, `CHANGELOG.md`, `ROADMAP.md`, `CONTRIBUTING.md`); a French
  `README.fr.md` is kept for French speakers. The in-depth guides moved under
  `docs/fr/` (French, the reference language: architecture, hardware, wiring,
  install), with an English index at `docs/en/README.md`.
- **License clarified to GPL-3.0-only** (previously GPL-3.0-or-later): the full
  GNU GPL v3 text now ships in `LICENSE`.

### Added
- `CONTRIBUTING.md`.

## [1.2.1] - 2026-07-13

### Changed
- **Self-monitoring of the dashboard.** The local systemd service `dashboard` is
  now shown among the monitored items (green dot while it runs as a service), via
  `SERVICE_LABELS` → `systemctl is-active dashboard`.
- Removed `componenthub` from the ESP32 side (`SERVICE_LABELS` /
  `NETWORK_SERVICES`): ComponentHub no longer exists as an ESP32 - it is now
  monitored as a desktop app (morfBeacon heartbeat).

## [1.2.0] - 2026-07-13

### Added
- **LAN supervision of the desktop apps (morfBeacon).** The dashboard now listens
  for the UDP heartbeats broadcast by **ComponentHub**, **SiteWatch** (and future
  tools) on port `45454`, and shows whether each desktop app is online.
  *Push-presence* model: no probing, no IP to know, automatic discovery; an app
  with no heartbeat for `BEACON_OFFLINE_AFTER` seconds (60 s by default) is
  considered offline.
- New module `beacon_listener.py`: background UDP listener (standard library
  only). Watched apps configured in `BEACON_APPS` (`config.py`) - adding a future
  project is a single line.

### Changed
- **Status area laid out in two columns**: up to **6 monitored items** (systemd
  services + desktop apps), color dots kept. Names that are too long are
  abbreviated with a trailing ".".

## [1.1.0]

### Added
- **ST7789 (240 × 320 SPI) support** alongside the ILI9341. The driver is chosen
  via `DISPLAY_DRIVER` in `config.py` (`"ili9341"` or `"st7789"`).
- New driver `st7789.py` exposing the same `Display` API, and a new `screen.py`
  module that selects the driver from the configuration (`dashboard.py` and
  `boot.py` import `Display` from it, no direct dependency on a driver).
- Panel offsets `ST7789_X_OFFSET` / `ST7789_Y_OFFSET` in `config.py` for panels
  that need one.
- Embedded **DejaVu Sans Mono** font (in `assets/fonts/`) instead of the default
  PIL bitmap font: crisp, anti-aliased text on both screens, perfectly aligned
  columns. Font sizes centralized in `config.py` via `load_font()`.
- `reboot_alert.py` to detect reboot reports in the configured log folder while
  ignoring old history, and `reboot_ack.py` to acknowledge the `REBOOT!` badge
  without deleting the logs.

### Changed
- Robust header: hostname and time aligned dynamically; the centered version
  fades out when the hostname is too long (no more overlap).

## [1.0.1]

### Fixed
- **Startup crash on Raspberry Pi OS / `lgpio`** ("GPIO not allocated"): the
  chip-select (CE0 / GPIO 8) is now driven **in hardware** by the SPI driver,
  no longer toggled manually.

### Added
- Version (read from the `VERSION` file) shown in the header; `dev` when absent.
- Health dots (green / orange / red) in front of CPU, RAM, Swap, SSD and on the
  system load; temperature colored against its thresholds.
- SSD line: used space / total capacity (e.g. `8 / 98 Gio`) on top of the usage
  percentage. Load line: health dot + load as a percentage of cores, on top of
  the 1 / 5 / 15 min averages.

### Changed
- Alert thresholds centralized in `config.py` (CPU, RAM, Swap, Temp, SSD, Load),
  with a single `health_color(value, warning, critical)` helper.
- Monitored services driven by `SERVICE_LABELS` in `config.py`.

## [1.0.0]

### Added
- First modular architecture: `config.py`, `systeminfo.py`, `display.py`,
  `boot.py`, `ili9341.py`, `dashboard.py`.
- Boot animation; CPU, RAM, Swap, SSD, network and services display.
- `systemd` service with auto-start at boot.

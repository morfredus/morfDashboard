#!/usr/bin/env bash
#
# install-service.sh — Installe morfDashboard en service systemd robuste.
#
# Copie l'application dans un dossier FIXE (par défaut /opt/morfdashboard),
# hors du clone git, puis installe/active le service « morfdashboard » pointant là.
# Ainsi, déplacer le dépôt (ou une synchro Syncthing) ne casse plus rien.
#
# Usage :
#   sudo ./scripts/linux/install-service.sh
#   sudo MORF_APP_DIR=/opt/rdash ./scripts/linux/install-service.sh   # autre dossier
#   sudo ./scripts/linux/install-service.sh --refresh-config         # sauvegarde + remplace la config locale
#   sudo ./scripts/linux/install-service.sh --uninstall

set -euo pipefail

SERVICE_NAME="morfdashboard"
UNIT_DEST="/etc/systemd/system/$SERVICE_NAME.service"
# MORF_APP_DIR : variable unique du parc. RD_APP_DIR reste reconnu
# pour ne pas casser une note ou un script anterieur.
APP_DIR="${MORF_APP_DIR:-${RD_APP_DIR:-/opt/morfdashboard}}"
CONFIG_DIR="${RD_CONFIG_DIR:-/etc/morfsystem/morfdashboard}"
CONFIG_FILE="$CONFIG_DIR/config.local.py"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUN_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"
REFRESH_CONFIG=0

for arg in "$@"; do
    case "$arg" in
        --refresh-config) REFRESH_CONFIG=1 ;;
    esac
done

if [[ "${EUID}" -ne 0 ]]; then
    echo "Ce script doit être lancé avec sudo :  sudo $0 $*" >&2
    exit 1
fi

# --- Désinstallation ------------------------------------------------------
if [[ "${1:-}" == "--uninstall" ]]; then
    echo "Désinstallation de $SERVICE_NAME…"
    systemctl disable --now "$SERVICE_NAME" 2>/dev/null || true
    rm -f "$UNIT_DEST"
    systemctl daemon-reload
    echo "Service supprimé. (Application $APP_DIR conservée — la retirer : sudo rm -rf $APP_DIR)"
    exit 0
fi

echo "Utilisateur  : $RUN_USER"
echo "Source       : $REPO_ROOT"
echo "Installation : $APP_DIR"
echo "Config locale: $CONFIG_FILE"

# --- 1. Arrêter l'ancien lancement ---------------------------------------
systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# Avant la 1.6.1, ce service s'appelait « dashboard ». Une unité de ce nom est
# encore installée et ACTIVE sur toute machine mise à jour depuis cette époque.
# L'étape 5 traquait le crontab et l'autostart, mais pas l'ancienne UNITÉ elle-
# même — la plus probable : sans ce nettoyage, dashboard.service et
# morfdashboard.service piloteraient tous deux le même écran SPI.
LEGACY_UNIT="/etc/systemd/system/dashboard.service"
if [[ -f "$LEGACY_UNIT" ]]; then
    echo "Ancien service 'dashboard' détecté : désactivation (remplacé par 'morfdashboard')."
    systemctl disable --now dashboard 2>/dev/null || true
    rm -f "$LEGACY_UNIT"
    systemctl daemon-reload
fi

# --- 2. Copier l'application dans le dossier fixe -------------------------
mkdir -p "$APP_DIR"
if command -v rsync >/dev/null; then
    rsync -a --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
             --exclude='*_preview.png' --exclude='config.local.py' \
             "$REPO_ROOT"/ "$APP_DIR"/
else
    cp -a "$REPO_ROOT"/. "$APP_DIR"/
    rm -rf "$APP_DIR/.git" "$APP_DIR"/**/__pycache__ "$APP_DIR/config.local.py" 2>/dev/null || true
fi
chown -R "$RUN_USER:$RUN_USER" "$APP_DIR"
echo "Application copiée dans $APP_DIR"

# --- 3. Installer/preserver la configuration locale ----------------------
mkdir -p "$CONFIG_DIR"
if [[ "$REFRESH_CONFIG" -eq 1 && -f "$CONFIG_FILE" ]]; then
    BACKUP="$CONFIG_FILE.$(date +%Y%m%d-%H%M%S).bak"
    cp -a "$CONFIG_FILE" "$BACKUP"
    install -m 0644 "$REPO_ROOT/config.local.example.py" "$CONFIG_FILE"
    echo "Config locale remplacée : $CONFIG_FILE (sauvegarde : $BACKUP)."
elif [[ ! -f "$CONFIG_FILE" ]]; then
    install -m 0644 "$REPO_ROOT/config.local.example.py" "$CONFIG_FILE"
    echo "Config initiale copiée : $CONFIG_FILE (à adapter si besoin)."
else
    echo "Config existante conservée : $CONFIG_FILE"
fi

# --- 4. Installer et démarrer le service ---------------------------------
sed -e "s/__RUN_USER__/$RUN_USER/g" -e "s#__APP_DIR__#$APP_DIR#g" \
    "$SCRIPT_DIR/morfdashboard.service" > "$UNIT_DEST"
chmod 0644 "$UNIT_DEST"
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
echo "Service '$SERVICE_NAME' installé (ExecStart -> $APP_DIR/dashboard.py) et démarré."

# --- 5. Détecter d'autres démarrages automatiques (à nettoyer à la main) --
echo
echo "Vérification d'anciens lancements résiduels…"
FOUND=0
if crontab -u "$RUN_USER" -l 2>/dev/null | grep -iqE "dashboard|morfDashboard"; then
    echo "  ⚠ crontab de $RUN_USER contient une entrée dashboard — à retirer :  crontab -u $RUN_USER -e"; FOUND=1
fi
if [[ -f /etc/rc.local ]] && grep -iqE "dashboard|morfDashboard" /etc/rc.local; then
    echo "  ⚠ /etc/rc.local référence dashboard — à retirer manuellement"; FOUND=1
fi
for f in "/home/$RUN_USER/.config/autostart/"*dashboard* "/home/$RUN_USER/.config/autostart/"*Dashboard*; do
    [[ -e "$f" ]] && { echo "  ⚠ autostart bureau : $f — à retirer"; FOUND=1; }
done
[[ "$FOUND" -eq 0 ]] && echo "  Aucun autre lancement automatique détecté. Le service 'morfdashboard' a remplacé l'ancien."

echo
sleep 1
systemctl --no-pager --lines=0 status "$SERVICE_NAME" || true
echo
echo "Journaux :  journalctl -u $SERVICE_NAME -f"

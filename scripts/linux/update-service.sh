#!/usr/bin/env bash
#
# update-service.sh — Met à jour morfDashboard installé en service.
#
# Récupère le code (git pull), recopie l'application dans le dossier fixe, puis
# redémarre le service. Sans compilation (Python). Complément de install-service.sh.
#
# Usage :
#   sudo ./scripts/linux/update-service.sh          # git pull + recopie + restart
#   sudo ./scripts/linux/update-service.sh --no-pull # recopie seulement
#   sudo ./scripts/linux/update-service.sh --refresh-config # sauvegarde + remplace la config locale

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
NO_PULL=0
REFRESH_CONFIG=0

FORCE=0

for arg in "$@"; do
    case "$arg" in
        --no-pull) NO_PULL=1 ;;
        --refresh-config) REFRESH_CONFIG=1 ;;
        --force) FORCE=1 ;;
    esac
done

if [[ "${EUID}" -ne 0 ]]; then
    echo "Ce script doit être lancé avec sudo :  sudo $0 $*" >&2
    exit 1
fi
if [[ ! -f "$UNIT_DEST" ]]; then
    echo "Service '$SERVICE_NAME' non installé. Lance d'abord :  sudo ./scripts/linux/install-service.sh" >&2
    exit 1
fi

# --- Récupérer le code (en tant que l'utilisateur) -----------------------
# Avant l'arrêt : récupérer le code ne demande pas que le service soit stoppé,
# et il faut disposer du code final pour savoir s'il y a seulement quelque
# chose à déployer.
if [[ "$NO_PULL" -ne 1 ]]; then
    echo "git pull (utilisateur $RUN_USER)…"
    sudo -u "$RUN_USER" bash -c "cd '$REPO_ROOT' && git pull --ff-only"
fi

# --- Y a-t-il seulement quelque chose à faire ? --------------------------
# Arrêter le service, recopier des fichiers identiques et le redémarrer n'est
# pas neutre : c'est une coupure de supervision et un uptime remis à zéro, payés
# au moment précis où l'on croyait ne rien toucher. rsync sait dire, à blanc, ce
# qu'il changerait ; s'il ne changerait rien et que la configuration est en
# place, il n'y a pas de mise à jour à faire.
#
# Sans rsync, la détection est impossible et on déploie comme avant : mieux vaut
# un redémarrage inutile qu'une mise à jour silencieusement omise.
if [[ "$FORCE" -ne 1 && "$REFRESH_CONFIG" -ne 1 ]] && command -v rsync >/dev/null; then
    PENDING="$(rsync -a --itemize-changes --dry-run \
        --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
        --exclude='*_preview.png' --exclude='config.local.py' \
        "$REPO_ROOT"/ "$APP_DIR"/ 2>/dev/null || echo "indetermine")"
    if [[ -z "$PENDING" && -f "$CONFIG_FILE" ]]; then
        echo "morfDashboard est déjà à jour : aucun fichier à recopier, configuration en place."
        echo "Rien n'a été déployé, le service n'a PAS été redémarré."
        echo "Utiliser --force pour redéployer et redémarrer malgré tout."
        exit 0
    fi
fi

SERVICE_WAS_ACTIVE=0
if systemctl is-active --quiet "$SERVICE_NAME"; then
    SERVICE_WAS_ACTIVE=1
fi

# --- Arreter avant toute mise a jour ------------------------------------
echo "Arrêt de $SERVICE_NAME avant mise à jour…"
systemctl stop "$SERVICE_NAME" 2>/dev/null || true

# --- Recopier l'application ----------------------------------------------
echo "Recopie vers $APP_DIR…"
if command -v rsync >/dev/null; then
    rsync -a --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
             --exclude='*_preview.png' --exclude='config.local.py' \
             "$REPO_ROOT"/ "$APP_DIR"/
else
    cp -a "$REPO_ROOT"/. "$APP_DIR"/
    rm -rf "$APP_DIR/.git" "$APP_DIR"/**/__pycache__ "$APP_DIR/config.local.py" 2>/dev/null || true
fi
chown -R "$RUN_USER:$RUN_USER" "$APP_DIR"

# --- Installer la config locale si elle n'existe pas encore --------------
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

# --- Rafraichir l'unite systemd -----------------------------------------
sed -e "s/__RUN_USER__/$RUN_USER/g" -e "s#__APP_DIR__#$APP_DIR#g" \
    "$SCRIPT_DIR/morfdashboard.service" > "$UNIT_DEST"
chmod 0644 "$UNIT_DEST"
systemctl daemon-reload

# --- Redémarrer si le service tournait, sinon le laisser arrêté ----------
if [[ "$SERVICE_WAS_ACTIVE" -eq 1 ]]; then
    systemctl start "$SERVICE_NAME"
else
    echo "Service laissé arrêté (il ne tournait pas avant la mise à jour)."
fi
sleep 1
echo "Mise à jour appliquée."
systemctl --no-pager --lines=0 status "$SERVICE_NAME" || true

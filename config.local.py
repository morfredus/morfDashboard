# Configuration locale morfDashboard.
#
# Copier vers /etc/morfsystem/morfdashboard/config.local.py puis adapter. Seules les
# constantes a surcharger sont necessaires ici ; config.py fournit les defauts.

# Exemple : choisir les canaux morfNotify utilises par les alertes persistantes.
# ALERT_NOTIFY_TARGETS = ["email"]
ALERT_NOTIFY_TARGETS = ["telegram"]
# ALERT_NOTIFY_TARGETS = ["email", "telegram"]

# Exemple : desactiver les notifications sans toucher au code installe.
# ALERT_NOTIFY_ENABLED = False

# Ajouter seulement les services propres a cette machine. Les dictionnaires
# locaux sont fusionnés avec ceux de config.py : les services livrés avec le
# dashboard restent donc visibles après une mise à jour.
SERVICE_LABELS = {
# "morfnotify": "morfNotify",  # service systemd local (Notifications)
}

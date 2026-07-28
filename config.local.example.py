# Configuration locale morfDashboard.
#
# Copier vers /etc/morfsystem/morfdashboard/config.local.py puis adapter. Seules les
# constantes a surcharger sont necessaires ici ; config.py fournit les defauts.

# Canaux morfNotify utilises par les alertes persistantes.
# Choisir ["email"], ["telegram"] ou ["email", "telegram"] selon les
# destinations configurees dans morfNotify.
ALERT_NOTIFY_TARGETS = ["telegram"]

# Activer/desactiver les notifications sans toucher au code installe.
ALERT_NOTIFY_ENABLED = True
# ALERT_NOTIFY_ENABLED = False

# Delais de test courts. Remonter ces valeurs en production si besoin.
ALERT_MIN_DURATION_SECONDS = 5 * 60
ALERT_SERVICE_MIN_DURATION_SECONDS = 2 * 60
ALERT_REPEAT_COOLDOWN_SECONDS = 6 * 60 * 60

# Ajouter seulement les services propres a cette machine. Les dictionnaires
# locaux sont fusionnés avec ceux de config.py : les services livrés avec le
# dashboard restent donc visibles après une mise à jour.
SERVICE_LABELS = {
#    "morfnotify": "morfNotify",
}

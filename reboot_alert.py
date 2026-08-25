import time
from datetime import datetime

from pathlib import Path

try:
    from config import REBOOT_ALERT_ACK_FILE
except Exception:
    REBOOT_ALERT_ACK_FILE = Path("/home/morfredus/Logs/.dashboard_reboot_ack")

try:
    from config import REBOOT_ALERT_BOOT_WINDOW_SECONDS
except Exception:
    REBOOT_ALERT_BOOT_WINDOW_SECONDS = 10 * 60

try:
    from config import REBOOT_ALERT_LOG_DIR
except Exception:
    REBOOT_ALERT_LOG_DIR = Path("/home/morfredus/Logs")

try:
    from config import REBOOT_ALERT_PATTERNS
except Exception:
    REBOOT_ALERT_PATTERNS = ("Boot_*",)

try:
    from config import REBOOT_EXPECTED_FILE
except Exception:
    REBOOT_EXPECTED_FILE = Path("/home/morfredus/Logs/.dashboard_expected_reboot")


def _uptime_seconds():
    try:
        with open("/proc/uptime") as f:
            return float(f.readline().split()[0])
    except Exception:
        return float("inf")


def _boot_time():
    uptime = _uptime_seconds()
    if uptime == float("inf"):
        return 0
    return time.time() - uptime


def _read_ack():
    try:
        return REBOOT_ALERT_ACK_FILE.read_text().strip()
    except Exception:
        return ""


def _write_ack(report_name):
    REBOOT_ALERT_ACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    REBOOT_ALERT_ACK_FILE.write_text(f"{report_name}\n")


def _reports():
    if not REBOOT_ALERT_LOG_DIR.is_dir():
        return []

    reports = []
    seen = set()
    for pattern in REBOOT_ALERT_PATTERNS:
        for path in REBOOT_ALERT_LOG_DIR.glob(pattern):
            if path in seen or not path.is_dir():
                continue
            seen.add(path)
            reports.append(path)
    return reports


def _current_boot_reports():
    boot_time = _boot_time()
    window = REBOOT_ALERT_BOOT_WINDOW_SECONDS
    return [
        path for path in _reports()
        if abs(path.stat().st_mtime - boot_time) <= window
    ]


def current_reboot_report():
    reports = _current_boot_reports()
    if not reports:
        return None
    return max(reports, key=lambda path: path.stat().st_mtime)


def _consume_expected_marker():
    """Vrai si un redémarrage/arrêt VOLONTAIRE avait été signalé (bouton).

    Le marqueur est à usage unique : on le supprime dès qu'on le lit, pour qu'il
    n'acquitte que le boot qui suit l'action volontaire. Un reboot inattendu plus
    tard ne trouvera aucun marqueur et affichera bien le badge.
    """
    try:
        if REBOOT_EXPECTED_FILE.exists():
            REBOOT_EXPECTED_FILE.unlink()
            return True
    except Exception:
        pass
    return False


def get_reboot_alert():
    try:
        report = current_reboot_report()
        if report is None or _read_ack() == report.name:
            return {"active": False, "count": 0, "latest": None, "acknowledged": True}

        # Redémarrage/arrêt volontaire (bouton d'alimentation) : marqueur posé
        # avant l'action. On acquitte ce boot automatiquement et on consomme le
        # marqueur, pour ne pas afficher le badge REBOOT sur une action demandée.
        if _consume_expected_marker():
            _write_ack(report.name)
            return {"active": False, "count": 0, "latest": None, "acknowledged": True}

        latest_time = datetime.fromtimestamp(report.stat().st_mtime)
        return {
            "active": True,
            "count": 1,
            "latest": latest_time.strftime("%d/%m %H:%M"),
            "report": report.name,
            "acknowledged": False,
        }
    except Exception:
        return {"active": False, "count": 0, "latest": None, "acknowledged": False}


def acknowledge_current_reboot():
    report = current_reboot_report()
    if report is None:
        return None
    _write_ack(report.name)
    return report.name

"""
beacon_listener.py
Ecoute passive des heartbeats morfBeacon (UDP broadcast) emis par les
applications de bureau (ComponentHub, SiteWatch, futurs outils).

Le dashboard ne sonde rien : il ECOUTE le port BEACON_PORT et tient a jour, pour
chaque application vue, la date du dernier heartbeat et son etat. Une application
est « en ligne » si son dernier heartbeat date de moins de BEACON_OFFLINE_AFTER
secondes.

Un seul ecouteur pour tout le programme, dans un thread de fond : demarre une
fois par dashboard.py via start(). Aucune dependance externe (stdlib seule).
"""

import json
import socket
import threading
import time

from config import BEACON_PORT, BEACON_OFFLINE_AFTER

_PROTO_PREFIX = "morfbeacon/"   # champ "proto" attendu, ex. "morfbeacon/1"


class BeaconListener:
    def __init__(self, port=BEACON_PORT):
        self._port = port
        self._lock = threading.Lock()
        # Indexe par INSTANCE (app, host) et non par seul nom : le meme service
        # tournant sur deux machines (pi4fred et pi4dev) est deux instances. Les
        # confondre sous le seul nom les faisait s'ecraser l'une l'autre, et
        # empechait de distinguer l'instance LOCALE d'une instance distante -- ce
        # qui est justement ce qu'un dashboard local doit savoir.
        self._inst = {}          # (app, host) -> {last, state, role, host, version, ip, status_port}
        self._thread = None

    def start(self):
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="beacon", daemon=True)
        self._thread.start()

    def _run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            # Permet a plusieurs ecouteurs (le service dashboard + l'outil
            # beacon_status.py lance en SSH) de recevoir le meme broadcast.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass  # SO_REUSEPORT indisponible (ex. Windows) : coexistence best-effort
        try:
            sock.bind(("", self._port))
        except OSError:
            # Port occupe : on renonce a l'ecoute, le dashboard fonctionne sans.
            return

        while True:
            try:
                data, addr = sock.recvfrom(2048)
            except OSError:
                continue
            try:
                msg = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if not str(msg.get("proto", "")).startswith(_PROTO_PREFIX):
                continue
            app = msg.get("app")
            if not app:
                continue
            host = msg.get("host")

            with self._lock:
                self._inst[(app, host)] = {
                    "last": time.monotonic(),
                    "state": msg.get("state", "ok"),
                    # role du protocole morfBeacon : "host" (service sur une machine)
                    # ou "device" (equipement autonome). Absent => "host", defaut
                    # historique. Sert au filtrage « local » du dashboard.
                    "role": msg.get("role", "host"),
                    "host": host,
                    "version": msg.get("version"),
                    "ip": addr[0],
                    "status_port": int(msg.get("status_port", 0) or 0),
                }

    def _fresh_instances(self, app):
        """Instances FRAICHES d'une application (une par machine)."""
        now = time.monotonic()
        with self._lock:
            return [dict(e) for (a, _h), e in self._inst.items()
                    if a == app and (now - e["last"]) <= BEACON_OFFLINE_AFTER]

    def status(self, app):
        """(online, state) pour 'app', toutes machines confondues.

        En ligne si AU MOINS une instance est fraiche : c'est la vue « ce service
        tourne-t-il quelque part sur le parc ? », utile a l'outil de diagnostic.
        """
        fresh = self._fresh_instances(app)
        if not fresh:
            return False, None
        # Etat de l'instance vue le plus recemment.
        latest = max(fresh, key=lambda e: e["last"])
        return True, latest.get("state")

    def local_status(self, app, local_host):
        """(online, state) pour la seule instance LOCALE de 'app'.

        Locale = un equipement (role device, ou qu'il soit) ou un service tournant
        sur CETTE machine (host == local_host). Une instance distante ne compte pas :
        le dashboard est exclusivement local. (False, None) si aucune instance
        locale n'est fraiche.
        """
        candidates = []
        for e in self._fresh_instances(app):
            is_device = e.get("role", "host") == "device"
            is_local = (e.get("host") and local_host
                        and str(e["host"]).lower() == str(local_host).lower())
            if is_device or is_local:
                candidates.append(e)
        if not candidates:
            return False, None
        return True, max(candidates, key=lambda e: e["last"]).get("state")

    def snapshot(self):
        """Copie {app: {...,'online':bool}} par application (instance la plus fraiche).

        Collapse volontaire des instances vers le nom d'application : l'outil de
        diagnostic beacon_status.py veut une vue par application, pas par machine.
        """
        now = time.monotonic()
        with self._lock:
            out = {}
            for (app, _host), entry in self._inst.items():
                online = (now - entry["last"]) <= BEACON_OFFLINE_AFTER
                prev = out.get(app)
                if prev is None or entry["last"] > prev["_last_raw"]:
                    out[app] = {**entry, "online": online, "_last_raw": entry["last"]}
            for e in out.values():
                e.pop("_last_raw", None)
            return out


# --- Singleton pratique -------------------------------------------------------
# systeminfo.py interroge cet ecouteur unique ; dashboard.py le demarre au boot.

_listener = None


def start():
    """Demarre l'ecouteur unique (idempotent). A appeler une fois au demarrage."""
    global _listener
    if _listener is None:
        _listener = BeaconListener()
        _listener.start()
    return _listener


def status(app):
    """(online, state) pour 'app' ; (False, None) si l'ecouteur n'est pas demarre."""
    if _listener is None:
        return False, None
    return _listener.status(app)


def local_status(app, local_host):
    """(online, state) pour la seule instance LOCALE de 'app' (voir la methode).

    (False, None) si l'ecouteur n'est pas demarre.
    """
    if _listener is None:
        return False, None
    return _listener.local_status(app, local_host)

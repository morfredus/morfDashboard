#!/usr/bin/env python3
"""
beacon_status.py
Outil en ligne de commande (typiquement lancé en SSH) : découvre les applications
morfBeacon vivantes sur le réseau local, interroge leur endpoint HTTP /status et
affiche leurs métriques détaillées. Produit aussi un rapport Markdown lisible.

L'écran du dashboard ne montre que la PRÉSENCE (pastilles). Cet outil sert à
consulter le DÉTAIL à la demande, sans clavier ni souris sur le Raspberry.

Exemples :
    python3 beacon_status.py                 # écoute 4 s, console + beacon_status.md
    python3 beacon_status.py --listen 8      # fenêtre d'écoute plus longue
    python3 beacon_status.py --app SiteWatch # une seule application
    python3 beacon_status.py -o rapport.md   # chemin du rapport Markdown
    python3 beacon_status.py --no-file       # console seulement (pas de fichier)

Aucune dépendance externe (bibliothèque standard + config.py / beacon_listener.py).
"""

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime

from config import BEACON_PORT
from beacon_listener import BeaconListener

STATE_EMOJI = {"ok": "🟢", "warning": "🟠", "error": "🔴", "starting": "⚪"}


def _fetch_status(ip, port, timeout=2.0):
    """GET http://ip:port/status -> dict (lève une exception en cas d'échec)."""
    url = f"http://{ip}:{port}/status"
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _human_uptime(seconds):
    try:
        s = int(seconds)
    except (TypeError, ValueError):
        return "?"
    days, rem = divmod(s, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    if days:
        return f"{days} j {hours} h"
    if hours:
        return f"{hours} h {minutes} min"
    return f"{minutes} min"


def collect(listen_seconds, port, app_filter):
    """Écoute les heartbeats puis interroge /status. Retourne {app: infos}."""
    listener = BeaconListener(port=port)
    listener.start()
    time.sleep(listen_seconds)

    result = {}
    for app, entry in listener.snapshot().items():
        if not entry.get("online"):
            continue
        if app_filter and app.lower() != app_filter.lower():
            continue

        info = dict(entry)
        info["status"] = None
        info["status_error"] = None

        status_port = entry.get("status_port") or 0
        if status_port:
            try:
                info["status"] = _fetch_status(entry["ip"], status_port)
            except Exception as exc:  # réseau, timeout, JSON...
                info["status_error"] = str(exc)

        result[app] = info
    return result


def render_markdown(apps, listen_seconds, port):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out = [
        f"# État des applications - {now}",
        "",
        f"_Découverte : écoute morfBeacon pendant {listen_seconds:.0f} s "
        f"sur le port UDP {port}._",
        "",
    ]

    if not apps:
        out += ["Aucune application détectée sur le réseau local.", ""]
        return "\n".join(out)

    out += [f"**{len(apps)} application(s) en ligne.**", ""]

    for app in sorted(apps):
        e = apps[app]
        status = e.get("status") or {}
        state = status.get("state") or e.get("state") or "?"
        emoji = STATE_EMOJI.get(state, "⚫")

        out.append(f"## {emoji} {app} - {state}")
        out.append("")
        out.append(f"- **Hôte** : {e.get('host', '?')} (`{e.get('ip', '?')}`)")
        out.append(f"- **Version** : {e.get('version', '?')}")
        uptime = status.get("uptime_s", e.get("uptime_s"))
        if uptime is not None:
            out.append(f"- **Uptime** : {_human_uptime(uptime)} ({int(uptime)} s)")
        out.append(f"- **Port /status** : {e.get('status_port', 0) or '-'}")
        out.append("")

        if e.get("status_error"):
            out.append(f"> ⚠️ `/status` injoignable : {e['status_error']}")
            out.append("")
        elif status.get("metrics"):
            out.append("| Métrique | Valeur |")
            out.append("|---|---|")
            for key, value in status["metrics"].items():
                out.append(f"| `{key}` | {value} |")
            out.append("")
        elif e.get("status_port"):
            out.append("_Aucune métrique exposée par `/status`._")
            out.append("")
        else:
            out.append("_Présence seule (pas de serveur `/status`)._")
            out.append("")

    return "\n".join(out)


def print_console(apps):
    if not apps:
        print("Aucune application détectée sur le réseau local.")
        return
    for app in sorted(apps):
        e = apps[app]
        status = e.get("status") or {}
        state = status.get("state") or e.get("state") or "?"
        emoji = STATE_EMOJI.get(state, "?")
        print(f"{emoji} {app}  v{e.get('version', '?')}  @ {e.get('ip', '?')}  ({state})")
        if e.get("status_error"):
            print(f"    /status : ECHEC ({e['status_error']})")
        elif status.get("metrics"):
            for key, value in status["metrics"].items():
                print(f"    {key} = {value}")
        elif not e.get("status_port"):
            print("    (présence seule, pas de /status)")


def main():
    parser = argparse.ArgumentParser(
        description="Découvre les applications morfBeacon et affiche leurs "
                    "métriques /status. Produit un rapport Markdown.")
    parser.add_argument("--listen", type=float, default=4.0,
                        help="durée d'écoute des heartbeats, en secondes (défaut 4)")
    parser.add_argument("--port", type=int, default=BEACON_PORT,
                        help=f"port UDP du heartbeat (défaut {BEACON_PORT})")
    parser.add_argument("--app", help="ne montrer qu'une application (par son nom)")
    parser.add_argument("-o", "--output", default="beacon_status.md",
                        help="chemin du rapport Markdown (défaut beacon_status.md)")
    parser.add_argument("--no-file", action="store_true",
                        help="afficher en console sans écrire de fichier")
    args = parser.parse_args()

    # Console en UTF-8 quand c'est possible (emojis d'état) ; sinon on remplace
    # les caractères non encodables plutôt que de planter.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print(f"Écoute des heartbeats morfBeacon pendant {args.listen:.0f} s "
          f"(port {args.port})...")
    apps = collect(args.listen, args.port, args.app)

    # Le rapport Markdown est le livrable principal : on l'écrit d'abord.
    if not args.no_file:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(render_markdown(apps, args.listen, args.port))

    print()
    print_console(apps)

    if not args.no_file:
        print(f"\nRapport Markdown écrit : {args.output}")


if __name__ == "__main__":
    main()

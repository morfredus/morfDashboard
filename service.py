#!/usr/bin/env python3
"""Installe, met a jour ou retire morfDashboard — meme interface que le parc.

    ./service.py install       installe et demarre le service
    ./service.py update        recopie l'application et redemarre
    ./service.py uninstall     retire le service, garde la configuration
    ./service.py status        ce que systemd dit de lui
    ./service.py is-installed  muet : le code de retour EST la reponse

Pourquoi ce fichier existe, alors que morfDashboard garde ses scripts shell.

Tous les autres services du parc exposent un `service.py` adosse a morfdeploy,
et morfTools s'appuie sur cette regle : un projet qui est un service a un
`service.py`. morfDashboard ne rentrait pas dans ce moule — c'est une
application Python deployee par rsync depuis l'arbre des sources, la ou
morfdeploy copie un binaire compile — si bien qu'il restait un cas particulier.

Le cout de ce cas particulier a fini par se voir : `morf.py upgrade` recuperait
son nouveau code et laissait le service tourner sur l'ancien, en silence, parce
qu'aucun `service.py` ne repondait. Plutot que d'apprendre l'exception a
morfTools, morfDashboard adopte l'interface commune et garde sa mecanique.

Ce fichier ne reimplemente donc rien : il traduit une interface. Le deploiement
reste entierement dans scripts/linux/, qui connait le rsync, les exclusions, la
config locale et l'unite systemd — la connaissance du projet reste dans le
projet.
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LINUX_SCRIPTS = HERE / "scripts" / "linux"

#: Nom de l'unite systemd. Le meme que dans les scripts shell ; il est repete
#: ici plutot que devine, parce qu'une deduction silencieusement fausse
#: repondrait « pas installe » pour un service qui tourne.
SERVICE_NAME = "morfdashboard"

#: morfDashboard pilote un ecran SPI (ILI9341 / ST7789) sur un Raspberry Pi et
#: s'installe en unite systemd : il n'y a pas de version Windows a installer, et
#: le dire vaut mieux que lancer bash sur une machine qui n'en a pas.
SUPPORTED = "Linux"


def unsupported_note() -> str:
    return (
        f"morfDashboard s'installe sous {SUPPORTED} (unite systemd, ecran SPI "
        f"d'un Raspberry Pi).\nCette machine est sous {platform.system()} : rien "
        "a installer ici."
    )


def run_script(name: str, args: list) -> int:
    script = LINUX_SCRIPTS / name
    if not script.is_file():
        print(f"Script introuvable : {script}", file=sys.stderr)
        return 2
    # `bash <script>` plutot que `./<script>` : le bit d'execution se perd a
    # chaque promotion depuis Windows, et un deploiement ne doit pas dependre
    # d'un attribut de fichier que la copie ne transporte pas.
    return subprocess.run(["bash", str(script), *args], cwd=HERE, check=False).returncode


def is_installed() -> bool:
    """Vrai quand l'unite est connue de systemd.

    Interroge systemd plutot que de tester la presence du fichier d'unite :
    c'est le gestionnaire de services qui fait autorite sur ce qu'il connait.
    Aucun privilege n'est requis — lister les unites est une lecture.
    """
    probe = subprocess.run(
        ["systemctl", "list-unit-files", f"{SERVICE_NAME}.service"],
        capture_output=True, text=True, check=False,
    )
    return SERVICE_NAME in probe.stdout


def require_root(action: str) -> bool:
    if hasattr(os, "geteuid") and os.geteuid() != 0:
        print(f"'{action}' ecrit dans /opt, /etc et /etc/systemd/system.",
              file=sys.stderr)
        print(f"Relancer avec :  sudo ./service.py {action}", file=sys.stderr)
        return False
    return True


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="service.py",
        description="Installe, met a jour ou retire le service morfDashboard.",
    )
    parser.add_argument(
        "action",
        choices=("install", "update", "uninstall", "status", "is-installed", "config"),
        help="Ce qu'il faut faire",
    )
    # morfTools appelle « config push --force » / « config merge » sur CHAQUE
    # service.py du parc. morfDashboard doit accepter ce verbe comme il accepte
    # deja --repo, sinon un deploiement « replace » du parc echoue ici seul.
    parser.add_argument(
        "mode", nargs="?", default="",
        help="config : 'push' (remplace la config depuis le depot) ou 'merge'",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="update : redeployer et redemarrer meme si rien n'a change",
    )
    parser.add_argument(
        "--purge", action="store_true",
        help="uninstall : non supporte par ce projet, signale et ignore",
    )
    parser.add_argument(
        "--backup", metavar="DIR", default="",
        help="uninstall --purge : non supporte par ce projet",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="uninstall : montre ce qui serait retire sans rien toucher",
    )
    # Accepte et ignore : morfTools passe --repo aux service.py du parc, et
    # refuser l'option ferait echouer un balayage sur une difference de forme.
    parser.add_argument("--repo", default="", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    # Un dry-run d'uninstall ne touche a rien : il decrit le meme plan que
    # l'execution reelle, sans privilege, et doit reussir sur toute plateforme
    # (un balayage `morf uninstall --all --dry-run` passe aussi par ici sous
    # Windows, ou il n'y a simplement rien a retirer). Traite AVANT le controle
    # de plateforme et AVANT require_root, comme le dry-run de morfdeploy.
    if args.action == "uninstall" and args.dry_run:
        print("Would uninstall morfDashboard")
        if platform.system() != SUPPORTED:
            print(f"    not applicable on {platform.system()} (Linux-only service)")
        elif is_installed():
            print("    would deregister the service (systemctl disable --now)")
        else:
            print(f"    {SERVICE_NAME}.service is not installed here")
        print("Configuration would be kept (this project does not support --purge).")
        print("\nNothing was removed (--dry-run).")
        return 0

    if platform.system() != SUPPORTED:
        # `is-installed` doit rester muet et repondre par son code de retour :
        # rien n'est installe ici, et ce n'est pas une erreur.
        if args.action == "is-installed":
            return 1
        print(unsupported_note(), file=sys.stderr)
        return 3

    if args.action == "is-installed":
        # 0 installe, 1 absent. Jamais 2 (« impossible de savoir ») : sous
        # Linux, interroger systemd ne demande aucun privilege.
        return 0 if is_installed() else 1

    if args.action == "status":
        if not is_installed():
            print(f"morfDashboard : non installe ({SERVICE_NAME}.service inconnu de systemd)")
            return 0
        return subprocess.run(
            ["systemctl", "--no-pager", "--lines=0", "status", SERVICE_NAME],
            check=False,
        ).returncode

    if args.action == "config":
        # Config de morfDashboard = un fichier Python (config.local.py), pas un
        # JSON fusionnable. « merge » (ajouter des cles sans toucher aux valeurs)
        # n'a donc pas de sens ici : on conserve la config locale et on le dit,
        # plutot que d'echouer ou d'ecraser en silence.
        if args.mode == "merge":
            if not require_root("config"):
                return 2
            print("morfDashboard : config Python (config.local.py) ; 'merge' sans "
                  "objet, configuration locale conservee.")
            return 0
        # « push » (defaut) : remplacer la config depuis le depot, avec sauvegarde.
        # La logique vit deja dans install-service.sh (--refresh-config), source
        # unique de verite du placement de config ; on la reutilise.
        if not require_root("config"):
            return 2
        return run_script("install-service.sh", ["--refresh-config"])

    if not require_root(args.action):
        return 2

    if args.action == "install":
        return run_script("install-service.sh", [])

    if args.action == "update":
        if not is_installed():
            print("morfDashboard n'est pas installe sur cette machine.",
                  file=sys.stderr)
            print("Lancer d'abord :  sudo ./service.py install", file=sys.stderr)
            return 1
        # --no-pull : recuperer le code est le travail de morf.py, deployer est
        # le notre. C'est le meme partage que pour les services morfdeploy, dont
        # l'`update` ne fait jamais de git pull non plus.
        opts = ["--no-pull"]
        if args.force:
            opts.append("--force")
        return run_script("update-service.sh", opts)

    # uninstall
    if args.purge or args.backup:
        print("[note] --purge n'est pas supporte par ce projet : le service est "
              "retire, sa configuration reste en place", file=sys.stderr)
    return run_script("install-service.sh", ["--uninstall"])


if __name__ == "__main__":
    sys.exit(main())

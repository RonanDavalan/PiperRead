"""
piper_server_entry.py — point d'entrée gelé séparément pour le paquet Windows.

Pourquoi ce fichier existe :
    PyInstaller gèle un point d'entrée par exécutable. Le serveur HTTP de
    Piper tourne en processus séparé, jamais lié dans `piperread-gui.exe`
    (frontière GPL actée dans `server.py`) : il lui faut donc son propre
    exécutable gelé, `piper-http-server.exe`
    (`gui/packaging/windows/piper-http-server.spec`), que `server.py` invoque
    par son chemin sur Windows, à la place de `python3 -m piper.http_server`.
    Ce fichier ne fait rien d'autre qu'appeler `piper.http_server.main`
    telle quelle : les arguments de la ligne de commande (`--host`, `--port`,
    `--model`) viennent de `server._commande_serveur`, jamais d'ici.

Dépend de :
    `piper.http_server` (paquet `piper-tts[http]`).
"""

from piper.http_server import main

if __name__ == "__main__":
    raise SystemExit(main())

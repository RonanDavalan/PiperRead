"""
piper_server_entry.py — lance le serveur HTTP de Piper dans le processus du moteur.

Pourquoi ce fichier existe :
    L'interface ne lie jamais Piper (GPL) dans son propre processus
    (`server.py`) : ce fichier est exécuté par l'interpréteur du moteur (le
    venv de Piper sous Linux) ou gelé en `piper-http-server.exe` sous Windows
    (`gui/packaging/windows/piper-http-server.spec`), et n'importe rien de
    l'interface. Les arguments (`--host`, `--port`, `--model`) viennent de
    `server._commande_serveur` et passent tels quels à `piper.http_server`.

    Deux choses doivent précéder le chargement de la voix :
    - couper les événements de télémétrie d'onnxruntime par son API quand
      `ORT_DISABLE_TELEMETRY=1` : sous Windows la variable seule n'a aucun
      effet (événements ETW relevés par le service de diagnostic du
      système, décision « télémétrie du moteur d'inférence ») ;
    - surveiller l'interface (`PIPERREAD_PARENT_PID`) : le serveur garde la
      voix chargée tant qu'elle vit, et ne doit pas lui survivre si elle
      disparaît sans l'avoir arrêté.
    Sous Windows, les chemins accentués sont réglés par le manifeste de
    l'exécutable gelé (page de code UTF-8, `piper-http-server.spec`), pas ici.

    Le premier argument `download-voices` ouvre à la place le module de
    téléchargement de voix du moteur (`piper.download_voices`), avec les
    arguments qui suivent : l'exécutable Windows gelé n'a pas d'interpréteur
    où lancer `-m piper.download_voices`, et la fenêtre de voix
    (`voice_download.py`) utilise la même entrée sur les deux systèmes.

Dépend de :
    `piper.http_server` (paquet `piper-tts[http]`) et `onnxruntime`.
"""

import os
import sys
import threading
import time
from pathlib import Path

# Exécuté comme script, ce fichier met son propre dossier en tête de
# sys.path : les modules de l'interface (config.py, server.py…) y
# masqueraient des modules homonymes du moteur.
if sys.path and Path(sys.path[0]).resolve() == Path(__file__).resolve().parent:
    del sys.path[0]

_INTERVALLE_SURVEILLANCE_SECONDES = 1.0


def couper_telemetrie_si_demande(environnement=os.environ) -> bool:
    if environnement.get("ORT_DISABLE_TELEMETRY") != "1":
        return False
    import onnxruntime

    onnxruntime.disable_telemetry_events()
    return True


def _attendre_fin_windows(pid: int) -> bool:
    import ctypes

    synchronize = 0x00100000
    infini = 0xFFFFFFFF
    noyau = ctypes.windll.kernel32
    poignee = noyau.OpenProcess(synchronize, False, pid)
    if not poignee:
        return False
    noyau.WaitForSingleObject(poignee, infini)
    return True


def _attendre_fin_posix(pid: int) -> bool:
    while os.getppid() == pid:
        time.sleep(_INTERVALLE_SURVEILLANCE_SECONDES)
    return True


def surveiller_parent(environnement=os.environ) -> threading.Thread | None:
    valeur = environnement.get("PIPERREAD_PARENT_PID", "")
    if not valeur.isdigit():
        return None
    pid = int(valeur)
    attendre = _attendre_fin_windows if sys.platform == "win32" else _attendre_fin_posix

    def surveiller() -> None:
        if attendre(pid):
            os._exit(0)

    fil = threading.Thread(target=surveiller, name="surveillance-interface", daemon=True)
    fil.start()
    return fil


def telecharger_voix(arguments: list[str]) -> int:
    from piper.download_voices import main as telecharger

    sys.argv = [sys.argv[0], *arguments]
    telecharger()
    return 0


def main() -> int:
    if sys.argv[1:2] == ["download-voices"]:
        return telecharger_voix(sys.argv[2:])

    surveiller_parent()
    couper_telemetrie_si_demande()

    from piper.http_server import main as lancer_serveur

    return lancer_serveur()


if __name__ == "__main__":
    raise SystemExit(main())

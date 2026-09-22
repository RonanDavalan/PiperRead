"""
player.py — joue un WAV reçu du serveur de synthèse sur la sortie audio par défaut.

Pourquoi ce fichier existe :
    Le serveur renvoie un WAV complet en mémoire, jamais un fichier sur
    disque ; la lecture se fait donc directement depuis les octets reçus,
    sans écriture temporaire.

Entrée / sortie :
    Entrée : les octets d'un fichier WAV mono ou stéréo, 16 bits, et deux
    événements optionnels (`stop_event`, `pause_event`) pour interrompre ou
    suspendre la lecture en cours depuis un autre fil. Sortie : aucune
    (lecture bloquante jusqu'à la fin du son, jusqu'à l'arrêt demandé, ou
    tant que la pause n'est pas levée).

Dépend de :
    `sounddevice` (liaison PortAudio, portable Linux/Windows/macOS).
"""

import io
import threading
import wave

import sounddevice as sd

_LARGEUR_ECHANTILLON_GEREE = 2  # 16 bits — seul format produit par le serveur Piper
_TAILLE_BLOC_TRAMES = 4096


class ErreurLecture(RuntimeError):
    pass


def play_wav_bytes(
    wav_bytes: bytes,
    stop_event: threading.Event | None = None,
    pause_event: threading.Event | None = None,
) -> None:
    with wave.open(io.BytesIO(wav_bytes), "rb") as fichier_wav:
        canaux = fichier_wav.getnchannels()
        largeur = fichier_wav.getsampwidth()
        frequence = fichier_wav.getframerate()
        trames = fichier_wav.readframes(fichier_wav.getnframes())

    if largeur != _LARGEUR_ECHANTILLON_GEREE:
        raise ErreurLecture(
            f"Largeur d'échantillon non gérée : {largeur * 8} bits "
            f"(16 bits attendus)."
        )

    if stop_event is None and pause_event is None:
        with sd.RawOutputStream(
            samplerate=frequence, channels=canaux, dtype="int16"
        ) as flux:
            flux.write(trames)
        return

    taille_bloc_octets = _TAILLE_BLOC_TRAMES * largeur * canaux
    with sd.RawOutputStream(
        samplerate=frequence, channels=canaux, dtype="int16"
    ) as flux:
        for debut in range(0, len(trames), taille_bloc_octets):
            if pause_event is not None:
                pause_event.wait()
            if stop_event is not None and stop_event.is_set():
                return
            flux.write(trames[debut : debut + taille_bloc_octets])

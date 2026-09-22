"""
player.py — joue un WAV reçu du serveur de synthèse sur la sortie audio par défaut.

Pourquoi ce fichier existe :
    Le serveur renvoie un WAV complet en mémoire, jamais un fichier sur
    disque ; la lecture se fait donc directement depuis les octets reçus,
    sans écriture temporaire.

Entrée / sortie :
    Entrée : les octets d'un fichier WAV mono ou stéréo, 16 bits. Sortie :
    aucune (lecture bloquante jusqu'à la fin du son).

Dépend de :
    `sounddevice` (liaison PortAudio, portable Linux/Windows/macOS).
"""

import io
import wave

import sounddevice as sd

_LARGEUR_ECHANTILLON_GEREE = 2  # 16 bits — seul format produit par le serveur Piper


class ErreurLecture(RuntimeError):
    pass


def play_wav_bytes(wav_bytes: bytes) -> None:
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

    with sd.RawOutputStream(
        samplerate=frequence, channels=canaux, dtype="int16"
    ) as flux:
        flux.write(trames)

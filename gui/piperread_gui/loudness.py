"""
loudness.py — gain par voix qui ramène toutes les voix au même niveau perçu (clé `normalize`).

Pourquoi ce fichier existe :
    Piper normalise la crête de chaque phrase à 0 dBFS, mais deux voix de même
    crête n'ont pas le même niveau perçu. Le niveau (valeur efficace, en dBFS)
    d'une voix est mesuré une fois sur une phrase de référence, gardé dans le
    fichier que lit aussi `utils/normalize.sh`, puis converti en gain. Mêmes
    constantes que le noyau : une voix joue au même niveau dans les deux.

Entrée / sortie :
    Entrée : le chemin d'un modèle `.onnx` et une fonction qui synthétise un texte
    et rend les octets du WAV (le serveur HTTP déjà lancé par l'interface).
    Sortie : le coefficient à appliquer aux échantillons (`scale_pcm16`), au plus
    `MAX_GAIN` : la crête de Piper valant 0 dBFS, aucune crête ne dépasse −1 dBFS.

Dépend de :
    la bibliothèque standard seulement.
"""

import array
import io
import json
import math
import os
import sys
import tempfile
import wave
from pathlib import Path
from typing import Callable

TARGET_DB = -22.2
MAX_GAIN = 0.8913
REPEATS = 6

REFERENCE_TEXTS = {
    "fr": "Le vieux pont de pierre enjambe la rivière, et les enfants y jouent chaque soir jusqu'à la tombée de la nuit.",
    "en": "The old stone bridge crosses the river, and the children play there every evening until nightfall.",
    "de": "Die alte Steinbrücke führt über den Fluss, und die Kinder spielen dort jeden Abend bis zur Dämmerung.",
    "es": "El viejo puente de piedra cruza el río, y los niños juegan allí cada tarde hasta que cae la noche.",
}


def state_file() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "piperread" / "voice-levels"


def pcm16_energy(trames: bytes) -> tuple[float, int]:
    """Somme des carrés et nombre d'échantillons d'un flux 16 bits."""
    echantillons = array.array("h")
    echantillons.frombytes(trames)
    if sys.byteorder == "big":
        echantillons.byteswap()
    return float(sum(x * x for x in echantillons)), len(echantillons)


def wav_energy(wav_bytes: bytes) -> tuple[float, int]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as fichier:
        return pcm16_energy(fichier.readframes(fichier.getnframes()))


def level_db(energies: list[tuple[float, int]]) -> float | None:
    total = sum(somme for somme, _ in energies)
    nombre = sum(n for _, n in energies)
    if nombre == 0:
        return None
    return 10 * math.log10(max(total / nombre, 1e-12) / 32768.0**2)


def gain_for_level(level: float) -> float:
    return min(MAX_GAIN, 10 ** ((TARGET_DB - level) / 20))


def voice_language(model_path: Path) -> str:
    """Langue de la voix : champ « language », à défaut sa voix espeak ; l'anglais pour le reste."""
    try:
        config = json.loads(Path(f"{model_path}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        config = {}
    code = (config.get("language") or {}).get("code") or (config.get("espeak") or {}).get("voice") or ""
    base = code.replace("-", "_").split("_")[0]
    return base if base in REFERENCE_TEXTS else "en"


def _signature(model_path: Path) -> str:
    etat = model_path.stat()
    return f"{etat.st_size}\t{int(etat.st_mtime)}"


def _lire_niveau(fichier: Path, nom: str, signature: str) -> float | None:
    try:
        lignes = fichier.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for ligne in lignes:
        champs = ligne.split("\t")
        if len(champs) == 4 and champs[0] == nom and f"{champs[1]}\t{champs[2]}" == signature:
            try:
                return float(champs[3])
            except ValueError:
                return None
    return None


def _ecrire_niveau(fichier: Path, nom: str, signature: str, niveau: float) -> None:
    fichier.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        lignes = [l for l in fichier.read_text(encoding="utf-8").splitlines() if l.split("\t", 1)[0] != nom]
    except OSError:
        lignes = []
    lignes.append(f"{nom}\t{signature}\t{niveau:.2f}")
    descripteur, temporaire = tempfile.mkstemp(prefix="voice-levels.", dir=fichier.parent)
    with os.fdopen(descripteur, "w", encoding="utf-8") as sortie:
        sortie.write("\n".join(lignes) + "\n")
    os.replace(temporaire, fichier)


def voice_gain(model_path: Path, synthesize_wav: Callable[[str], bytes]) -> float:
    """Gain de la voix : lu dans le fichier de mesures si celui du fichier de voix est à jour, sinon mesuré et gardé."""
    model_path = Path(model_path)
    nom = model_path.name.removesuffix(".onnx")
    signature = _signature(model_path)
    fichier = state_file()
    niveau = _lire_niveau(fichier, nom, signature)
    if niveau is None:
        texte = REFERENCE_TEXTS[voice_language(model_path)]
        niveau = level_db([wav_energy(synthesize_wav(texte)) for _ in range(REPEATS)])
        if niveau is None:
            raise ValueError(f"Mesure impossible : flux vide pour {nom}.")
        _ecrire_niveau(fichier, nom, signature, niveau)
    return gain_for_level(niveau)


def scale_pcm16(trames: bytes, gain: float) -> bytes:
    """Multiplie les échantillons 16 bits par `gain` (au plus 1 : jamais d'écrêtage)."""
    if gain == 1.0:
        return trames
    echantillons = array.array("h")
    echantillons.frombytes(trames)
    if sys.byteorder == "big":
        echantillons.byteswap()
    mis_a_l_echelle = array.array("h", (max(-32768, min(32767, round(x * gain))) for x in echantillons))
    if sys.byteorder == "big":
        mis_a_l_echelle.byteswap()
    return mis_a_l_echelle.tobytes()

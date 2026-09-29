"""
voice_catalog.py — voix proposées par PiperRead, à l'identique de `utils/voices.sh`.

Pourquoi ce fichier existe :
    Le catalogue de Piper ne donne pas la licence de ses voix : PiperRead la
    note à la main, pour que l'utilisateur la connaisse avant de télécharger.
    Le noyau la porte dans `VOICE_CATALOG` (Bash) ; ce port Python évite qu'un
    des deux processus importe l'autre. Un test compare les deux tables ligne
    à ligne, pour qu'elles ne divergent pas.

Entrée / sortie :
    Entrée : un code de langue (`en`, `fr`, `de`, `es`). Sortie : les voix
    proposées (`Voix`), dont la recommandée de la langue.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Voix:
    nom: str
    langue: str
    taux: int
    taille_mo: int
    licence: str
    locuteurs: int
    rang: str


_TABLE = (
    ("en_US-ljspeech-medium", "en", 22050, 61, "public-domain", 1, "recommended"),
    ("en_US-kristin-medium", "en", 22050, 61, "public-domain", 1, "alternative"),
    ("en_GB-alba-medium", "en", 22050, 60, "CC-BY 4.0", 1, "alternative"),
    ("en_US-kathleen-low", "en", 16000, 60, "CC0", 1, "light"),
    ("fr_FR-siwis-medium", "fr", 22050, 60, "CC-BY 4.0", 1, "recommended"),
    ("fr_FR-siwis-low", "fr", 16000, 27, "CC-BY 4.0", 1, "light"),
    ("de_DE-thorsten-medium", "de", 22050, 60, "CC0", 1, "recommended"),
    ("de_DE-thorsten-low", "de", 16000, 60, "CC0", 1, "light"),
    ("es_ES-davefx-medium", "es", 22050, 60, "CC0", 1, "recommended"),
    ("es_ES-sharvard-medium", "es", 22050, 73, "CC-BY 3.0", 2, "alternative"),
    ("es_ES-carlfm-x_low", "es", 16000, 27, "public-domain", 1, "light"),
)

CATALOGUE = tuple(Voix(*ligne) for ligne in _TABLE)


def voix_recommandee(langue: str) -> Voix:
    """La voix que `--download-voice` propose sans nom ; l'anglais si la langue est inconnue."""
    for voix in CATALOGUE:
        if voix.langue == langue and voix.rang == "recommended":
            return voix
    return voix_recommandee("en")


def voix_par_nom(nom: str) -> Voix | None:
    return next((voix for voix in CATALOGUE if voix.nom == nom), None)

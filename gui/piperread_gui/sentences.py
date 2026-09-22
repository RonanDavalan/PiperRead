"""
sentences.py — découpe un texte en phrases avant envoi au moteur de synthèse.

Pourquoi ce fichier existe :
    Envoyer un texte entier en une seule requête retarde le premier son
    jusqu'à la synthèse complète ; découper par phrase permet de commencer à
    jouer pendant que la suite se synthétise, et prépare la pause et le
    déplacement phrase par phrase des sessions suivantes.

Entrée / sortie :
    Entrée : un texte brut et un code de langue (`en`, `fr`, `de`, `es` — les
    quatre langues déjà documentées du projet). Sortie : la liste des phrases,
    nettoyées des espaces de bord, sans élément vide.

Dépend de :
    `pysbd`, découpeur de phrases multilingue.
"""

import pysbd

_LANGUES_GEREES = ("en", "fr", "de", "es")


def split_sentences(text: str, lang: str) -> list[str]:
    if lang not in _LANGUES_GEREES:
        raise ValueError(
            f"Langue non gérée : {lang!r} (attendu : {', '.join(_LANGUES_GEREES)})"
        )
    segmenter = pysbd.Segmenter(language=lang, clean=False)
    return [s.strip() for s in segmenter.segment(text) if s.strip()]

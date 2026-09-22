"""
cleaner.py — retire le balisage Markdown d'un texte avant sa lecture à voix haute.

Pourquoi ce fichier existe :
    Le moteur vocal prononcerait les symboles (dièses, astérisques, crochets) :
    `**test**` serait lu « asterisk, asterisk, test… ». Le noyau les retire
    déjà par `clean_markdown` (`utils/cleaner.sh`) ; ce module applique les
    mêmes expressions, dans le même ordre, réécrites avec `re` plutôt
    qu'appelées en sous-processus `sed`, pour que l'interface n'ait besoin
    d'aucun interpréteur Bash, y compris sous Windows.

Entrée / sortie :
    Entrée : le texte brut capturé. Sortie : le même texte sans balisage.

Dépend de :
    Rien d'autre que la bibliothèque standard. `sed` traite chaque ligne
    séparément : le texte est donc découpé en lignes avant les
    substitutions, pour que `^`, `$` et les classes niées ne franchissent
    jamais un saut de ligne, exactement comme dans `clean_markdown`.
"""

import re

# Traduction des classes POSIX de cleaner.sh : [^[:alnum:]*] devient
# (?:[^\w*]|_), puisque \w compte le soulignement parmi les alphanumériques.
_HORS_MOT_ETOILE = r"(?:[^\w*]|_)"
_HORS_MOT = r"\W"

_EMPHASES = (
    re.compile(rf"(^|{_HORS_MOT_ETOILE})\*\*([^*\s]([^*]*[^*\s])?)\*\*({_HORS_MOT_ETOILE}|$)"),
    re.compile(rf"(^|{_HORS_MOT_ETOILE})\*([^*\s]([^*]*[^*\s])?)\*({_HORS_MOT_ETOILE}|$)"),
    re.compile(rf"(^|{_HORS_MOT})__([^_\s]([^_]*[^_\s])?)__({_HORS_MOT}|$)"),
    re.compile(rf"(^|{_HORS_MOT})_([^_\s]([^_]*[^_\s])?)_({_HORS_MOT}|$)"),
)

_AVANT_EMPHASES = (
    (re.compile(r"!\[.*\]\(.*\)"), ""),
    (re.compile(r"\[(.*)\]\(.*\)"), r"\1"),
    (re.compile(r"`"), ""),
)

# Deux passes sur les emphases, comme cleaner.sh : un marqueur fermant consommé
# par une correspondance ne peut pas ouvrir la suivante dans la même passe.
_SUBSTITUTIONS = (
    *_AVANT_EMPHASES,
    *((motif, r"\1\2\4") for motif in _EMPHASES),
    *((motif, r"\1\2\4") for motif in _EMPHASES),
    (re.compile(r"^#+ "), ""),
    (re.compile(r"^\s*[-*+]\s"), ""),
    (re.compile(r"^>\s?"), ""),
)


def _clean_line(ligne: str) -> str:
    for motif, remplacement in _SUBSTITUTIONS:
        ligne = motif.sub(remplacement, ligne)
    return ligne


def clean_markdown(texte: str) -> str:
    return "\n".join(_clean_line(ligne) for ligne in texte.split("\n"))

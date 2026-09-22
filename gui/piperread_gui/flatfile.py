"""
flatfile.py — lit un fichier « clé=valeur » sans jamais exécuter son contenu.

Pourquoi ce fichier existe :
    Port Python de `utils/flatfile.sh` : la configuration et les messages sont
    des fichiers édités par l'utilisateur, partagés avec le noyau. Le même
    format et la même règle de clé (`^[a-z][a-z_]*$`) doivent produire le même
    résultat des deux côtés, sans jamais passer par `exec`/`eval`.

Entrée / sortie :
    Entrée : le chemin d'un fichier plat. Sortie : un dictionnaire clé/valeur ;
    les lignes vides, celles qui commencent par `#` et celles dont la clé
    n'est pas en minuscules et tirets bas sont ignorées. Un fichier absent ou
    illisible rend un dictionnaire vide.
"""

import re
from pathlib import Path

_CLE_VALIDE = re.compile(r"[a-z][a-z_]*")


def read_flat_file(path: Path) -> dict[str, str]:
    valeurs: dict[str, str] = {}
    try:
        texte = path.read_text(encoding="utf-8")
    except OSError:
        return valeurs

    for ligne in texte.splitlines():
        if "=" in ligne:
            cle, valeur = ligne.split("=", 1)
        else:
            cle, valeur = ligne, ""
        if not _CLE_VALIDE.fullmatch(cle):
            continue
        valeurs[cle] = valeur

    return valeurs

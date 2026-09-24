import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from piperread_gui.cleaner import clean_markdown

CLEANER_SH = Path(__file__).resolve().parents[2] / "utils" / "cleaner.sh"


@pytest.mark.parametrize(
    "brut, attendu",
    [
        ("**test** test", "test test"),
        ("*test* test", "test test"),
        ("__gras__ et _italique_", "gras et italique"),
        ("Émile **Zola** écrit _Germinal_.", "Émile Zola écrit Germinal."),
        ("# Titre\n## Sous-titre", "Titre\nSous-titre"),
        ("- un\n* deux\n+ trois", "un\ndeux\ntrois"),
        ("> citation", "citation"),
        ("Voir [le site](https://exemple.fr).", "Voir le site."),
        ("Image ![logo](logo.png) ici", "Image  ici"),
        ("`code` en ligne", "code en ligne"),
        ("avant\n---\naprès", "avant\n\naprès"),
        ("  * * *", ""),
        ("_____", ""),
        ("- - -\r", ""),
    ],
)
def test_retire_le_balisage(brut, attendu):
    assert clean_markdown(brut) == attendu


@pytest.mark.parametrize(
    "texte",
    ["ma_variable vaut 2*3", "snake_case_name", "2 * 3 * 4", "x**2** et **2**x"],
)
def test_identifiants_et_operations_intacts(texte):
    assert clean_markdown(texte) == texte


def test_les_lignes_sont_traitees_separement():
    assert clean_markdown("*début\nfin*") == "*début\nfin*"


CORPUS = [
    "**test** test",
    "*un* **deux** _trois_ __quatre__",
    "ma_variable vaut 2*3 et __init__.py",
    "# Titre\n- item\n> citation\n  * indenté",
    "Voir [le site](https://exemple.fr) et ![img](a.png)",
    "***triple*** _**mixte**_ **a** **b**",
    "éléphant **été** à_b_c, **mot**, fin.",
    "texte\r\n**windows**\r\n",
    "* * *\n**pas fermé\n#Pas de titre",
    "Titre\n---\n\n***\n___\n- - -\n    ----\na -- b\nfin ---\n-*-",
]


@pytest.mark.skipif(
    sys.platform == "win32" or shutil.which("bash") is None or not CLEANER_SH.is_file(),
    reason="référence Bash disponible seulement dans le clone, sous Linux",
)
@pytest.mark.parametrize("texte", CORPUS)
def test_meme_sortie_que_clean_markdown_du_noyau(texte):
    resultat = subprocess.run(
        ["bash", "-c", 'source "$1"; clean_markdown "$2"', "_", str(CLEANER_SH), texte],
        capture_output=True,
        check=True,
        env={**os.environ, "LC_ALL": "C.UTF-8"},
    )
    reference = resultat.stdout.decode("utf-8").removesuffix("\n")
    assert clean_markdown(texte) == reference

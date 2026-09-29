import re
from pathlib import Path

import pytest

from piperread_gui import voice_catalog

_VOICES_SH = Path(__file__).resolve().parents[2] / "utils" / "voices.sh"


def _table_du_noyau() -> list[tuple]:
    lignes = re.findall(r'^\s+"([^"]+\|[^"]*)"$', _VOICES_SH.read_text(encoding="utf-8"), re.MULTILINE)
    table = []
    for ligne in lignes:
        nom, langue, taux, taille, licence, locuteurs, rang, _remarque = ligne.split("|")
        table.append((nom, langue, int(taux), int(taille), licence, int(locuteurs), rang))
    return table


def test_meme_table_que_le_noyau():
    noyau = _table_du_noyau()
    assert len(noyau) == 11
    assert [tuple(vars(voix).values()) for voix in voice_catalog.CATALOGUE] == noyau


@pytest.mark.parametrize("langue", ["en", "fr", "de", "es"])
def test_une_seule_voix_recommandee_par_langue(langue):
    recommandees = [v for v in voice_catalog.CATALOGUE if v.langue == langue and v.rang == "recommended"]
    assert len(recommandees) == 1
    assert voice_catalog.voix_recommandee(langue) == recommandees[0]


def test_langue_inconnue_retombe_sur_l_anglais():
    assert voice_catalog.voix_recommandee("it").nom == "en_US-ljspeech-medium"


def test_voix_par_nom():
    assert voice_catalog.voix_par_nom("fr_FR-siwis-medium").taille_mo == 60
    assert voice_catalog.voix_par_nom("inconnue") is None

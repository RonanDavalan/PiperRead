import pytest

from piperread_gui.sentences import split_sentences


def test_decoupe_trois_phrases_francaises():
    texte = "Bonjour Ronan. Voici un test en deux phrases ! Et une question ?"
    assert split_sentences(texte, "fr") == [
        "Bonjour Ronan.",
        "Voici un test en deux phrases !",
        "Et une question ?",
    ]


def test_ignore_les_fragments_vides():
    texte = "Une phrase.   \n\n   Une autre."
    resultat = split_sentences(texte, "fr")
    assert "" not in resultat
    assert all(phrase.strip() == phrase for phrase in resultat)


def test_ignore_les_segments_sans_lettre_ni_chiffre():
    texte = "Une phrase.\n\n—\n\n…\n\n→ | --\n\nUne autre."
    assert split_sentences(texte, "fr") == ["Une phrase.", "Une autre."]


def test_garde_un_segment_fait_d_un_seul_chiffre():
    assert split_sentences("Étape\n\n3", "fr") == ["Étape", "3"]


def test_langue_non_geree_leve():
    with pytest.raises(ValueError):
        split_sentences("Hola.", "it")


@pytest.mark.parametrize("lang", ["en", "de", "es"])
def test_langues_documentees_fonctionnent(lang):
    assert split_sentences("One. Two.", lang)

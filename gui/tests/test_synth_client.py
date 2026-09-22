import pytest
import requests

from piperread_gui import synth_client


class _ReponseFactice:
    def __init__(self, status_code=200, content=b"RIFF....WAVEfmt ", text=""):
        self.status_code = status_code
        self.content = content
        self.text = text


def test_texte_vide_leve_avant_requete(monkeypatch):
    def echoue(*_a, **_kw):
        raise AssertionError("aucune requête ne doit partir pour un texte vide")

    monkeypatch.setattr(synth_client.requests, "post", echoue)

    with pytest.raises(ValueError):
        synth_client.synthesize("http://127.0.0.1:5000", "   ")


def test_retourne_les_octets_audio(monkeypatch):
    monkeypatch.setattr(
        synth_client.requests, "post", lambda *_a, **_kw: _ReponseFactice()
    )
    assert synth_client.synthesize("http://127.0.0.1:5000", "Bonjour.") == b"RIFF....WAVEfmt "


def test_statut_non_200_leve(monkeypatch):
    monkeypatch.setattr(
        synth_client.requests,
        "post",
        lambda *_a, **_kw: _ReponseFactice(status_code=500, text="erreur serveur"),
    )
    with pytest.raises(synth_client.ErreurSynthese, match="500"):
        synth_client.synthesize("http://127.0.0.1:5000", "Bonjour.")


def test_reponse_vide_leve(monkeypatch):
    monkeypatch.setattr(
        synth_client.requests, "post", lambda *_a, **_kw: _ReponseFactice(content=b"")
    )
    with pytest.raises(synth_client.ErreurSynthese):
        synth_client.synthesize("http://127.0.0.1:5000", "Bonjour.")


def test_length_scale_transmis_si_fourni(monkeypatch):
    corps_captes = {}

    def post_capte(url, json, timeout):
        corps_captes.update(json)
        return _ReponseFactice()

    monkeypatch.setattr(synth_client.requests, "post", post_capte)
    synth_client.synthesize("http://127.0.0.1:5000", "Bonjour.", length_scale=0.8)

    assert corps_captes == {"text": "Bonjour.", "length_scale": 0.8}


def test_length_scale_absent_si_non_fourni(monkeypatch):
    corps_captes = {}

    def post_capte(url, json, timeout):
        corps_captes.update(json)
        return _ReponseFactice()

    monkeypatch.setattr(synth_client.requests, "post", post_capte)
    synth_client.synthesize("http://127.0.0.1:5000", "Bonjour.")

    assert corps_captes == {"text": "Bonjour."}


def test_erreur_reseau_convertie(monkeypatch):
    def leve(*_a, **_kw):
        raise requests.ConnectionError("refus de connexion")

    monkeypatch.setattr(synth_client.requests, "post", leve)

    with pytest.raises(synth_client.ErreurSynthese, match="refus de connexion"):
        synth_client.synthesize("http://127.0.0.1:5000", "Bonjour.")

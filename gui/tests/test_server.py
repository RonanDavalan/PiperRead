import io
import socket

import pytest

from piperread_gui import server


def test_port_libre_rebindable():
    port = server._port_libre("127.0.0.1")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as verif:
        verif.bind(("127.0.0.1", port))


def test_trouver_interprete_prefere_le_clone(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_REPO_ROOT", tmp_path)
    interprete_clone = tmp_path / "piper-env" / "bin" / "python3"
    interprete_clone.parent.mkdir(parents=True)
    interprete_clone.touch()

    assert server._trouver_interprete() == interprete_clone


def test_trouver_interprete_repli_paquet(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_REPO_ROOT", tmp_path)
    interprete_paquet = tmp_path / "venv-paquet" / "bin" / "python3"
    interprete_paquet.parent.mkdir(parents=True)
    interprete_paquet.touch()
    monkeypatch.setattr(server, "_VENV_PAQUET", tmp_path / "venv-paquet")

    assert server._trouver_interprete() == interprete_paquet


def test_trouver_interprete_absent_leve(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_REPO_ROOT", tmp_path)
    monkeypatch.setattr(server, "_VENV_PAQUET", tmp_path / "introuvable")

    with pytest.raises(server.ErreurServeurPiper, match="piper-tts\\[http\\]"):
        server._trouver_interprete()


def test_modele_absent_leve(tmp_path):
    with pytest.raises(server.ErreurServeurPiper):
        server.PiperHttpServer(tmp_path / "aucun-modele.onnx")


class _ProcessusFactice:
    def __init__(self, sorti_immediatement: bool):
        self._sorti_immediatement = sorti_immediatement
        self.termine = False
        self.tue = False
        self.stdout = io.StringIO("")
        self.stderr = io.StringIO("message d'erreur du serveur")

    def poll(self):
        return 1 if self._sorti_immediatement else None

    def terminate(self):
        self.termine = True

    def kill(self):
        self.tue = True

    def wait(self, timeout=None):
        return 0


def test_start_leve_si_le_processus_sort_immediatement(tmp_path, monkeypatch):
    modele = tmp_path / "voix.onnx"
    modele.touch()
    serveur = server.PiperHttpServer(modele)

    monkeypatch.setattr(server, "_trouver_interprete", lambda: tmp_path / "python3")
    monkeypatch.setattr(
        server.subprocess,
        "Popen",
        lambda *_a, **_kw: _ProcessusFactice(sorti_immediatement=True),
    )

    with pytest.raises(server.ErreurServeurPiper, match="message d'erreur du serveur"):
        serveur.start()


def test_start_attend_hote_local(tmp_path, monkeypatch):
    modele = tmp_path / "voix.onnx"
    modele.touch()
    serveur = server.PiperHttpServer(modele)

    monkeypatch.setattr(server, "_trouver_interprete", lambda: tmp_path / "python3")

    arguments_captures = {}

    def faux_popen(commande, **_kwargs):
        arguments_captures["commande"] = commande
        return _ProcessusFactice(sorti_immediatement=False)

    monkeypatch.setattr(server.subprocess, "Popen", faux_popen)
    monkeypatch.setattr(server.urllib.request, "urlopen", lambda *_a, **_kw: io.BytesIO(b"{}"))

    serveur.start()
    try:
        commande = arguments_captures["commande"]
        assert "--host" in commande
        assert commande[commande.index("--host") + 1] == "127.0.0.1"
        assert serveur.base_url == f"http://127.0.0.1:{serveur.port}"
    finally:
        serveur.stop()

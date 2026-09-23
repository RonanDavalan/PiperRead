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


def test_trouver_executable_windows_dans_son_sous_dossier(tmp_path, monkeypatch):
    monkeypatch.setattr(server.sys, "executable", str(tmp_path / "piperread-gui.exe"))
    executable = tmp_path / "piper-http-server" / server._NOM_EXECUTABLE_WINDOWS
    executable.parent.mkdir()
    executable.touch()

    assert server._trouver_executable_windows() == executable


def test_trouver_executable_windows_ignore_l_ancien_emplacement(tmp_path, monkeypatch):
    monkeypatch.setattr(server.sys, "executable", str(tmp_path / "piperread-gui.exe"))
    (tmp_path / server._NOM_EXECUTABLE_WINDOWS).touch()

    with pytest.raises(server.ErreurServeurPiper, match="piper-http-server"):
        server._trouver_executable_windows()


def test_trouver_executable_windows_absent_leve(tmp_path, monkeypatch):
    monkeypatch.setattr(server.sys, "executable", str(tmp_path / "piperread-gui.exe"))

    with pytest.raises(server.ErreurServeurPiper, match="piper-http-server.exe"):
        server._trouver_executable_windows()


def test_commande_serveur_windows_invoque_lexecutable_directement(tmp_path, monkeypatch):
    monkeypatch.setattr(server.sys, "platform", "win32")
    monkeypatch.setattr(server.sys, "executable", str(tmp_path / "piperread-gui.exe"))
    executable = tmp_path / "piper-http-server" / server._NOM_EXECUTABLE_WINDOWS
    executable.parent.mkdir()
    executable.touch()
    modele = tmp_path / "voix.onnx"

    commande = server._commande_serveur(5000, modele)

    assert commande[0] == str(executable)
    assert "-m" not in commande
    assert commande[commande.index("--port") + 1] == "5000"


def test_commande_serveur_posix_execute_le_point_d_entree(tmp_path, monkeypatch):
    monkeypatch.setattr(server.sys, "platform", "linux")
    monkeypatch.setattr(server, "_trouver_interprete", lambda: tmp_path / "python3")
    modele = tmp_path / "voix.onnx"

    commande = server._commande_serveur(5000, modele)

    assert commande[0] == str(tmp_path / "python3")
    assert commande[1] == str(server._POINT_D_ENTREE)
    assert server._POINT_D_ENTREE.is_file()
    assert "-m" not in commande


def test_modele_absent_leve(tmp_path):
    with pytest.raises(server.ErreurServeurPiper):
        server.PiperHttpServer(tmp_path / "aucun-modele.onnx")


class _ProcessusFactice:
    def __init__(self, sorti_immediatement: bool, stderr: str = "message d'erreur du serveur"):
        self._sorti_immediatement = sorti_immediatement
        self.termine = False
        self.tue = False
        self.stdout = None
        self.stderr = io.StringIO(stderr)

    def poll(self):
        return 1 if (self._sorti_immediatement or self.termine) else None

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


def test_start_garde_seulement_les_dernieres_lignes_d_erreur(tmp_path, monkeypatch):
    modele = tmp_path / "voix.onnx"
    modele.touch()
    serveur = server.PiperHttpServer(modele)
    lignes = "".join(f"ligne {n}\n" for n in range(500))

    monkeypatch.setattr(server, "_trouver_interprete", lambda: tmp_path / "python3")
    monkeypatch.setattr(
        server.subprocess,
        "Popen",
        lambda *_a, **_kw: _ProcessusFactice(sorti_immediatement=True, stderr=lignes),
    )

    with pytest.raises(server.ErreurServeurPiper) as erreur:
        serveur.start()

    assert "ligne 499" in str(erreur.value)
    assert "ligne 400" not in str(erreur.value)


def test_start_transmet_le_pid_de_l_interface_et_ne_garde_aucun_tube_de_sortie(tmp_path, monkeypatch):
    modele = tmp_path / "voix.onnx"
    modele.touch()
    serveur = server.PiperHttpServer(modele)
    monkeypatch.setattr(server, "_trouver_interprete", lambda: tmp_path / "python3")
    captures = {}

    def faux_popen(commande, **kwargs):
        captures.update(kwargs)
        return _ProcessusFactice(sorti_immediatement=False, stderr="")

    monkeypatch.setattr(server.subprocess, "Popen", faux_popen)
    monkeypatch.setattr(server.urllib.request, "urlopen", lambda *_a, **_kw: io.BytesIO(b"{}"))

    serveur.start()
    try:
        assert captures["env"]["PIPERREAD_PARENT_PID"] == str(server.os.getpid())
        assert captures["stdout"] == server.subprocess.DEVNULL
        assert serveur.est_actif
    finally:
        serveur.stop()
    assert not serveur.est_actif

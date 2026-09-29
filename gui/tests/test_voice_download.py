import sys
import textwrap

import pytest

from piperread_gui import voice_download
from piperread_gui.voice_download import ErreurTelechargement, Telechargement

_SCRIPT_REUSSI = textwrap.dedent(
    """
    import sys
    dossier, nom = sys.argv[1], sys.argv[2]
    open(f"{dossier}/{nom}.onnx", "wb").write(b"modele")
    open(f"{dossier}/{nom}.onnx.json", "w").write("{}")
    """
)


def _commande_de_script(monkeypatch, corps: str, tmp_path):
    script = tmp_path / "faux_moteur.py"
    script.write_text(corps, encoding="utf-8")
    monkeypatch.setattr(
        voice_download, "_commande", lambda dossier, nom: [sys.executable, str(script), str(dossier), nom]
    )


def test_voix_posee_dans_le_dossier_sans_reste(monkeypatch, tmp_path):
    _commande_de_script(monkeypatch, _SCRIPT_REUSSI, tmp_path)
    voix = tmp_path / "voix"

    modele = Telechargement("fr_FR-siwis-medium", voix).executer()

    assert modele == voix / "fr_FR-siwis-medium.onnx"
    assert modele.read_bytes() == b"modele"
    assert (voix / "fr_FR-siwis-medium.onnx.json").is_file()
    assert sorted(p.name for p in voix.iterdir()) == ["fr_FR-siwis-medium.onnx", "fr_FR-siwis-medium.onnx.json"]


def test_echec_ne_laisse_rien_dans_le_dossier(monkeypatch, tmp_path):
    corps = "import sys\nopen(sys.argv[1] + '/x.onnx', 'wb').write(b'tronque')\nsys.stderr.write('reseau coupe\\n')\nsys.exit(1)\n"
    _commande_de_script(monkeypatch, corps, tmp_path)
    voix = tmp_path / "voix"

    with pytest.raises(ErreurTelechargement, match="reseau coupe"):
        Telechargement("x", voix).executer()

    assert list(voix.iterdir()) == []


def test_fichier_vide_refuse_meme_avec_code_zero(monkeypatch, tmp_path):
    corps = "import sys\nopen(sys.argv[1] + '/x.onnx', 'wb').close()\nopen(sys.argv[1] + '/x.onnx.json', 'w').write('{}')\n"
    _commande_de_script(monkeypatch, corps, tmp_path)
    voix = tmp_path / "voix"

    with pytest.raises(ErreurTelechargement):
        Telechargement("x", voix).executer()

    assert list(voix.iterdir()) == []


def test_nom_invalide_refuse_avant_tout_processus(tmp_path):
    with pytest.raises(ErreurTelechargement):
        Telechargement("../evil", tmp_path)


def test_annulation_tue_le_processus_et_ne_pose_rien(monkeypatch, tmp_path):
    _commande_de_script(monkeypatch, "import time\ntime.sleep(60)\n", tmp_path)
    voix = tmp_path / "voix"
    telechargement = Telechargement("x", voix)

    import threading
    import time

    resultat = []
    fil = threading.Thread(target=lambda: resultat.append(_executer(telechargement)))
    fil.start()
    time.sleep(0.5)
    telechargement.annuler()
    fil.join(timeout=10)

    assert not fil.is_alive()
    assert isinstance(resultat[0], ErreurTelechargement)
    assert list(voix.iterdir()) == []


def _executer(telechargement):
    try:
        return telechargement.executer()
    except ErreurTelechargement as erreur:
        return erreur


def test_commande_linux_passe_par_l_entree_du_moteur(monkeypatch, tmp_path):
    monkeypatch.setattr(voice_download.sys, "platform", "linux")
    monkeypatch.setattr(voice_download.server, "_trouver_interprete", lambda: tmp_path / "python3")

    commande = voice_download._commande(tmp_path / "tmp", "fr_FR-siwis-medium")

    assert commande[0] == str(tmp_path / "python3")
    assert commande[1].endswith("piper_server_entry.py")
    assert commande[2:] == ["download-voices", "--download-dir", str(tmp_path / "tmp"), "fr_FR-siwis-medium"]


def test_commande_windows_passe_par_l_executable_gele(monkeypatch, tmp_path):
    monkeypatch.setattr(voice_download.sys, "platform", "win32")
    monkeypatch.setattr(voice_download.server, "_trouver_executable_windows", lambda: tmp_path / "piper-http-server.exe")

    commande = voice_download._commande(tmp_path / "tmp", "x")

    assert commande == [
        str(tmp_path / "piper-http-server.exe"),
        "download-voices",
        "--download-dir",
        str(tmp_path / "tmp"),
        "x",
    ]

from piperread_gui import frozen


def test_installation_dir_none_hors_gel():
    assert frozen.installation_dir() is None


def test_installation_dir_dossier_de_lexecutable_gele(monkeypatch, tmp_path):
    monkeypatch.setattr(frozen.sys, "frozen", True, raising=False)
    monkeypatch.setattr(frozen.sys, "executable", str(tmp_path / "piperread-gui.exe"))

    assert frozen.installation_dir() == tmp_path

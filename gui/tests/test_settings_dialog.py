import pytest
from PySide6.QtWidgets import QApplication

from piperread_gui import config
from piperread_gui.controller import PlaybackController
from piperread_gui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _config_isole(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for cle in ("PIPERREAD_SPEED", "PIPERREAD_VOICE", "PIPERREAD_LANG"):
        monkeypatch.delenv(cle, raising=False)


def _voix(tmp_path, *noms):
    dossier = tmp_path / "voices"
    dossier.mkdir(exist_ok=True)
    for nom in noms:
        (dossier / f"{nom}.onnx").touch()
    return dossier


def test_dialogue_pre_rempli_avec_les_reglages_actuels(application, tmp_path):
    voices_dir = _voix(tmp_path, "alpha", "beta")
    controleur = PlaybackController(voices_dir / "beta.onnx", "fr", speed=1.75)

    dialogue = SettingsDialog(controleur)

    assert dialogue._voix.currentText() == "beta"
    assert dialogue._vitesse.value() == pytest.approx(1.75)
    assert dialogue._langue.currentData() == "fr"


def test_aucune_voix_desactive_le_champ(application, tmp_path):
    voices_dir = _voix(tmp_path, "seule")
    controleur = PlaybackController(voices_dir / "seule.onnx", "fr")
    (voices_dir / "seule.onnx").unlink()

    dialogue = SettingsDialog(controleur)

    assert not dialogue._voix.isEnabled()


def test_enregistrer_ecrit_le_fichier_et_met_a_jour_le_controleur(application, tmp_path):
    voices_dir = _voix(tmp_path, "alpha", "beta")
    controleur = PlaybackController(voices_dir / "alpha.onnx", "fr", speed=1.0)

    dialogue = SettingsDialog(controleur)
    dialogue._voix.setCurrentText("beta")
    dialogue._vitesse.setValue(2.0)
    dialogue._langue.setCurrentIndex(dialogue._langue.findData("en"))

    dialogue._enregistrer()

    valeurs, _ = config.load_config_file()
    assert valeurs == {"speed": "2.00", "voice": "beta", "lang": "en"}

    assert controleur.model_path == voices_dir / "beta.onnx"
    assert controleur.lang == "en"
    assert controleur.speed == pytest.approx(2.0)


def test_voix_des_deux_dossiers_proposees_et_appliquees(application, tmp_path):
    clone = tmp_path / "clone"
    clone.mkdir()
    (clone / "fr_FR-siwis-medium.onnx").touch()
    utilisateur = tmp_path / "utilisateur"
    utilisateur.mkdir()
    (utilisateur / "fr_FR-gilles-low.onnx").touch()
    (utilisateur / "fr_FR-siwis-medium.onnx").touch()
    controleur = PlaybackController(clone / "fr_FR-siwis-medium.onnx", "fr", speed=1.0)

    dialogue = SettingsDialog(controleur, voices_dirs=[clone, utilisateur])

    noms = [dialogue._voix.itemText(i) for i in range(dialogue._voix.count())]
    assert noms == ["fr_FR-gilles-low", "fr_FR-siwis-medium"]
    assert dialogue._voix.currentText() == "fr_FR-siwis-medium"

    dialogue._voix.setCurrentText("fr_FR-gilles-low")
    dialogue._enregistrer()
    assert controleur.model_path == utilisateur / "fr_FR-gilles-low.onnx"


def test_annuler_ne_modifie_rien(application, tmp_path):
    voices_dir = _voix(tmp_path, "alpha")
    controleur = PlaybackController(voices_dir / "alpha.onnx", "fr", speed=1.0)

    dialogue = SettingsDialog(controleur)
    dialogue._vitesse.setValue(2.5)
    dialogue.reject()

    assert not config.config_file_path().exists()
    assert controleur.speed == 1.0


def test_case_de_lancement_automatique_reflete_et_modifie_l_etat(application, tmp_path, monkeypatch):
    from piperread_gui import autostart

    etat = {"actif": True, "appels": []}
    monkeypatch.setattr(autostart, "est_active", lambda: etat["actif"])
    monkeypatch.setattr(autostart, "activer", lambda icone=None: etat["appels"].append(("activer", icone)))
    monkeypatch.setattr(autostart, "desactiver", lambda: etat["appels"].append(("desactiver",)))
    voices_dir = _voix(tmp_path, "alpha")
    controleur = PlaybackController(voices_dir / "alpha.onnx", "fr")

    dialogue = SettingsDialog(controleur, tmp_path / "icone.svg")
    assert dialogue._lancement_auto.isChecked()
    dialogue._enregistrer()
    assert etat["appels"] == []

    dialogue = SettingsDialog(controleur, tmp_path / "icone.svg")
    dialogue._lancement_auto.setChecked(False)
    dialogue._enregistrer()
    assert etat["appels"] == [("desactiver",)]

    etat["actif"] = False
    dialogue = SettingsDialog(controleur, tmp_path / "icone.svg")
    dialogue._lancement_auto.setChecked(True)
    dialogue._enregistrer()
    assert etat["appels"][-1] == ("activer", tmp_path / "icone.svg")

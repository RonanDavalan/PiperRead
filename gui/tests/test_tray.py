import pytest
from PySide6.QtWidgets import QApplication

from piperread_gui.controller import Etat, PlaybackController
from piperread_gui.tray import MESSAGE_TRAY_ABSENT, PiperReadTray, avertir_si_tray_absent


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


def test_menu_reflete_l_etat(application, tmp_path):
    icone = tmp_path / "icone.svg"
    icone.write_text("<svg></svg>")
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    tray = PiperReadTray(controleur, icone)

    assert tray._action_lire.isEnabled()
    assert not tray._action_pause.isEnabled()
    assert not tray._action_reprendre.isEnabled()
    assert not tray._action_arreter.isEnabled()
    assert not tray._action_precedente.isEnabled()
    assert not tray._action_suivante.isEnabled()

    controleur.etat_change.emit(Etat.LECTURE)
    assert not tray._action_lire.isEnabled()
    assert tray._action_pause.isEnabled()
    assert tray._action_arreter.isEnabled()
    assert tray._action_suivante.isEnabled()

    controleur.etat_change.emit(Etat.PAUSE)
    assert tray._action_reprendre.isEnabled()
    assert not tray._action_pause.isEnabled()


def test_avertir_si_tray_absent_notifie_une_fois(application, monkeypatch):
    appels = []
    monkeypatch.setattr(
        "piperread_gui.tray.notifier", lambda titre, message: appels.append((titre, message))
    )
    monkeypatch.setattr(
        "piperread_gui.tray.QSystemTrayIcon.isSystemTrayAvailable",
        staticmethod(lambda: False),
    )

    assert avertir_si_tray_absent() is False
    assert appels == [("PiperRead", MESSAGE_TRAY_ABSENT)]


def test_avertir_si_tray_present_ne_notifie_pas(application, monkeypatch):
    appels = []
    monkeypatch.setattr(
        "piperread_gui.tray.notifier", lambda titre, message: appels.append((titre, message))
    )
    monkeypatch.setattr(
        "piperread_gui.tray.QSystemTrayIcon.isSystemTrayAvailable",
        staticmethod(lambda: True),
    )

    assert avertir_si_tray_absent() is True
    assert appels == []

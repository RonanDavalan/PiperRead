import pytest
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from piperread_gui.controller import Etat, PlaybackController
from piperread_gui.i18n import load_messages, msg
from piperread_gui.tray import PiperReadTray, avertir_si_tray_absent


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
    assert not tray._action_arreter.isEnabled()
    assert not tray._action_precedente.isEnabled()
    assert not tray._action_suivante.isEnabled()

    controleur.etat_change.emit(Etat.LECTURE)
    assert not tray._action_lire.isEnabled()
    assert tray._action_pause.isEnabled()
    assert tray._action_arreter.isEnabled()
    assert tray._action_suivante.isEnabled()

    controleur.etat_change.emit(Etat.PAUSE)
    assert tray._action_lire.isEnabled()
    assert not tray._action_pause.isEnabled()


def test_menu_libelles_dans_la_langue_du_controleur(application, tmp_path):
    icone = tmp_path / "icone.svg"
    icone.write_text("<svg></svg>")
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    tray = PiperReadTray(controleur, icone)

    assert tray._action_lire.text() == "Lire"
    assert tray._action_pause.text() == "Pause"
    assert tray._action_arreter.text() == "Arrêter"
    assert tray._action_precedente.text() == "Phrase précédente"
    assert tray._action_suivante.text() == "Phrase suivante"
    assert tray._action_reglages.text() == "Réglages…"
    assert tray._action_quitter.text() == "Quitter"
    assert tray._action_reglages.isEnabled()


def test_menu_sans_entree_reprendre(application, tmp_path):
    icone = tmp_path / "icone.svg"
    icone.write_text("<svg></svg>")
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    tray = PiperReadTray(controleur, icone)

    libelles = [action.text() for action in tray.contextMenu().actions() if not action.isSeparator()]
    assert libelles == [
        "Lire",
        "Pause",
        "Arrêter",
        "Phrase précédente",
        "Phrase suivante",
        "Réglages…",
        "Quitter",
    ]


class _ControleurEspion(PlaybackController):
    def __init__(self):
        super().__init__(model_path="modele.onnx", lang="fr")
        self.appels = []

    def lire(self):
        self.appels.append("lire")

    def pause(self):
        self.appels.append("pause")


@pytest.mark.parametrize(
    "etat, attendu",
    [(Etat.ARRET, ["lire"]), (Etat.LECTURE, ["pause"]), (Etat.PAUSE, ["lire"])],
)
def test_clic_gauche_suit_l_etat(application, tmp_path, etat, attendu):
    icone = tmp_path / "icone.svg"
    icone.write_text("<svg></svg>")
    controleur = _ControleurEspion()
    tray = PiperReadTray(controleur, icone)
    controleur._etat = etat

    tray.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)

    assert controleur.appels == attendu


@pytest.mark.parametrize(
    "raison",
    [
        QSystemTrayIcon.ActivationReason.Context,
        QSystemTrayIcon.ActivationReason.DoubleClick,
        QSystemTrayIcon.ActivationReason.MiddleClick,
    ],
)
def test_autres_activations_sans_effet(application, tmp_path, raison):
    icone = tmp_path / "icone.svg"
    icone.write_text("<svg></svg>")
    controleur = _ControleurEspion()
    tray = PiperReadTray(controleur, icone)

    tray.activated.emit(raison)

    assert controleur.appels == []


def test_clic_gauche_en_pause_reprend_sans_recommencer(application, tmp_path):
    icone = tmp_path / "icone.svg"
    icone.write_text("<svg></svg>")
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    tray = PiperReadTray(controleur, icone)
    controleur._phrases = ["une.", "deux.", "trois."]
    controleur._index = 2
    controleur._definir_etat(Etat.LECTURE)

    tray.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
    assert controleur.etat == Etat.PAUSE

    tray.activated.emit(QSystemTrayIcon.ActivationReason.Trigger)
    assert controleur.etat == Etat.LECTURE
    assert controleur._evenement_pause.is_set()
    assert controleur._index == 2


def test_avertir_si_tray_absent_notifie_une_fois(application, monkeypatch):
    appels = []
    monkeypatch.setattr(
        "piperread_gui.tray.notifier", lambda titre, message: appels.append((titre, message))
    )
    monkeypatch.setattr(
        "piperread_gui.tray.QSystemTrayIcon.isSystemTrayAvailable",
        staticmethod(lambda: False),
    )

    messages = load_messages("fr")
    assert avertir_si_tray_absent(messages) is False
    assert appels == [("PiperRead", msg(messages, "gui_tray_absent"))]


def test_avertir_si_tray_present_ne_notifie_pas(application, monkeypatch):
    appels = []
    monkeypatch.setattr(
        "piperread_gui.tray.notifier", lambda titre, message: appels.append((titre, message))
    )
    monkeypatch.setattr(
        "piperread_gui.tray.QSystemTrayIcon.isSystemTrayAvailable",
        staticmethod(lambda: True),
    )

    assert avertir_si_tray_absent(load_messages("fr")) is True
    assert appels == []

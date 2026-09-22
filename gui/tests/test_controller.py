import time

from PySide6.QtCore import Qt

from piperread_gui import controller as controller_module
from piperread_gui.controller import Etat, PlaybackController


class _ServeurFactice:
    def __init__(self, *_a, **_kw):
        self.base_url = "http://127.0.0.1:0"

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False


def _controleur_pret(monkeypatch, phrases):
    monkeypatch.setattr(controller_module, "read_clipboard", lambda: "texte")
    monkeypatch.setattr(
        controller_module, "split_sentences", lambda texte, lang: list(phrases)
    )
    monkeypatch.setattr(controller_module, "PiperHttpServer", _ServeurFactice)
    monkeypatch.setattr(
        controller_module,
        "synthesize",
        lambda base_url, phrase: b"audio:" + phrase.encode(),
    )
    return PlaybackController(model_path="modele.onnx", lang="fr")


def test_lire_joue_les_phrases_dans_l_ordre(monkeypatch):
    jouees = []
    monkeypatch.setattr(
        controller_module, "play_wav_bytes", lambda audio, **_kw: jouees.append(audio)
    )
    controleur = _controleur_pret(monkeypatch, ["une.", "deux.", "trois."])

    etats = []
    # DirectConnection : le fil de lecture émet depuis un thread Python hors
    # QThread, sans boucle d'événements Qt active dans ce test pour marshaler
    # une connexion en file d'attente vers le thread principal.
    controleur.etat_change.connect(etats.append, Qt.ConnectionType.DirectConnection)

    controleur.lire()
    controleur._fil.join(timeout=2.0)

    assert jouees == [b"audio:une.", b"audio:deux.", b"audio:trois."]
    assert etats[0] == Etat.LECTURE
    assert etats[-1] == Etat.ARRET
    assert controleur.etat == Etat.ARRET


def test_presse_papiers_vide_ne_demarre_rien(monkeypatch):
    monkeypatch.setattr(controller_module, "read_clipboard", lambda: "   ")
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")

    erreurs = []
    controleur.erreur.connect(erreurs.append)
    controleur.lire()

    assert erreurs == ["Presse-papiers vide : rien à lire."]
    assert controleur.etat == Etat.ARRET


def test_pause_seulement_pendant_la_lecture():
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    controleur._definir_etat(Etat.LECTURE)

    controleur.pause()
    assert controleur.etat == Etat.PAUSE
    assert not controleur._evenement_pause.is_set()

    controleur.reprendre()
    assert controleur.etat == Etat.LECTURE
    assert controleur._evenement_pause.is_set()


def test_pause_ignoree_hors_lecture():
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    controleur.pause()
    assert controleur.etat == Etat.ARRET


def test_arreter_quand_rien_ne_tourne_ne_fait_rien():
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    controleur.arreter()
    assert controleur.etat == Etat.ARRET


def test_phrase_suivante_interrompt_et_avance(monkeypatch):
    def jeu_bloquant(audio, stop_event=None, pause_event=None):
        while not stop_event.is_set():
            time.sleep(0.01)

    monkeypatch.setattr(controller_module, "play_wav_bytes", jeu_bloquant)
    controleur = _controleur_pret(monkeypatch, ["une.", "deux.", "trois."])

    phrases_jouees = []
    controleur.phrase_courante.connect(
        lambda numero, total: phrases_jouees.append(numero),
        Qt.ConnectionType.DirectConnection,
    )

    controleur.lire()
    limite = time.monotonic() + 2.0
    while len(phrases_jouees) < 1 and time.monotonic() < limite:
        time.sleep(0.01)

    controleur.phrase_suivante()
    limite = time.monotonic() + 2.0
    while len(phrases_jouees) < 2 and time.monotonic() < limite:
        time.sleep(0.01)

    assert phrases_jouees[:2] == [1, 2]
    controleur.arreter()
    assert controleur.etat == Etat.ARRET

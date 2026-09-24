import threading
import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from piperread_gui import controller as controller_module
from piperread_gui.controller import Etat, PlaybackController


class _ServeurFactice:
    demarrages: list = []
    arrets: list = []

    def __init__(self, model_path, telemetry="off"):
        self.model_path = model_path
        self.base_url = "http://127.0.0.1:0"
        self.est_actif = False

    def start(self):
        _ServeurFactice.demarrages.append(self.model_path)
        self.est_actif = True

    def stop(self):
        _ServeurFactice.arrets.append(self.model_path)
        self.est_actif = False


@pytest.fixture(autouse=True)
def _compteurs_remis_a_zero():
    _ServeurFactice.demarrages = []
    _ServeurFactice.arrets = []


def _controleur_pret(monkeypatch, phrases):
    monkeypatch.setattr(controller_module, "read_clipboard", lambda: "texte")
    monkeypatch.setattr(
        controller_module, "split_sentences", lambda texte, lang: list(phrases)
    )
    monkeypatch.setattr(controller_module, "PiperHttpServer", _ServeurFactice)
    monkeypatch.setattr(
        controller_module,
        "synthesize",
        lambda base_url, phrase, length_scale=None: b"audio:" + phrase.encode(),
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


def test_lire_nettoie_le_markdown_avant_le_decoupage(monkeypatch):
    monkeypatch.setattr(controller_module, "play_wav_bytes", lambda audio, **_kw: None)
    controleur = _controleur_pret(monkeypatch, ["test test"])

    recus = []
    monkeypatch.setattr(
        controller_module,
        "split_sentences",
        lambda texte, lang: recus.append(texte) or [texte],
    )
    monkeypatch.setattr(controller_module, "read_clipboard", lambda: "**test** test")

    controleur.lire()
    controleur._fil.join(timeout=2.0)

    assert recus == ["test test"]


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


def test_reglages_par_defaut():
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    assert controleur.model_path == Path("modele.onnx")
    assert controleur.lang == "fr"
    assert controleur.speed == 1.0
    assert controleur.messages["gui_menu_play"] == "Lire"


def test_appliquer_reglages_met_a_jour_le_controleur():
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    controleur.appliquer_reglages(Path("autre.onnx"), "en", 1.5)

    assert controleur.model_path == Path("autre.onnx")
    assert controleur.lang == "en"
    assert controleur.speed == 1.5
    assert controleur.messages["gui_menu_play"] == "Play"
    assert controleur._length_scale == pytest.approx(1 / 1.5)


def test_appliquer_reglages_meme_langue_ne_recharge_pas_les_messages():
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    messages_avant = controleur.messages
    controleur.appliquer_reglages(Path("modele.onnx"), "fr", 2.0)
    assert controleur.messages is messages_avant


def test_lire_transmet_le_length_scale_a_la_synthese(monkeypatch):
    appels = []
    monkeypatch.setattr(controller_module, "read_clipboard", lambda: "texte")
    monkeypatch.setattr(
        controller_module, "split_sentences", lambda texte, lang: ["une."]
    )
    monkeypatch.setattr(controller_module, "PiperHttpServer", _ServeurFactice)
    monkeypatch.setattr(controller_module, "play_wav_bytes", lambda audio, **_kw: None)

    def synthese_captee(base_url, phrase, length_scale=None):
        appels.append(length_scale)
        return b"audio"

    monkeypatch.setattr(controller_module, "synthesize", synthese_captee)

    controleur = PlaybackController(model_path="modele.onnx", lang="fr", speed=2.0)
    controleur.lire()
    controleur._fil.join(timeout=2.0)

    assert appels == [pytest.approx(0.5)]


def test_presse_papiers_vide_message_traduit_en(monkeypatch):
    monkeypatch.setattr(controller_module, "read_clipboard", lambda: "   ")
    controleur = PlaybackController(model_path="modele.onnx", lang="en")

    erreurs = []
    controleur.erreur.connect(erreurs.append)
    controleur.lire()

    assert erreurs == ["Clipboard empty: nothing to read."]


# --- serveur résident ---


def _attendre(condition, delai=2.0):
    limite = time.monotonic() + delai
    while not condition() and time.monotonic() < limite:
        time.sleep(0.01)
    return condition()


def test_un_seul_demarrage_de_serveur_pour_deux_lectures(monkeypatch):
    monkeypatch.setattr(controller_module, "play_wav_bytes", lambda audio, **_kw: None)
    controleur = _controleur_pret(monkeypatch, ["une.", "deux."])

    controleur.demarrer_moteur()
    controleur.lire()
    controleur._fil.join(timeout=2.0)
    controleur.lire()
    controleur._fil.join(timeout=2.0)

    assert _ServeurFactice.demarrages == [Path("modele.onnx")]


def test_changer_de_voix_relance_le_serveur_et_la_vitesse_non(monkeypatch):
    controleur = _controleur_pret(monkeypatch, ["une."])
    controleur.demarrer_moteur()
    assert _attendre(lambda: len(_ServeurFactice.demarrages) == 1)

    controleur.appliquer_reglages(Path("modele.onnx"), "fr", 2.0)
    controleur._moteur.submit(lambda: None).result()
    assert _ServeurFactice.demarrages == [Path("modele.onnx")]

    controleur.appliquer_reglages(Path("autre.onnx"), "fr", 2.0)
    controleur._moteur.submit(lambda: None).result()
    assert _ServeurFactice.demarrages == [Path("modele.onnx"), Path("autre.onnx")]
    assert _ServeurFactice.arrets == [Path("modele.onnx")]


def test_serveur_arrete_de_lui_meme_est_relance_a_la_lecture_suivante(monkeypatch):
    monkeypatch.setattr(controller_module, "play_wav_bytes", lambda audio, **_kw: None)
    controleur = _controleur_pret(monkeypatch, ["une."])

    controleur.lire()
    controleur._fil.join(timeout=2.0)
    controleur._serveur.est_actif = False
    controleur.lire()
    controleur._fil.join(timeout=2.0)

    assert len(_ServeurFactice.demarrages) == 2


def test_arreter_moteur_arrete_le_serveur(monkeypatch):
    controleur = _controleur_pret(monkeypatch, ["une."])
    controleur.demarrer_moteur()
    assert _attendre(lambda: len(_ServeurFactice.demarrages) == 1)

    controleur.arreter_moteur()

    assert _ServeurFactice.arrets == [Path("modele.onnx")]


def test_echec_du_demarrage_du_moteur_est_signale(monkeypatch):
    class _ServeurEnEchec(_ServeurFactice):
        def start(self):
            raise controller_module.ErreurServeurPiper("voix illisible")

    monkeypatch.setattr(controller_module, "PiperHttpServer", _ServeurEnEchec)
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    erreurs = []
    controleur.erreur.connect(erreurs.append, Qt.ConnectionType.DirectConnection)

    controleur.demarrer_moteur()
    controleur._moteur.submit(lambda: None).result(timeout=5.0)

    assert _attendre(lambda: erreurs == ["voix illisible"])


# --- phrase suivante préparée pendant la lecture ---


def test_phrase_suivante_demandee_pendant_la_lecture_de_la_courante(monkeypatch):
    controleur = _controleur_pret(monkeypatch, ["une.", "deux."])
    deuxieme_demandee = threading.Event()
    vue_pendant_la_premiere = []

    def synthese(base_url, phrase, length_scale=None):
        if phrase == "deux.":
            deuxieme_demandee.set()
        return phrase.encode()

    def jeu(audio, **_kw):
        if audio == b"une.":
            vue_pendant_la_premiere.append(deuxieme_demandee.wait(timeout=2.0))

    monkeypatch.setattr(controller_module, "synthesize", synthese)
    monkeypatch.setattr(controller_module, "play_wav_bytes", jeu)

    controleur.lire()
    controleur._fil.join(timeout=3.0)

    assert vue_pendant_la_premiere == [True]


def test_phrase_preparee_non_jouee_apres_un_retour_en_arriere(monkeypatch):
    controleur = _controleur_pret(monkeypatch, ["a.", "b.", "c."])
    jouees = []
    retour_fait = []

    def jeu(audio, stop_event=None, pause_event=None):
        jouees.append(audio)
        if audio == b"audio:b." and not retour_fait:
            retour_fait.append(True)
            controleur.phrase_precedente()

    monkeypatch.setattr(controller_module, "play_wav_bytes", jeu)

    controleur.lire()
    controleur._fil.join(timeout=3.0)

    assert jouees == [b"audio:a.", b"audio:b.", b"audio:a.", b"audio:b.", b"audio:c."]


def test_arret_pendant_le_chargement_de_la_voix_n_attend_pas_le_chargement(monkeypatch):
    liberer = threading.Event()

    class _ServeurLent(_ServeurFactice):
        def start(self):
            liberer.wait(timeout=5.0)
            super().start()

    controleur = _controleur_pret(monkeypatch, ["une."])
    monkeypatch.setattr(controller_module, "PiperHttpServer", _ServeurLent)
    monkeypatch.setattr(controller_module, "play_wav_bytes", lambda audio, **_kw: None)

    controleur.lire()
    assert _attendre(lambda: controleur.etat == Etat.LECTURE)
    debut = time.monotonic()
    controleur.arreter()
    duree = time.monotonic() - debut
    liberer.set()
    controleur._moteur.submit(lambda: None).result(timeout=5.0)

    assert duree < 1.0
    assert controleur.etat == Etat.ARRET


def test_filet_et_ponctuation_seule_ne_coupent_pas_la_lecture(monkeypatch):
    # Même comportement que le serveur HTTP de Piper : un texte sans phonème
    # n'y produit aucun audio et la route répond 500.
    def synthese(base_url, phrase, length_scale=None):
        if not any(c.isalnum() for c in phrase):
            raise controller_module.ErreurSynthese("Le serveur a répondu 500")
        return b"audio:" + phrase.encode()

    jouees = []
    erreurs = []
    monkeypatch.setattr(
        controller_module,
        "read_clipboard",
        lambda: "Premier paragraphe.\n\n---\n\n### Titre\n\n—\n\n* * *\n\nDernière phrase.",
    )
    monkeypatch.setattr(controller_module, "PiperHttpServer", _ServeurFactice)
    monkeypatch.setattr(controller_module, "synthesize", synthese)
    monkeypatch.setattr(
        controller_module, "play_wav_bytes", lambda audio, **_kw: jouees.append(audio)
    )
    controleur = PlaybackController(model_path="modele.onnx", lang="fr")
    controleur.erreur.connect(erreurs.append, Qt.ConnectionType.DirectConnection)

    controleur.lire()
    controleur._fil.join(timeout=2.0)

    assert jouees == [b"audio:Premier paragraphe.", b"audio:Titre", "audio:Dernière phrase.".encode()]
    assert erreurs == []

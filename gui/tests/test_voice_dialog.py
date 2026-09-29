import threading

import pytest
from PySide6.QtWidgets import QApplication, QDialog

from piperread_gui.i18n import load_messages
from piperread_gui.voice_dialog import VoiceDialog, voix_proposees
from piperread_gui.voice_download import ErreurTelechargement


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


class FauxTelechargement:
    instances = []

    def __init__(self, nom, dossier):
        self.nom = nom
        self.dossier = dossier
        self.lance = threading.Event()
        self.annule = threading.Event()
        FauxTelechargement.instances.append(self)

    def executer(self):
        self.lance.set()
        modele = self.dossier / f"{self.nom}.onnx"
        self.dossier.mkdir(parents=True, exist_ok=True)
        modele.write_bytes(b"m")
        return modele

    def annuler(self):
        self.annule.set()


class FauxEchec(FauxTelechargement):
    def executer(self):
        self.lance.set()
        raise ErreurTelechargement("reseau coupe")


class FauxLent(FauxTelechargement):
    def executer(self):
        self.lance.set()
        self.annule.wait(10)
        raise ErreurTelechargement("annule")


@pytest.fixture(autouse=True)
def _instances_vides():
    FauxTelechargement.instances = []


def _attendre(application, condition, delai=5.0):
    import time

    fin = time.monotonic() + delai
    while not condition() and time.monotonic() < fin:
        application.processEvents()
        time.sleep(0.01)
    return condition()


def test_propose_la_voix_recommandee_de_la_langue_en_tete():
    assert voix_proposees("fr")[0].nom == "fr_FR-siwis-medium"
    assert voix_proposees("de")[0].nom == "de_DE-thorsten-medium"
    assert {voix.nom for voix in voix_proposees("es")} == {voix.nom for voix in voix_proposees("en")}


def test_affiche_taille_et_licence_de_la_voix_proposee(application, tmp_path):
    fenetre = VoiceDialog(load_messages("fr"), "fr", tmp_path, fabrique=FauxTelechargement)

    assert fenetre._choix.currentData() == "fr_FR-siwis-medium"
    assert "60 Mo" in fenetre._details.text()
    assert "CC-BY 4.0" in fenetre._details.text()


def test_domaine_public_traduit(application, tmp_path):
    fenetre = VoiceDialog(load_messages("fr"), "en", tmp_path, fabrique=FauxTelechargement)

    assert fenetre._choix.currentData() == "en_US-ljspeech-medium"
    assert "Domaine public" in fenetre._details.text()


def test_aucun_telechargement_avant_le_clic(application, tmp_path):
    fenetre = VoiceDialog(load_messages("fr"), "fr", tmp_path / "voix", fabrique=FauxTelechargement)
    fenetre.show()
    application.processEvents()

    assert FauxTelechargement.instances == []
    assert not (tmp_path / "voix").exists()


def test_clic_telecharge_et_ferme_avec_la_voix_posee(application, tmp_path):
    fenetre = VoiceDialog(load_messages("fr"), "fr", tmp_path / "voix", fabrique=FauxTelechargement)

    fenetre._telecharger.click()

    assert _attendre(application, lambda: fenetre.result() == QDialog.DialogCode.Accepted)
    assert fenetre.voix_installee == tmp_path / "voix" / "fr_FR-siwis-medium.onnx"
    assert [i.nom for i in FauxTelechargement.instances] == ["fr_FR-siwis-medium"]


def test_le_clic_telecharge_la_voix_choisie(application, tmp_path):
    fenetre = VoiceDialog(load_messages("fr"), "fr", tmp_path, fabrique=FauxTelechargement)
    fenetre._choix.setCurrentIndex(fenetre._choix.findData("fr_FR-siwis-low"))

    fenetre._telecharger.click()

    assert _attendre(application, lambda: fenetre.voix_installee is not None)
    assert FauxTelechargement.instances[0].nom == "fr_FR-siwis-low"


def test_echec_reste_ouvert_et_permet_de_reessayer(application, tmp_path):
    fenetre = VoiceDialog(load_messages("fr"), "fr", tmp_path, fabrique=FauxEchec)

    fenetre._telecharger.click()

    assert _attendre(application, lambda: fenetre.erreur is not None)
    assert fenetre.voix_installee is None
    assert fenetre.result() != QDialog.DialogCode.Accepted
    assert "fr_FR-siwis-medium" in fenetre._etat.text()
    assert fenetre._telecharger.isEnabled()
    assert fenetre._choix.isEnabled()


def test_fermer_pendant_le_telechargement_l_interrompt(application, tmp_path):
    fenetre = VoiceDialog(load_messages("fr"), "fr", tmp_path, fabrique=FauxLent)

    fenetre._telecharger.click()
    assert FauxLent.instances[0].lance.wait(5)
    fenetre.reject()

    assert FauxLent.instances[0].annule.is_set()
    assert fenetre.voix_installee is None


def test_voix_deja_installee_signalee_et_non_telechargeable(application, tmp_path):
    fenetre = VoiceDialog(
        load_messages("fr"), "fr", tmp_path, installees={"fr_FR-siwis-medium"}, fabrique=FauxTelechargement
    )

    assert "installée" in fenetre._choix.itemText(0)
    assert not fenetre._telecharger.isEnabled()
    fenetre._choix.setCurrentIndex(fenetre._choix.findData("fr_FR-siwis-low"))
    assert fenetre._telecharger.isEnabled()

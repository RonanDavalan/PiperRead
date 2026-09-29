"""
voice_dialog.py — fenêtre qui propose une voix et la télécharge au clic, jamais avant.

Pourquoi ce fichier existe :
    Aucune voix n'est livrée ni téléchargée sans demande. Au premier lancement
    sans voix, l'interface ouvre cette fenêtre : elle nomme la voix
    recommandée de la langue de l'utilisateur avec sa taille et sa licence, et
    n'ouvre aucune connexion tant que « Télécharger » n'a pas été cliqué. La
    fenêtre de réglages l'ouvre aussi, pour changer de voix plus tard
    (`settings_dialog.py`). Le téléchargement tourne dans un fil, pour que la
    fenêtre reste vivante et que la fermer l'interrompe (`voice_download.py`).

Entrée / sortie :
    Entrée : les messages traduits déjà résolus, la langue, le dossier des
    voix de l'utilisateur et, pour les tests, la fabrique du téléchargement.
    Sortie : à la validation, `voix_installee` porte le chemin du `.onnx` posé
    dans le dossier des voix ; à la fermeture ou après un échec, `None`.
"""

import threading
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
)

from piperread_gui import voice_catalog
from piperread_gui.i18n import msg
from piperread_gui.voice_catalog import Voix
from piperread_gui.voice_download import ErreurTelechargement, Telechargement

_LANGUES = ("en", "fr", "de", "es")
_RANGS = ("recommended", "alternative", "light")
_DELAI_ARRET_SECONDES = 5.0


def voix_proposees(langue: str) -> list[Voix]:
    """Les voix du catalogue, celles de la langue de l'utilisateur d'abord."""
    ordre_langues = [langue, *(code for code in _LANGUES if code != langue)]
    return sorted(
        voice_catalog.CATALOGUE,
        key=lambda voix: (ordre_langues.index(voix.langue), _RANGS.index(voix.rang)),
    )


def _licence(messages: dict[str, str], licence: str) -> str:
    return msg(messages, "license_public_domain") if licence == "public-domain" else licence


class VoiceDialog(QDialog):
    termine = Signal(object)

    def __init__(
        self,
        messages: dict[str, str],
        langue: str,
        dossier_voix: Path,
        installees: set[str] | None = None,
        parent=None,
        fabrique=Telechargement,
    ):
        super().__init__(parent)
        self._messages = messages
        self._dossier_voix = dossier_voix
        self._installees = installees or set()
        self._fabrique = fabrique
        self._telechargement = None
        self._fil: threading.Thread | None = None
        self.voix_installee: Path | None = None
        self.erreur: str | None = None

        self.setWindowTitle(msg(messages, "gui_voice_title"))

        self._introduction = QLabel(msg(messages, "gui_voice_intro"))
        self._introduction.setWordWrap(True)

        self._choix = QComboBox()
        for voix in voix_proposees(langue):
            self._choix.addItem(self._libelle(voix), voix.nom)
        self._details = QLabel()
        self._details.setWordWrap(True)
        self._progression = QProgressBar()
        self._progression.setRange(0, 0)
        self._progression.setTextVisible(False)
        self._progression.hide()
        self._etat = QLabel()
        self._etat.setWordWrap(True)

        self._boutons = QDialogButtonBox()
        self._telecharger = self._boutons.addButton(
            msg(messages, "gui_voice_download"), QDialogButtonBox.ButtonRole.AcceptRole
        )
        self._plus_tard = self._boutons.addButton(
            msg(messages, "gui_voice_later"), QDialogButtonBox.ButtonRole.RejectRole
        )
        self._telecharger.clicked.connect(self._lancer)
        self._plus_tard.clicked.connect(self.reject)

        agencement = QVBoxLayout(self)
        agencement.addWidget(self._introduction)
        agencement.addWidget(self._choix)
        agencement.addWidget(self._details)
        agencement.addWidget(self._progression)
        agencement.addWidget(self._etat)
        agencement.addWidget(self._boutons)

        self._choix.currentIndexChanged.connect(self._actualiser_details)
        self.termine.connect(self._sur_fin)
        self._actualiser_details()

    def _libelle(self, voix: Voix) -> str:
        remarques = []
        if voix.rang != "alternative":
            remarques.append(msg(self._messages, f"voices_{voix.rang}"))
        if voix.nom in self._installees:
            remarques.append(msg(self._messages, "voices_installed"))
        return f"{voix.nom} ({', '.join(remarques)})" if remarques else voix.nom

    def _voix_choisie(self) -> Voix:
        return voice_catalog.voix_par_nom(self._choix.currentData())

    def _actualiser_details(self) -> None:
        voix = self._voix_choisie()
        self._details.setText(
            msg(
                self._messages,
                "gui_voice_details",
                msg(self._messages, "voices_size", str(voix.taille_mo)),
                _licence(self._messages, voix.licence),
            )
        )
        self._telecharger.setEnabled(voix.nom not in self._installees and self._fil is None)

    def _lancer(self) -> None:
        voix = self._voix_choisie()
        self._telechargement = self._fabrique(voix.nom, self._dossier_voix)
        self._choix.setEnabled(False)
        self._telecharger.setEnabled(False)
        self._etat.setText(msg(self._messages, "gui_voice_progress", voix.nom))
        self._progression.show()
        self._fil = threading.Thread(target=self._travailler, name="telechargement-voix", daemon=True)
        self._fil.start()

    def _travailler(self) -> None:
        try:
            resultat = self._telechargement.executer()
        except ErreurTelechargement as erreur:
            resultat = erreur
        self.termine.emit(resultat)

    def _sur_fin(self, resultat) -> None:
        self._fil = None
        self._progression.hide()
        if isinstance(resultat, Path):
            self.voix_installee = resultat
            self.accept()
            return
        self.erreur = str(resultat)
        self._choix.setEnabled(True)
        self._actualiser_details()
        self._etat.setText(msg(self._messages, "download_failed", self._voix_choisie().nom))

    def reject(self) -> None:
        if self._fil is not None:
            self._telechargement.annuler()
            self._fil.join(timeout=_DELAI_ARRET_SECONDES)
            self._fil = None
        super().reject()

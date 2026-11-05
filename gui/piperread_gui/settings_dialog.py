"""
settings_dialog.py — dialogue minimal de réglages (voix, vitesse, langue, lancement à l'ouverture de session).

Pourquoi ce fichier existe :
    Sépare la présentation Qt de la résolution de configuration (`config.py`) :
    ce dialogue affiche les valeurs actuelles du contrôleur, laisse
    l'utilisateur en choisir de nouvelles parmi les mêmes contraintes que le
    noyau (bornes de vitesse 0,5 à 3,0, voix installées, quatre langues, dossier
    de voix existant, dont le bouton de parcours relance la liste des voix), puis
    délègue l'écriture du fichier à `config.write_config_values` — le même
    fichier, les mêmes clés que `read.sh`. Le lancement à l'ouverture de
    session n'est pas une clé de ce fichier : la case lit et écrit le
    mécanisme du système (`autostart.py`). Le bouton « Télécharger une voix »
    ouvre la fenêtre de voix (`voice_dialog.py`) : la voix posée s'ajoute à la
    liste et devient la voix choisie, sans être enregistrée avant la
    validation.

Entrée / sortie :
    Entrée : le `PlaybackController` de la session (voix, vitesse, langue et
    messages traduits déjà résolus), le chemin de l'icône, repris par
    l'entrée de lancement automatique d'un clone, et les dossiers de voix
    (`config.voices_dirs`, dossier choisi compris) et ce dossier choisi
    (`voices_dir`) ; sans eux, le dossier de la voix courante seul.
    Sortie : à la validation,
    `piperread.conf` est réécrit, le contrôleur reçoit les nouveaux réglages
    (`appliquer_reglages`) et le lancement à l'ouverture de session est
    activé ou désactivé s'il a changé ; à l'annulation, rien n'est modifié.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from piperread_gui import autostart, config
from piperread_gui.i18n import msg
from piperread_gui.voice_dialog import VoiceDialog

_NOMS_LANGUES = {"en": "English", "fr": "Français", "de": "Deutsch", "es": "Español"}


class SettingsDialog(QDialog):
    def __init__(self, controller, icone=None, parent=None, voices_dirs=None, voices_dir=None):
        super().__init__(parent)
        self._controller = controller
        self._icone = icone
        messages = controller.messages
        self.setWindowTitle(msg(messages, "gui_settings_title"))

        dossiers = voices_dirs or [controller.model_path.parent]
        self._dossier_initial = voices_dir or ""
        self._dossiers_base = [dossier for dossier in dossiers if str(dossier) != self._dossier_initial]
        self._dossiers_voix = list(dossiers)
        self._modeles = config.available_voices(self._dossiers_voix)

        self._champ_dossier = QLineEdit(self._dossier_initial)
        self._champ_dossier.editingFinished.connect(self._dossier_modifie)
        self._parcourir = QPushButton(msg(messages, "gui_settings_browse"))
        self._parcourir.clicked.connect(self._parcourir_dossier)
        self._rangee_dossier = QWidget()
        disposition_dossier = QHBoxLayout(self._rangee_dossier)
        disposition_dossier.setContentsMargins(0, 0, 0, 0)
        disposition_dossier.addWidget(self._champ_dossier)
        disposition_dossier.addWidget(self._parcourir)

        self._voix = QComboBox()
        self._afficher_voix(controller.model_path.stem)

        self._obtenir_voix = QPushButton(msg(messages, "gui_settings_get_voice"))
        self._obtenir_voix.clicked.connect(self._telecharger_une_voix)

        self._vitesse = QDoubleSpinBox()
        self._vitesse.setRange(0.5, 3.0)
        self._vitesse.setSingleStep(0.1)
        self._vitesse.setDecimals(2)
        self._vitesse.setValue(controller.speed)

        self._langue = QComboBox()
        codes = ("en", "fr", "de", "es")
        for code in codes:
            self._langue.addItem(_NOMS_LANGUES[code], code)
        if controller.lang in codes:
            self._langue.setCurrentIndex(codes.index(controller.lang))

        self._lancement_auto = QCheckBox(msg(messages, "gui_settings_autostart"))
        self._lancement_auto_initial = autostart.est_active()
        self._lancement_auto.setChecked(self._lancement_auto_initial)

        agencement = QFormLayout(self)
        agencement.addRow(msg(messages, "gui_settings_voice"), self._voix)
        agencement.addRow(self._obtenir_voix)
        agencement.addRow(msg(messages, "gui_settings_voices_dir"), self._rangee_dossier)
        agencement.addRow(msg(messages, "gui_settings_speed"), self._vitesse)
        agencement.addRow(msg(messages, "gui_settings_lang"), self._langue)
        agencement.addRow(self._lancement_auto)

        boutons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        boutons.button(QDialogButtonBox.StandardButton.Save).setText(msg(messages, "gui_settings_save"))
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setText(msg(messages, "gui_settings_cancel"))
        boutons.accepted.connect(self._enregistrer)
        boutons.rejected.connect(self.reject)
        agencement.addRow(boutons)

    def _afficher_voix(self, voix_courante: str) -> None:
        self._voix.clear()
        noms_voix = list(self._modeles)
        if noms_voix:
            self._voix.addItems(noms_voix)
            self._voix.setEnabled(True)
            if voix_courante in noms_voix:
                self._voix.setCurrentText(voix_courante)
        else:
            self._voix.addItem(msg(self._controller.messages, "gui_settings_no_voice"))
            self._voix.setEnabled(False)

    @property
    def voices_dir(self) -> str | None:
        return self._dossier_valide() or None

    @property
    def voices_dirs(self) -> list:
        return list(self._dossiers_voix)

    def _dossier_valide(self) -> str:
        """Le dossier saisi, développé, s'il est valide ; vide sinon."""
        return config.valid_voices_dir(self._champ_dossier.text().strip()) or ""

    def _dossier_modifie(self) -> None:
        saisi = self._champ_dossier.text().strip()
        valide = self._dossier_valide()
        invalide = bool(saisi) and not valide
        self._champ_dossier.setStyleSheet("border: 1px solid #c0392b;" if invalide else "")
        self._champ_dossier.setToolTip(msg(self._controller.messages, "gui_settings_voices_dir_invalid") if invalide else "")
        courante = self._voix.currentText() if self._voix.isEnabled() else ""
        self._dossiers_voix = ([Path(valide)] if valide else []) + self._dossiers_base
        self._modeles = config.available_voices(self._dossiers_voix)
        self._afficher_voix(courante)

    def _parcourir_dossier(self) -> None:
        depart = self._dossier_valide() or str(Path.home())
        choisi = QFileDialog.getExistingDirectory(
            self, msg(self._controller.messages, "gui_settings_voices_dir_choose"), depart
        )
        if choisi:
            self._champ_dossier.setText(choisi)
            self._dossier_modifie()

    def _dossier_de_telechargement(self) -> Path:
        valide = self._dossier_valide()
        return Path(valide) if valide else (self._dossiers_base or self._dossiers_voix)[-1]

    def _creer_fenetre_voix(self) -> VoiceDialog:
        return VoiceDialog(
            self._controller.messages,
            self._controller.lang,
            self._dossier_de_telechargement(),
            installees=set(self._modeles),
            parent=self,
        )

    def _telecharger_une_voix(self) -> None:
        fenetre = self._creer_fenetre_voix()
        if fenetre.exec() != QDialog.DialogCode.Accepted or fenetre.voix_installee is None:
            return
        self._modeles = config.available_voices(self._dossiers_voix)
        self._afficher_voix(fenetre.voix_installee.stem)

    def _enregistrer(self) -> None:
        saisi = self._champ_dossier.text().strip()
        if saisi and not self._dossier_valide():
            self._dossier_modifie()
            return
        nom_voix = self._voix.currentText() if self._voix.isEnabled() else None
        vitesse = self._vitesse.value()
        langue = self._langue.currentData()

        valeurs = {"speed": f"{vitesse:.2f}", "lang": langue}
        if nom_voix:
            valeurs["voice"] = nom_voix
        if self._dossier_valide() != self._dossier_initial:
            valeurs["voices_dir"] = self._dossier_valide()
        config.write_config_values(valeurs)

        modele = self._modeles[nom_voix] if nom_voix else self._controller.model_path
        self._controller.appliquer_reglages(modele, langue, vitesse)

        lancement_auto = self._lancement_auto.isChecked()
        if lancement_auto != self._lancement_auto_initial:
            if lancement_auto:
                autostart.activer(self._icone)
            else:
                autostart.desactiver()
        self.accept()

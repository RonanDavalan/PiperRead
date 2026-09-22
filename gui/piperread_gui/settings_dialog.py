"""
settings_dialog.py — dialogue minimal de réglages (voix, vitesse, langue), écrit dans piperread.conf.

Pourquoi ce fichier existe :
    Sépare la présentation Qt de la résolution de configuration (`config.py`) :
    ce dialogue affiche les valeurs actuelles du contrôleur, laisse
    l'utilisateur en choisir de nouvelles parmi les mêmes contraintes que le
    noyau (bornes de vitesse 0,5 à 3,0, voix installées, quatre langues), puis
    délègue l'écriture du fichier à `config.write_config_values` — le même
    fichier, les mêmes clés que `read.sh`.

Entrée / sortie :
    Entrée : le `PlaybackController` de la session (voix, vitesse, langue et
    messages traduits déjà résolus). Sortie : à la validation,
    `piperread.conf` est réécrit et le contrôleur reçoit les nouveaux réglages
    (`appliquer_reglages`) ; à l'annulation, rien n'est modifié.
"""

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
)

from piperread_gui import config
from piperread_gui.i18n import msg

_NOMS_LANGUES = {"en": "English", "fr": "Français", "de": "Deutsch", "es": "Español"}


class SettingsDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self._controller = controller
        messages = controller.messages
        self.setWindowTitle(msg(messages, "gui_settings_title"))

        voix_dir = controller.model_path.parent
        noms_voix = sorted(p.stem for p in voix_dir.glob("*.onnx") if p.is_file())

        self._voix = QComboBox()
        if noms_voix:
            self._voix.addItems(noms_voix)
            voix_courante = controller.model_path.stem
            if voix_courante in noms_voix:
                self._voix.setCurrentText(voix_courante)
        else:
            self._voix.addItem(msg(messages, "gui_settings_no_voice"))
            self._voix.setEnabled(False)

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

        agencement = QFormLayout(self)
        agencement.addRow(msg(messages, "gui_settings_voice"), self._voix)
        agencement.addRow(msg(messages, "gui_settings_speed"), self._vitesse)
        agencement.addRow(msg(messages, "gui_settings_lang"), self._langue)

        boutons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        boutons.button(QDialogButtonBox.StandardButton.Save).setText(msg(messages, "gui_settings_save"))
        boutons.button(QDialogButtonBox.StandardButton.Cancel).setText(msg(messages, "gui_settings_cancel"))
        boutons.accepted.connect(self._enregistrer)
        boutons.rejected.connect(self.reject)
        agencement.addRow(boutons)

    def _enregistrer(self) -> None:
        voix_dir = self._controller.model_path.parent
        nom_voix = self._voix.currentText() if self._voix.isEnabled() else None
        vitesse = self._vitesse.value()
        langue = self._langue.currentData()

        valeurs = {"speed": f"{vitesse:.2f}", "lang": langue}
        if nom_voix:
            valeurs["voice"] = nom_voix
        config.write_config_values(valeurs)

        modele = voix_dir / f"{nom_voix}.onnx" if nom_voix else self._controller.model_path
        self._controller.appliquer_reglages(modele, langue, vitesse)
        self.accept()

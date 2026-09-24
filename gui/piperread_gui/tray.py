"""
tray.py — icône de tray et menu, branchés sur `PlaybackController`.

Pourquoi ce fichier existe :
    Sépare la présentation (icône, menu, activation/désactivation des
    entrées selon l'état) de la logique de lecture (`controller.py`), pour
    que l'une puisse être testée sans l'autre. Les libellés viennent des
    mêmes fichiers `lang/*.txt` que le noyau (`i18n.py`) : ce fichier ne
    contient aucun texte affiché à l'utilisateur en dur.

    Un clic gauche sur l'icône lit, met en pause ou reprend selon l'état :
    contrairement à un raccourci clavier, le tray connaît l'état courant et
    peut offrir ce geste unique sans ambiguïté. Le menu n'a donc pas
    d'entrée « Reprendre » : « Lire » en pause reprend déjà la lecture.
    L'entrée « Relancer » n'agit pas elle-même : elle émet `relance_demandee`,
    que `app.py` traite après avoir arrêté la lecture.

Entrée / sortie :
    Entrée : un `PlaybackController` déjà construit (dont les messages
    traduits, `controller.messages`), le chemin de l'icône SVG du projet et
    les dossiers de voix que le dialogue de réglages propose.
    Sortie : aucune (objet Qt vivant tant que l'application tourne).

Dépend de :
    `PySide6.QtWidgets` (`QSystemTrayIcon`, `QMenu`) ; `notifier.py` pour la
    notification unique en l'absence d'hôte de tray ; `i18n.py` pour les
    libellés ; `settings_dialog.py` pour le dialogue de réglages.
"""

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog, QMenu, QSystemTrayIcon

from piperread_gui.controller import Etat, PlaybackController
from piperread_gui.i18n import msg
from piperread_gui.notifier import notifier
from piperread_gui.settings_dialog import SettingsDialog


class PiperReadTray(QSystemTrayIcon):
    relance_demandee = Signal()

    def __init__(
        self, controller: PlaybackController, icon_path: Path, voices_dirs: list[Path] | None = None
    ):
        super().__init__(QIcon(str(icon_path)))
        self._controller = controller
        self._icon_path = icon_path
        self._voices_dirs = voices_dirs

        self._menu = QMenu()
        self._action_lire = self._menu.addAction("", self._controller.lire)
        self._action_pause = self._menu.addAction("", self._controller.pause)
        self._action_arreter = self._menu.addAction("", self._controller.arreter)
        self._menu.addSeparator()
        self._action_precedente = self._menu.addAction("", self._controller.phrase_precedente)
        self._action_suivante = self._menu.addAction("", self._controller.phrase_suivante)
        self._menu.addSeparator()
        self._action_reglages = self._menu.addAction("", self._ouvrir_reglages)
        self._action_relancer = self._menu.addAction("", self.relance_demandee.emit)
        self._menu.addSeparator()
        self._action_quitter = self._menu.addAction("", self._quitter)
        self.setContextMenu(self._menu)

        self._actualiser_textes()

        self.activated.connect(self._sur_activation)
        self._controller.etat_change.connect(self._sur_changement_etat)
        self._controller.erreur.connect(self._sur_erreur)
        self._sur_changement_etat(Etat.ARRET)

    def _actualiser_textes(self) -> None:
        messages = self._controller.messages
        self._action_lire.setText(msg(messages, "gui_menu_play"))
        self._action_pause.setText(msg(messages, "gui_menu_pause"))
        self._action_arreter.setText(msg(messages, "gui_menu_stop"))
        self._action_precedente.setText(msg(messages, "gui_menu_previous"))
        self._action_suivante.setText(msg(messages, "gui_menu_next"))
        self._action_reglages.setText(msg(messages, "gui_menu_settings"))
        self._action_relancer.setText(msg(messages, "gui_menu_restart"))
        self._action_quitter.setText(msg(messages, "gui_menu_quit"))
        self.setToolTip("PiperRead")

    def _sur_changement_etat(self, etat: Etat) -> None:
        self._action_lire.setEnabled(etat != Etat.LECTURE)
        self._action_pause.setEnabled(etat == Etat.LECTURE)
        self._action_arreter.setEnabled(etat != Etat.ARRET)
        self._action_precedente.setEnabled(etat != Etat.ARRET)
        self._action_suivante.setEnabled(etat != Etat.ARRET)

    def _sur_activation(self, raison: QSystemTrayIcon.ActivationReason) -> None:
        if raison != QSystemTrayIcon.ActivationReason.Trigger:
            return
        if self._controller.etat == Etat.LECTURE:
            self._controller.pause()
        else:
            self._controller.lire()

    def _sur_erreur(self, message: str) -> None:
        if self.isVisible():
            self.showMessage("PiperRead", message, QSystemTrayIcon.MessageIcon.Warning)
        else:
            notifier("PiperRead", message)

    def _ouvrir_reglages(self) -> None:
        dialogue = SettingsDialog(self._controller, self._icon_path, voices_dirs=self._voices_dirs)
        if dialogue.exec() == QDialog.DialogCode.Accepted:
            self._actualiser_textes()

    def _quitter(self) -> None:
        self._controller.arreter()
        QApplication.quit()


def avertir_si_tray_absent(messages: dict[str, str]) -> bool:
    disponible = QSystemTrayIcon.isSystemTrayAvailable()
    if not disponible:
        notifier("PiperRead", msg(messages, "gui_tray_absent"))
    return disponible

"""
tray.py — icône de tray et menu, branchés sur `PlaybackController`.

Pourquoi ce fichier existe :
    Sépare la présentation (icône, menu, activation/désactivation des
    entrées selon l'état) de la logique de lecture (`controller.py`), pour
    que l'une puisse être testée sans l'autre.

Entrée / sortie :
    Entrée : un `PlaybackController` déjà construit et le chemin de l'icône
    SVG du projet. Sortie : aucune (objet Qt vivant tant que l'application
    tourne).

Dépend de :
    `PySide6.QtWidgets` (`QSystemTrayIcon`, `QMenu`) ; `notifier.py` pour la
    notification unique en l'absence d'hôte de tray.
"""

from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from piperread_gui.controller import Etat, PlaybackController
from piperread_gui.notifier import notifier

MESSAGE_TRAY_ABSENT = (
    "Aucune zone de notification système détectée : PiperRead continue de "
    "fonctionner, mais son menu n'est accessible que si le bureau expose une "
    "zone de notification. Sur GNOME, installer l'extension « AppIndicator "
    "and KStatusNotifierItem Support » pour retrouver l'icône."
)


class PiperReadTray(QSystemTrayIcon):
    def __init__(self, controller: PlaybackController, icon_path: Path):
        super().__init__(QIcon(str(icon_path)))
        self._controller = controller

        menu = QMenu()
        self._action_lire = menu.addAction("Lire", self._controller.lire)
        self._action_pause = menu.addAction("Pause", self._controller.pause)
        self._action_reprendre = menu.addAction("Reprendre", self._controller.reprendre)
        self._action_arreter = menu.addAction("Arrêter", self._controller.arreter)
        menu.addSeparator()
        self._action_precedente = menu.addAction(
            "Phrase précédente", self._controller.phrase_precedente
        )
        self._action_suivante = menu.addAction(
            "Phrase suivante", self._controller.phrase_suivante
        )
        menu.addSeparator()
        self._action_reglages = menu.addAction("Réglages")
        self._action_reglages.setEnabled(False)
        self._action_reglages.setToolTip("Sessions suivantes du chantier « Interface graphique ».")
        menu.addSeparator()
        menu.addAction("Quitter", self._quitter)
        self.setContextMenu(menu)
        self.setToolTip("PiperRead")

        self._controller.etat_change.connect(self._sur_changement_etat)
        self._controller.erreur.connect(self._sur_erreur)
        self._sur_changement_etat(Etat.ARRET)

    def _sur_changement_etat(self, etat: Etat) -> None:
        self._action_lire.setEnabled(etat != Etat.LECTURE)
        self._action_pause.setEnabled(etat == Etat.LECTURE)
        self._action_reprendre.setEnabled(etat == Etat.PAUSE)
        self._action_arreter.setEnabled(etat != Etat.ARRET)
        self._action_precedente.setEnabled(etat != Etat.ARRET)
        self._action_suivante.setEnabled(etat != Etat.ARRET)

    def _sur_erreur(self, message: str) -> None:
        if self.isVisible():
            self.showMessage("PiperRead", message, QSystemTrayIcon.MessageIcon.Warning)
        else:
            notifier("PiperRead", message)

    def _quitter(self) -> None:
        self._controller.arreter()
        QApplication.quit()


def avertir_si_tray_absent() -> bool:
    disponible = QSystemTrayIcon.isSystemTrayAvailable()
    if not disponible:
        notifier("PiperRead", MESSAGE_TRAY_ABSENT)
    return disponible

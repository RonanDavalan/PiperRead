"""
controller.py — état de lecture, piloté par le tray, exécuté sur un fil de fond.

Pourquoi ce fichier existe :
    Le tray (`tray.py`) ne doit jamais bloquer la boucle d'événements Qt le
    temps d'une synthèse ou d'une lecture audio ; ce fichier isole la chaîne
    de lecture (capture → nettoyage Markdown → phrases → serveur → audio)
    dans un fil Python séparé, piloté par des signaux Qt et deux événements
    (`threading.Event`) pour la pause et l'arrêt. Le nettoyage précède le
    découpage, dans le même ordre que le noyau (capture → nettoyage →
    synthèse).

Entrée / sortie :
    Entrée : le chemin du modèle de voix, la langue de découpage et la
    vitesse (multiplicateur, 1.0 = voix naturelle), fixés à la construction
    puis modifiables par `appliquer_reglages` (dialogue de réglages).
    Sortie : trois signaux Qt — `etat_change` (nouvel `Etat`),
    `phrase_courante` (numéro, total) et `erreur` (message, dans la langue
    résolue) — que le tray relie à l'affichage du menu.

Dépend de :
    `PySide6.QtCore` pour les signaux ; `clipboard.py`, `cleaner.py`,
    `sentences.py`, `server.py`, `synth_client.py`, `player.py` ;
    `config.py` (`speed_to_length_scale`) et `i18n.py`.
"""

import threading
from enum import Enum, auto
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from piperread_gui.cleaner import clean_markdown
from piperread_gui.clipboard import read_clipboard
from piperread_gui.config import speed_to_length_scale
from piperread_gui.i18n import load_messages, msg
from piperread_gui.player import play_wav_bytes
from piperread_gui.sentences import split_sentences
from piperread_gui.server import ErreurServeurPiper, PiperHttpServer
from piperread_gui.synth_client import ErreurSynthese, synthesize


class Etat(Enum):
    ARRET = auto()
    LECTURE = auto()
    PAUSE = auto()


class PlaybackController(QObject):
    etat_change = Signal(object)
    phrase_courante = Signal(int, int)
    erreur = Signal(str)

    def __init__(self, model_path: Path, lang: str, speed: float = 1.0):
        super().__init__()
        self._model_path = Path(model_path)
        self._lang = lang
        self._speed = speed
        self._length_scale = speed_to_length_scale(speed)
        self._messages = load_messages(lang)
        self._etat = Etat.ARRET
        self._phrases: list[str] = []
        self._index = 0
        self._index_demande: int | None = None
        self._fil: threading.Thread | None = None
        self._evenement_pause = threading.Event()
        self._evenement_pause.set()
        self._evenement_arret = threading.Event()

    @property
    def etat(self) -> Etat:
        return self._etat

    @property
    def model_path(self) -> Path:
        return self._model_path

    @property
    def lang(self) -> str:
        return self._lang

    @property
    def speed(self) -> float:
        return self._speed

    @property
    def messages(self) -> dict[str, str]:
        return self._messages

    def appliquer_reglages(self, model_path: Path, lang: str, speed: float) -> None:
        self._model_path = Path(model_path)
        if lang != self._lang:
            self._lang = lang
            self._messages = load_messages(lang)
        self._speed = speed
        self._length_scale = speed_to_length_scale(speed)

    def _definir_etat(self, etat: Etat) -> None:
        self._etat = etat
        self.etat_change.emit(etat)

    def lire(self) -> None:
        if self._etat == Etat.PAUSE:
            self.reprendre()
            return
        if self._fil is not None and self._fil.is_alive():
            return

        texte = read_clipboard()
        if not texte.strip():
            self.erreur.emit(msg(self._messages, "gui_clipboard_empty"))
            return
        phrases = split_sentences(clean_markdown(texte), self._lang)
        if not phrases:
            self.erreur.emit(msg(self._messages, "gui_no_sentences"))
            return

        self._phrases = phrases
        self._index = 0
        self._index_demande = None
        self._evenement_arret.clear()
        self._evenement_pause.set()
        self._fil = threading.Thread(target=self._boucle_lecture, daemon=True)
        self._fil.start()

    def pause(self) -> None:
        if self._etat != Etat.LECTURE:
            return
        self._evenement_pause.clear()
        self._definir_etat(Etat.PAUSE)

    def reprendre(self) -> None:
        if self._etat != Etat.PAUSE:
            return
        self._evenement_pause.set()
        self._definir_etat(Etat.LECTURE)

    def arreter(self) -> None:
        if self._etat == Etat.ARRET:
            return
        self._evenement_arret.set()
        self._evenement_pause.set()
        if self._fil is not None:
            self._fil.join(timeout=5.0)
        self._fil = None
        self._definir_etat(Etat.ARRET)

    def phrase_precedente(self) -> None:
        self._sauter(-1)

    def phrase_suivante(self) -> None:
        self._sauter(1)

    def _sauter(self, delta: int) -> None:
        if self._etat == Etat.ARRET or not self._phrases:
            return
        cible = max(0, min(len(self._phrases) - 1, self._index + delta))
        if cible == self._index:
            return
        self._index_demande = cible
        self._evenement_arret.set()
        self._evenement_pause.set()

    def _boucle_lecture(self) -> None:
        try:
            with PiperHttpServer(self._model_path) as serveur:
                self._definir_etat(Etat.LECTURE)
                while self._index < len(self._phrases):
                    if self._evenement_arret.is_set() and self._index_demande is None:
                        return
                    phrase = self._phrases[self._index]
                    self.phrase_courante.emit(self._index + 1, len(self._phrases))
                    try:
                        audio = synthesize(serveur.base_url, phrase, length_scale=self._length_scale)
                    except ErreurSynthese as erreur:
                        self.erreur.emit(str(erreur))
                        return
                    play_wav_bytes(
                        audio,
                        stop_event=self._evenement_arret,
                        pause_event=self._evenement_pause,
                    )

                    if self._index_demande is not None:
                        self._index = self._index_demande
                        self._index_demande = None
                        self._evenement_arret.clear()
                        if self._etat == Etat.PAUSE:
                            self._evenement_pause.clear()
                        continue

                    if self._evenement_arret.is_set():
                        return
                    self._index += 1
        except ErreurServeurPiper as erreur:
            self.erreur.emit(str(erreur))
        finally:
            if self._index_demande is None:
                self._definir_etat(Etat.ARRET)

import io
import threading
import wave

import pytest

from piperread_gui import player


def _wav_de_test(canaux=1, largeur=2, frequence=22050, trames=b"\x00\x01" * 10) -> bytes:
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as fichier:
        fichier.setnchannels(canaux)
        fichier.setsampwidth(largeur)
        fichier.setframerate(frequence)
        fichier.writeframes(trames)
    return tampon.getvalue()


class _FluxFactice:
    def __init__(self, samplerate, channels, dtype):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.ecrit = b""

    def __enter__(self):
        return self

    def __exit__(self, *_exc_info):
        return False

    def write(self, trames):
        self.ecrit += trames


def test_joue_un_wav_16_bits(monkeypatch):
    flux_captures = []

    def faux_flux(samplerate, channels, dtype):
        flux = _FluxFactice(samplerate, channels, dtype)
        flux_captures.append(flux)
        return flux

    monkeypatch.setattr(player.sd, "RawOutputStream", faux_flux)

    player.play_wav_bytes(_wav_de_test(canaux=1, frequence=22050, trames=b"\x00\x01" * 5))

    (flux,) = flux_captures
    assert flux.samplerate == 22050
    assert flux.channels == 1
    assert flux.dtype == "int16"
    assert flux.ecrit == b"\x00\x01" * 5


def test_largeur_non_geree_leve(monkeypatch):
    monkeypatch.setattr(player.sd, "RawOutputStream", _FluxFactice)

    with pytest.raises(player.ErreurLecture):
        player.play_wav_bytes(_wav_de_test(largeur=1))


def test_arret_interrompt_l_ecriture(monkeypatch):
    flux_captures = []

    def faux_flux(samplerate, channels, dtype):
        flux = _FluxFactice(samplerate, channels, dtype)
        flux_captures.append(flux)
        return flux

    monkeypatch.setattr(player.sd, "RawOutputStream", faux_flux)
    monkeypatch.setattr(player, "_TAILLE_BLOC_TRAMES", 1)

    arret = threading.Event()
    arret.set()

    player.play_wav_bytes(
        _wav_de_test(canaux=1, frequence=22050, trames=b"\x00\x01" * 5),
        stop_event=arret,
    )

    (flux,) = flux_captures
    assert flux.ecrit == b""


def test_pause_bloque_l_ecriture_jusqu_a_liberation(monkeypatch):
    flux_captures = []

    def faux_flux(samplerate, channels, dtype):
        flux = _FluxFactice(samplerate, channels, dtype)
        flux_captures.append(flux)
        return flux

    monkeypatch.setattr(player.sd, "RawOutputStream", faux_flux)
    monkeypatch.setattr(player, "_TAILLE_BLOC_TRAMES", 1)

    pause = threading.Event()

    fil = threading.Thread(
        target=player.play_wav_bytes,
        args=(_wav_de_test(canaux=1, frequence=22050, trames=b"\x00\x01" * 3),),
        kwargs={"pause_event": pause},
    )
    fil.start()
    fil.join(timeout=0.2)
    assert fil.is_alive()

    pause.set()
    fil.join(timeout=2.0)
    assert not fil.is_alive()

    (flux,) = flux_captures
    assert flux.ecrit == b"\x00\x01" * 3

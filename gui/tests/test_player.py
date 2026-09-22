import io
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

import array
import io
import math
import wave

import pytest

from piperread_gui import loudness


@pytest.fixture(autouse=True)
def _etat_isole(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "etat"))
    return tmp_path


def _wav(amplitude: int, nombre: int = 2000) -> bytes:
    echantillons = array.array("h", [amplitude, -amplitude] * (nombre // 2))
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as fichier:
        fichier.setnchannels(1)
        fichier.setsampwidth(2)
        fichier.setframerate(22050)
        fichier.writeframes(echantillons.tobytes())
    return tampon.getvalue()


def _voix(tmp_path, nom="demo", contenu=b"x", langue=None):
    modele = tmp_path / f"{nom}.onnx"
    modele.write_bytes(contenu)
    if langue is not None:
        (tmp_path / f"{nom}.onnx.json").write_text(f'{{"language": {{"code": "{langue}"}}}}', encoding="utf-8")
    return modele


def test_le_niveau_d_une_onde_carree_est_son_amplitude_en_dbfs():
    niveau = loudness.level_db([loudness.wav_energy(_wav(16384))])
    assert niveau == pytest.approx(20 * math.log10(0.5), abs=0.01)


def test_flux_vide_sans_niveau():
    assert loudness.level_db([(0.0, 0)]) is None


def test_gain_ramene_a_la_cible_et_plafonne_a_moins_un_dbfs():
    assert loudness.gain_for_level(-15.0) == pytest.approx(10 ** ((loudness.TARGET_DB + 15.0) / 20))
    assert loudness.gain_for_level(-30.0) == loudness.MAX_GAIN
    assert 20 * math.log10(loudness.MAX_GAIN) <= -0.99


def test_mise_a_l_echelle_sans_ecretage():
    trames = array.array("h", [32767, -32768, 1000]).tobytes()
    assert loudness.scale_pcm16(trames, 1.0) == trames
    reduit = array.array("h")
    reduit.frombytes(loudness.scale_pcm16(trames, 0.5))
    assert list(reduit) == [16384, -16384, 500]


def test_mesure_une_fois_puis_gardee(tmp_path):
    modele = _voix(tmp_path)
    appels = []

    def synthese(texte):
        appels.append(texte)
        return _wav(16384)

    premier = loudness.voice_gain(modele, synthese)
    assert len(appels) == loudness.REPEATS
    assert loudness.voice_gain(modele, synthese) == pytest.approx(premier, abs=1e-3)
    assert len(appels) == loudness.REPEATS
    assert loudness.state_file().read_text(encoding="utf-8").count("\n") == 1


def test_fichier_de_voix_change_remesure_et_remplace_la_ligne(tmp_path):
    modele = _voix(tmp_path)
    loudness.voice_gain(modele, lambda _t: _wav(16384))
    _voix(tmp_path, contenu=b"xx")
    gain = loudness.voice_gain(modele, lambda _t: _wav(2000))
    assert gain == loudness.MAX_GAIN
    lignes = loudness.state_file().read_text(encoding="utf-8").splitlines()
    assert len(lignes) == 1 and lignes[0].startswith("demo\t2\t")


def test_texte_de_reference_dans_la_langue_de_la_voix(tmp_path):
    allemande = _voix(tmp_path, "de-voix", langue="de_DE")
    inconnue = _voix(tmp_path, "autre", langue="it_IT")
    assert loudness.voice_language(allemande) == "de"
    assert loudness.voice_language(inconnue) == "en"


def test_fichier_de_mesures_partage_avec_le_noyau(tmp_path):
    modele = _voix(tmp_path)
    taille = modele.stat().st_size
    date = int(modele.stat().st_mtime)
    fichier = loudness.state_file()
    fichier.parent.mkdir(parents=True)
    fichier.write_text(f"demo\t{taille}\t{date}\t-15.00\n", encoding="utf-8")
    gain = loudness.voice_gain(modele, lambda _t: pytest.fail("aucune synthèse attendue"))
    assert gain == pytest.approx(10 ** ((loudness.TARGET_DB + 15.0) / 20), abs=1e-4)

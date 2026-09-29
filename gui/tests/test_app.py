import pytest

from piperread_gui import app
from piperread_gui.app import _analyser_arguments


def test_sans_option_de_pilotage():
    arguments = _analyser_arguments(["--lang", "fr"])
    assert arguments.commande is None


@pytest.mark.parametrize(
    "option,commande",
    [
        ("--play", "lire"),
        ("--pause", "pause"),
        ("--resume", "reprendre"),
        ("--stop", "arreter"),
        ("--next", "phrase_suivante"),
        ("--previous", "phrase_precedente"),
        ("--quit", "quitter"),
    ],
)
def test_chaque_option_de_pilotage_produit_sa_commande(option, commande):
    arguments = _analyser_arguments([option])
    assert arguments.commande == commande


def test_options_de_pilotage_mutuellement_exclusives():
    with pytest.raises(SystemExit):
        _analyser_arguments(["--play", "--stop"])


def test_speed_absente_par_defaut():
    arguments = _analyser_arguments([])
    assert arguments.speed is None


def test_speed_transmise_telle_quelle():
    arguments = _analyser_arguments(["--speed", "1,5"])
    assert arguments.speed == "1,5"


def test_lang_absente_par_defaut():
    arguments = _analyser_arguments([])
    assert arguments.lang is None


def test_model_absent_par_defaut():
    arguments = _analyser_arguments([])
    assert arguments.model is None


# --- _resoudre_icone ---


def test_resoudre_icone_clone_prioritaire(tmp_path):
    ressources = tmp_path / "Ressources"
    ressources.mkdir()
    (ressources / "piperread.svg").touch()
    assert app._resoudre_icone(tmp_path) == ressources / "piperread.svg"


def test_resoudre_icone_repli_installee(tmp_path):
    assert app._resoudre_icone(tmp_path) == app._ICONE_INSTALLEE


def test_resoudre_icone_gelee_ignore_le_clone(monkeypatch, tmp_path):
    ressources = tmp_path / "Ressources"
    ressources.mkdir()
    (ressources / "piperread.svg").touch()
    monkeypatch.setattr(app.frozen, "installation_dir", lambda: tmp_path)

    assert app._resoudre_icone(tmp_path) == tmp_path / app._ICONE_GELEE


# --- --play sans instance lancée ---


def _sans_instance(monkeypatch):
    def envoyer(_commande):
        raise app.ErreurAucuneInstance("aucune instance")

    monkeypatch.setattr(app, "envoyer_commande", envoyer)


def test_play_sans_instance_laisse_demarrer_l_interface(monkeypatch):
    _sans_instance(monkeypatch)
    assert app._piloter_instance_existante("lire") is None


@pytest.mark.parametrize("commande", ["pause", "reprendre", "arreter", "phrase_suivante", "phrase_precedente", "quitter"])
def test_autres_commandes_sans_instance_sortent_en_erreur(monkeypatch, commande):
    _sans_instance(monkeypatch)
    assert app._piloter_instance_existante(commande) == 1


def test_play_avec_instance_lancee_ne_demarre_rien(monkeypatch, capsys):
    monkeypatch.setattr(app, "envoyer_commande", lambda commande: "ok")
    assert app._piloter_instance_existante("lire") == 0
    assert capsys.readouterr().out.strip() == "ok"


# --- première ouverture sans voix ---


class _FausseApplication:
    def __init__(self, *_):
        pass

    def setQuitOnLastWindowClosed(self, _):
        pass

    def setWindowIcon(self, _):
        pass


def _sans_voix(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setattr(app, "_VOICES_DIRS", [tmp_path / "voix"])
    monkeypatch.setattr(app, "QApplication", _FausseApplication)
    monkeypatch.setattr(app, "QIcon", lambda *_: None)
    monkeypatch.setattr(app, "notifier", lambda *_: None)
    for cle in ("PIPERREAD_SPEED", "PIPERREAD_VOICE", "PIPERREAD_LANG"):
        monkeypatch.delenv(cle, raising=False)


def test_sans_voix_la_fenetre_de_voix_est_proposee_avant_tout_demarrage(monkeypatch, tmp_path, capsys):
    _sans_voix(monkeypatch, tmp_path)
    appels = []
    monkeypatch.setattr(app, "_proposer_une_voix", lambda messages, langue: appels.append(langue))
    monkeypatch.setattr(app, "ControlServer", lambda: pytest.fail("le serveur de contrôle ne démarre pas sans voix"))

    assert app.main(["--lang", "fr"]) == 1

    assert appels == ["fr"]
    erreur = capsys.readouterr().err
    assert "piperread --list-voices" in erreur
    assert "{cmd}" not in erreur


def test_sans_voix_le_choix_de_la_fenetre_devient_la_voix_de_l_interface(monkeypatch, tmp_path):
    _sans_voix(monkeypatch, tmp_path)
    posee = tmp_path / "voix" / "fr_FR-siwis-medium.onnx"
    monkeypatch.setattr(app, "_proposer_une_voix", lambda messages, langue: posee)

    class Arret(Exception):
        pass

    class ControleArrete:
        def __init__(self):
            raise Arret()

    monkeypatch.setattr(app, "ControlServer", ControleArrete)

    with pytest.raises(Arret):
        app.main(["--lang", "fr"])

import sys

from piperread_gui import relance


def test_commande_par_module_sans_play(monkeypatch):
    monkeypatch.setattr(relance.frozen, "installation_dir", lambda: None)

    commande = relance.commande_de_relance(["--speed", "1,5", "--play", "--lang", "fr"])

    assert commande == [sys.executable, "-m", "piperread_gui.app", "--speed", "1,5", "--lang", "fr"]


def test_commande_de_l_executable_gele(monkeypatch, tmp_path):
    monkeypatch.setattr(relance.frozen, "installation_dir", lambda: tmp_path)

    assert relance.commande_de_relance([]) == [sys.executable]


def test_relancer_detache_le_nouveau_processus(monkeypatch):
    monkeypatch.setattr(relance.frozen, "installation_dir", lambda: None)
    monkeypatch.setattr(relance.sys, "platform", "linux")
    appels = []
    monkeypatch.setattr(relance.subprocess, "Popen", lambda commande, **options: appels.append((commande, options)))

    relance.relancer_instance(["--play"])

    commande, options = appels[0]
    assert commande == [sys.executable, "-m", "piperread_gui.app"]
    assert options["start_new_session"] is True

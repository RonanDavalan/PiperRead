import sys

import pytest

from piperread_gui import autostart


@pytest.fixture
def linux(tmp_path, monkeypatch):
    monkeypatch.setattr(autostart.sys, "platform", "linux")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(autostart, "ENTREE_SYSTEME", tmp_path / "etc" / autostart.NOM_ENTREE)
    return tmp_path


def _poser_entree_systeme(racine):
    entree = racine / "etc" / autostart.NOM_ENTREE
    entree.parent.mkdir(parents=True)
    entree.write_text("[Desktop Entry]\nType=Application\nName=PiperRead\nExec=piperread-gui\n")


# --- Linux, clone (aucune entrée système) ---


def test_clone_premier_lancement_ecrit_l_entree_utilisateur(linux):
    icone = linux / "piperread.svg"

    assert autostart.appliquer_defaut_premier_lancement(icone)

    valeurs = autostart._lire_entree(autostart.entree_utilisateur())
    assert valeurs["Exec"] == f"{sys.executable} -m piperread_gui.app"
    assert valeurs["Icon"] == str(icone)
    assert "Hidden" not in valeurs
    assert autostart.est_active()
    assert (linux / "state" / "piperread" / autostart.NOM_MARQUEUR).is_file()


def test_clone_choix_de_desactiver_jamais_reecrit(linux):
    autostart.appliquer_defaut_premier_lancement()
    autostart.desactiver()

    assert not autostart.appliquer_defaut_premier_lancement()
    assert not autostart.est_active()


def test_clone_entree_supprimee_par_le_bureau_pas_recreee(linux):
    autostart.appliquer_defaut_premier_lancement()
    autostart.entree_utilisateur().unlink()

    autostart.appliquer_defaut_premier_lancement()

    assert not autostart.entree_utilisateur().exists()


def test_clone_reactiver_reecrit_une_entree_complete(linux):
    autostart.desactiver()
    autostart.activer()

    valeurs = autostart._lire_entree(autostart.entree_utilisateur())
    assert "Hidden" not in valeurs
    assert valeurs["Exec"].endswith("-m piperread_gui.app")


def test_desactivation_gnome_lue_comme_desactivee(linux):
    entree = autostart.entree_utilisateur()
    entree.parent.mkdir(parents=True)
    entree.write_text("[Desktop Entry]\nExec=x\nX-GNOME-Autostart-enabled=false\n")

    assert not autostart.est_active()


# --- Linux, paquet (entrée système présente) ---


def test_paquet_premier_lancement_n_ecrit_rien(linux):
    _poser_entree_systeme(linux)

    autostart.appliquer_defaut_premier_lancement()

    assert autostart.est_active()
    assert not autostart.entree_utilisateur().exists()


def test_paquet_desactiver_masque_puis_activer_demasque(linux):
    _poser_entree_systeme(linux)

    autostart.desactiver()
    assert autostart._lire_entree(autostart.entree_utilisateur())["Hidden"] == "true"
    assert not autostart.est_active()

    autostart.activer()
    assert not autostart.entree_utilisateur().exists()
    assert autostart.est_active()


# --- Échappement de la ligne Exec ---


@pytest.mark.parametrize(
    "argument,attendu",
    [
        ("/usr/bin/python3", "/usr/bin/python3"),
        ("/home/a b/python3", '"/home/a b/python3"'),
        ("100%", "100%%"),
        ('/x/"q"', '"/x/\\\\"q\\\\""'),
    ],
)
def test_argument_exec(argument, attendu):
    assert autostart._argument_exec(argument) == attendu


# --- Windows (registre simulé) ---


class _RegistreFactice:
    def __init__(self):
        self.valeurs = {}

    def lire(self, cle, nom):
        return self.valeurs.get((cle, nom))

    def ecrire(self, cle, nom, valeur):
        self.valeurs[(cle, nom)] = valeur

    def supprimer(self, cle, nom):
        self.valeurs.pop((cle, nom), None)


@pytest.fixture
def windows(tmp_path, monkeypatch):
    monkeypatch.setattr(autostart.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    executable = tmp_path / "PiperRead" / "piperread-gui.exe"
    monkeypatch.setattr(autostart.sys, "executable", str(executable))
    registre = _RegistreFactice()
    monkeypatch.setattr(autostart, "registre", registre)
    return registre, executable


def test_windows_premier_lancement_pose_la_valeur_run(windows):
    registre, executable = windows

    autostart.appliquer_defaut_premier_lancement()

    assert registre.lire(autostart.CLE_RUN, "PiperRead") == f'"{executable.resolve()}"'
    assert autostart.est_active()


def test_windows_desactive_dans_le_gestionnaire_des_taches(windows):
    registre, _ = windows
    autostart.appliquer_defaut_premier_lancement()
    registre.ecrire(autostart.CLE_APPROBATION, "PiperRead", bytes([3]) + bytes(11))

    assert not autostart.est_active()
    assert not autostart.appliquer_defaut_premier_lancement()
    assert not autostart.est_active()

    autostart.activer()
    assert registre.lire(autostart.CLE_APPROBATION, "PiperRead") is None
    assert autostart.est_active()


def test_windows_desactiver_retire_la_valeur(windows):
    registre, _ = windows
    autostart.appliquer_defaut_premier_lancement()

    autostart.desactiver()

    assert registre.lire(autostart.CLE_RUN, "PiperRead") is None
    assert not autostart.appliquer_defaut_premier_lancement()
    assert not autostart.est_active()


def test_windows_dossier_deplace_corrige_le_chemin(windows, tmp_path, monkeypatch):
    registre, _ = windows
    autostart.appliquer_defaut_premier_lancement()
    nouvel_executable = tmp_path / "Ailleurs" / "piperread-gui.exe"
    monkeypatch.setattr(autostart.sys, "executable", str(nouvel_executable))

    autostart.appliquer_defaut_premier_lancement()

    assert registre.lire(autostart.CLE_RUN, "PiperRead") == f'"{nouvel_executable.resolve()}"'

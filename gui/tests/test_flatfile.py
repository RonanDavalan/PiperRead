from piperread_gui.flatfile import read_flat_file


def test_fichier_absent_rend_dictionnaire_vide(tmp_path):
    assert read_flat_file(tmp_path / "absent.txt") == {}


def test_lignes_vides_et_commentaires_ignores(tmp_path):
    fichier = tmp_path / "plat.txt"
    fichier.write_text("speed=1.5\n\n# commentaire\nvoice=demo\n")
    assert read_flat_file(fichier) == {"speed": "1.5", "voice": "demo"}


def test_cle_non_conforme_ignoree(tmp_path):
    fichier = tmp_path / "plat.txt"
    fichier.write_text("Speed=1.5\nSPEED=2\n1speed=3\nspeed_ok=4\n")
    assert read_flat_file(fichier) == {"speed_ok": "4"}


def test_ligne_sans_egal_donne_valeur_vide(tmp_path):
    fichier = tmp_path / "plat.txt"
    fichier.write_text("speed\n")
    assert read_flat_file(fichier) == {"speed": ""}


def test_dernier_gagne_sur_cle_dupliquee(tmp_path):
    fichier = tmp_path / "plat.txt"
    fichier.write_text("speed=1\nspeed=2\n")
    assert read_flat_file(fichier) == {"speed": "2"}


def test_valeur_peut_contenir_un_egal(tmp_path):
    fichier = tmp_path / "plat.txt"
    fichier.write_text("voice=nom=etrange\n")
    assert read_flat_file(fichier) == {"voice": "nom=etrange"}

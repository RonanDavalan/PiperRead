import pytest

from piperread_gui import config


@pytest.fixture(autouse=True)
def _config_isole(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for cle in ("PIPERREAD_SPEED", "PIPERREAD_VOICE", "PIPERREAD_LANG", "LANG"):
        monkeypatch.delenv(cle, raising=False)
    return tmp_path


def _ecrire_conf(tmp_path, contenu):
    chemin = config.config_file_path()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")


def _voix(tmp_path, *noms):
    dossier = tmp_path / "voices"
    dossier.mkdir(exist_ok=True)
    for nom in noms:
        (dossier / f"{nom}.onnx").touch()
    return dossier


# --- config_file_path ---


def test_config_file_path_suit_xdg_config_home(tmp_path):
    assert config.config_file_path() == tmp_path / "config" / "piperread" / "piperread.conf"


# --- load_config_file ---


def test_load_config_file_absent_rend_valeurs_vides():
    valeurs, inconnues = config.load_config_file()
    assert valeurs == {}
    assert inconnues == []


def test_load_config_file_separe_cles_connues_et_inconnues(tmp_path):
    _ecrire_conf(tmp_path, "speed=1.5\nvoice=demo\nlang=fr\nautre=1\n")
    valeurs, inconnues = config.load_config_file()
    assert valeurs == {"speed": "1.5", "voice": "demo", "lang": "fr"}
    assert inconnues == ["autre"]


def test_load_config_file_nettoie_espaces_et_cr(tmp_path):
    _ecrire_conf(tmp_path, "speed= 1.5 \r\n")
    valeurs, _ = config.load_config_file()
    assert valeurs["speed"] == "1.5"


# --- normalize_speed ---


@pytest.mark.parametrize(
    "brut,attendu",
    [
        ("1", "1"),
        ("1.5", "1.5"),
        ("1,5", "1.5"),
        ("0.5", "0.5"),
        ("3.0", "3.0"),
    ],
)
def test_normalize_speed_accepte_les_bornes(brut, attendu):
    assert config.normalize_speed(brut) == attendu


@pytest.mark.parametrize("brut", ["0.49", "3.01", "0", "-1", "abc", "", "1.5.2"])
def test_normalize_speed_refuse_hors_bornes_ou_non_numerique(brut):
    assert config.normalize_speed(brut) is None


def test_speed_to_length_scale():
    assert config.speed_to_length_scale(2.0) == pytest.approx(0.5)
    assert config.speed_to_length_scale(1.0) == pytest.approx(1.0)


# --- valid_lang ---


@pytest.mark.parametrize("code", ["en", "fr", "de", "es"])
def test_valid_lang_accepte_les_quatre_langues(code):
    assert config.valid_lang(code) == code


@pytest.mark.parametrize("code", ["it", "EN", "", "fr_FR"])
def test_valid_lang_refuse_le_reste(code):
    assert config.valid_lang(code) is None


# --- voix ---


def test_validate_voice_accepte_un_fichier_existant(tmp_path):
    voices_dir = _voix(tmp_path, "demo")
    assert config.validate_voice("demo", [voices_dir]) == "demo"


def test_validate_voice_refuse_un_fichier_absent(tmp_path):
    voices_dir = _voix(tmp_path)
    assert config.validate_voice("fantome", [voices_dir]) is None


def test_validate_voice_refuse_un_nom_avec_barre_oblique(tmp_path):
    voices_dir = _voix(tmp_path, "demo")
    assert config.validate_voice("../demo", [voices_dir]) is None


def test_default_voice_name_premiere_par_ordre_alphabetique(tmp_path):
    voices_dir = _voix(tmp_path, "zebra", "alpha")
    assert config.default_voice_name([voices_dir]) == "alpha"


def test_default_voice_name_aucune_voix(tmp_path):
    voices_dir = _voix(tmp_path)
    assert config.default_voice_name([voices_dir]) is None


# --- resolve_setting : ordre de priorité ---


def test_resolve_setting_option_prioritaire_sur_le_reste(monkeypatch, tmp_path):
    monkeypatch.setenv("PIPERREAD_LANG", "de")
    resultat = config.resolve_setting("lang", config.valid_lang, "en", {"lang": "es"})
    assert resultat.value == "en"
    assert resultat.source == "--lang"


def test_resolve_setting_environnement_avant_fichier(monkeypatch):
    monkeypatch.setenv("PIPERREAD_LANG", "de")
    resultat = config.resolve_setting("lang", config.valid_lang, None, {"lang": "es"})
    assert resultat.value == "de"
    assert resultat.source == "PIPERREAD_LANG"


def test_resolve_setting_fichier_si_rien_d_autre():
    resultat = config.resolve_setting("lang", config.valid_lang, None, {"lang": "es"})
    assert resultat.value == "es"
    assert resultat.source == "piperread.conf"


def test_resolve_setting_defaut_si_rien_de_valide():
    resultat = config.resolve_setting("lang", config.valid_lang, None, {})
    assert resultat.value is None
    assert resultat.source == "default"


def test_resolve_setting_option_invalide_refuse_immediatement():
    resultat = config.resolve_setting("lang", config.valid_lang, "it", {"lang": "es"})
    assert resultat.value is None
    assert resultat.invalid == ("lang", "it", "--lang")
    assert resultat.warnings == []


def test_resolve_setting_environnement_invalide_avertit_et_continue(monkeypatch):
    monkeypatch.setenv("PIPERREAD_LANG", "it")
    resultat = config.resolve_setting("lang", config.valid_lang, None, {"lang": "es"})
    assert resultat.value == "es"
    assert resultat.warnings == [("lang", "it", "PIPERREAD_LANG")]


def test_resolve_setting_fichier_invalide_avertit_et_rend_defaut():
    resultat = config.resolve_setting("lang", config.valid_lang, None, {"lang": "it"})
    assert resultat.value is None
    assert resultat.warnings == [("lang", "it", "piperread.conf")]


# --- resolve_settings : bout en bout ---


def test_resolve_settings_tout_par_defaut(tmp_path):
    voices_dir = _voix(tmp_path, "alpha")
    resultat = config.resolve_settings([voices_dir])
    assert resultat.speed == 1.0
    assert resultat.voice == "alpha"
    assert resultat.model_path == voices_dir / "alpha.onnx"
    assert resultat.lang == "en"
    assert resultat.invalid is None


def test_resolve_settings_lit_le_fichier(tmp_path):
    voices_dir = _voix(tmp_path, "alpha", "beta")
    _ecrire_conf(tmp_path, "speed=1.5\nvoice=beta\nlang=de\n")
    resultat = config.resolve_settings([voices_dir])
    assert resultat.speed == 1.5
    assert resultat.voice == "beta"
    assert resultat.lang == "de"


def test_resolve_settings_option_prioritaire_sur_fichier(tmp_path):
    voices_dir = _voix(tmp_path, "alpha")
    _ecrire_conf(tmp_path, "speed=1.5\nlang=de\n")
    resultat = config.resolve_settings([voices_dir], speed_option="2.0", lang_option="es")
    assert resultat.speed == 2.0
    assert resultat.lang == "es"


def test_resolve_settings_repli_sur_variable_lang_systeme(tmp_path, monkeypatch):
    voices_dir = _voix(tmp_path, "alpha")
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    resultat = config.resolve_settings([voices_dir])
    assert resultat.lang == "de"
    assert resultat.lang_source == "default"


def test_resolve_settings_voix_invalide_dans_le_fichier_retombe_sur_le_defaut(tmp_path):
    voices_dir = _voix(tmp_path, "alpha")
    _ecrire_conf(tmp_path, "voice=fantome\n")
    resultat = config.resolve_settings([voices_dir])
    assert resultat.voice == "alpha"
    assert resultat.warnings == [("voice", "fantome", "piperread.conf")]


def test_resolve_settings_speed_option_invalide_est_signalee(tmp_path):
    voices_dir = _voix(tmp_path, "alpha")
    resultat = config.resolve_settings([voices_dir], speed_option="99")
    assert resultat.invalid == ("speed", "99", "--speed")


# --- write_config_values ---


def test_write_config_values_cree_le_fichier(tmp_path):
    config.write_config_values({"speed": "1.5", "voice": "demo", "lang": "fr"})
    chemin = config.config_file_path()
    assert chemin.exists()
    valeurs, _ = config.load_config_file()
    assert valeurs == {"speed": "1.5", "voice": "demo", "lang": "fr"}


def test_write_config_values_permissions_du_dossier(tmp_path):
    config.write_config_values({"speed": "1.0"})
    assert oct(config.config_file_path().parent.stat().st_mode & 0o777) == oct(0o700)


def test_write_config_values_remplace_en_place_sans_toucher_le_reste(tmp_path):
    _ecrire_conf(tmp_path, "# commentaire conservé\nspeed=1.0\nautre=1\nvoice=demo\n")
    config.write_config_values({"speed": "2.0"})
    contenu = config.config_file_path().read_text(encoding="utf-8")
    assert contenu.splitlines() == [
        "# commentaire conservé",
        "speed=2.0",
        "autre=1",
        "voice=demo",
    ]


def test_write_config_values_ajoute_une_cle_absente(tmp_path):
    _ecrire_conf(tmp_path, "speed=1.0\n")
    config.write_config_values({"lang": "es"})
    valeurs, _ = config.load_config_file()
    assert valeurs == {"speed": "1.0", "lang": "es"}


def test_write_config_values_derniere_occurrence_gagne(tmp_path):
    _ecrire_conf(tmp_path, "speed=1.0\nspeed=1.2\n")
    config.write_config_values({"speed": "2.0"})
    contenu = config.config_file_path().read_text(encoding="utf-8")
    assert contenu.splitlines() == ["speed=1.0", "speed=2.0"]


# --- voices_dirs, find_voice, available_voices : deux dossiers ---


def _dossier(racine, *noms):
    racine.mkdir(parents=True, exist_ok=True)
    for nom in noms:
        (racine / f"{nom}.onnx").touch()
    return racine


def test_voices_dirs_clone_puis_utilisateur(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    depot = tmp_path / "depot"
    (depot / "voices").mkdir(parents=True)
    assert config.voices_dirs(depot) == [depot / "voices", tmp_path / "data" / "piperread" / "voices"]


def test_voices_dirs_sans_dossier_du_clone(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    depot = tmp_path / "depot_installe"
    assert config.voices_dirs(depot) == [tmp_path / "data" / "piperread" / "voices"]


def test_voices_dirs_repli_home_sans_xdg_data_home(tmp_path, monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(config.Path, "home", lambda: tmp_path / "home")
    depot = tmp_path / "depot_installe"
    assert config.voices_dirs(depot) == [tmp_path / "home" / ".local" / "share" / "piperread" / "voices"]


def test_voices_dirs_executable_windows_seul_son_dossier(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    installation = tmp_path / "piperread-gui"
    assert config.voices_dirs(installation, frozen=True) == [installation / "voices"]


def test_find_voice_cherche_dans_l_ordre(tmp_path):
    clone = _dossier(tmp_path / "clone", "b-clone", "c-commune")
    utilisateur = _dossier(tmp_path / "utilisateur", "a-utilisateur", "c-commune")
    dossiers = [clone, utilisateur]
    assert config.find_voice("b-clone", dossiers) == clone / "b-clone.onnx"
    assert config.find_voice("a-utilisateur", dossiers) == utilisateur / "a-utilisateur.onnx"
    assert config.find_voice("c-commune", dossiers) == clone / "c-commune.onnx"
    assert config.find_voice("d-absente", dossiers) is None


def test_available_voices_reunit_les_dossiers(tmp_path):
    clone = _dossier(tmp_path / "clone", "b-clone", "c-commune")
    utilisateur = _dossier(tmp_path / "utilisateur", "a-utilisateur", "c-commune")
    voix = config.available_voices([clone, utilisateur])
    assert list(voix) == ["a-utilisateur", "b-clone", "c-commune"]
    assert voix["c-commune"] == clone / "c-commune.onnx"


def test_available_voices_dossier_absent(tmp_path):
    assert config.available_voices([tmp_path / "absent"]) == {}


def test_resolve_settings_voix_du_dossier_utilisateur_malgre_le_clone(tmp_path):
    clone = _dossier(tmp_path / "clone", "fr_FR-siwis-medium")
    utilisateur = _dossier(tmp_path / "utilisateur", "fr_FR-gilles-low")
    _ecrire_conf(tmp_path, "voice=fr_FR-gilles-low\n")
    resultat = config.resolve_settings([clone, utilisateur])
    assert resultat.voice == "fr_FR-gilles-low"
    assert resultat.model_path == utilisateur / "fr_FR-gilles-low.onnx"
    assert resultat.warnings == []


def test_resolve_settings_defaut_tous_dossiers_confondus(tmp_path):
    clone = _dossier(tmp_path / "clone", "zebra")
    utilisateur = _dossier(tmp_path / "utilisateur", "alpha")
    resultat = config.resolve_settings([clone, utilisateur])
    assert resultat.model_path == utilisateur / "alpha.onnx"

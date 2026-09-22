from piperread_gui.i18n import load_messages, msg


def test_load_messages_anglais_seul():
    messages = load_messages("en")
    assert messages["gui_menu_play"] == "Play"


def test_load_messages_fusionne_avec_l_anglais():
    messages = load_messages("fr")
    assert messages["gui_menu_play"] == "Lire"
    # Clé partagée avec le noyau, présente dans les deux fichiers.
    assert messages["stopped"] == "Lecture arrêtée."


def test_load_messages_quatre_langues_chargent_sans_erreur():
    for code in ("en", "fr", "de", "es"):
        messages = load_messages(code)
        assert messages["gui_settings_title"]


def test_msg_substitue_les_arguments_positionnels():
    messages = {"exemple": "Valeur invalide « {2} » pour {1}."}
    assert msg(messages, "exemple", "--speed", "99") == 'Valeur invalide « 99 » pour --speed.'


def test_msg_cle_absente_rend_la_cle():
    assert msg({}, "cle_inconnue") == "cle_inconnue"

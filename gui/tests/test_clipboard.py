import subprocess

from PySide6.QtWidgets import QApplication

from piperread_gui import clipboard


def _application() -> QApplication:
    return QApplication.instance() or QApplication([])


def _resultat(stdout: str) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr="")


def test_utilise_wl_paste_en_priorite(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda binaire: "/usr/bin/" + binaire)

    appels = []

    def faux_run(command, **_kwargs):
        appels.append(command)
        return _resultat("texte wayland")

    monkeypatch.setattr(clipboard.subprocess, "run", faux_run)

    assert clipboard.read_clipboard() == "texte wayland"
    assert appels[0][0] == "wl-paste"


def test_repli_sur_xsel_si_wayland_absent(monkeypatch):
    monkeypatch.setattr(
        clipboard.shutil,
        "which",
        lambda binaire: None if binaire == "wl-paste" else "/usr/bin/xsel",
    )
    monkeypatch.setattr(
        clipboard.subprocess, "run", lambda command, **_kwargs: _resultat("texte x11")
    )

    assert clipboard.read_clipboard() == "texte x11"


def test_repli_sur_xsel_si_wayland_vide(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda binaire: "/usr/bin/" + binaire)

    def faux_run(command, **_kwargs):
        if command[0] == "wl-paste":
            return _resultat("   \n")
        return _resultat("texte x11")

    monkeypatch.setattr(clipboard.subprocess, "run", faux_run)

    assert clipboard.read_clipboard() == "texte x11"


def test_selection_prioritaire_sur_le_presse_papiers(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda binaire: "/usr/bin/" + binaire)

    appels = []

    def faux_run(command, **_kwargs):
        appels.append(command)
        if "--primary" in command:
            return _resultat("texte sélectionné")
        return _resultat("texte copié")

    monkeypatch.setattr(clipboard.subprocess, "run", faux_run)

    assert clipboard.read_clipboard() == "texte sélectionné"
    assert appels == [["wl-paste", "--primary", "--no-newline"]]


def test_repli_sur_le_presse_papiers_si_selection_vide(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda binaire: "/usr/bin/" + binaire)

    appels = []

    def faux_run(command, **_kwargs):
        appels.append(command)
        if "--primary" in command:
            return _resultat(" \n\t")
        return _resultat("texte copié")

    monkeypatch.setattr(clipboard.subprocess, "run", faux_run)

    assert clipboard.read_clipboard() == "texte copié"
    assert appels == [
        ["wl-paste", "--primary", "--no-newline"],
        ["xsel", "--primary", "--output"],
        ["wl-paste", "--no-newline"],
    ]


def test_selection_x11_avant_presse_papiers_wayland(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda binaire: "/usr/bin/" + binaire)

    def faux_run(command, **_kwargs):
        if command[0] == "xsel" and "--primary" in command:
            return _resultat("sélection x11")
        if "--primary" in command:
            return _resultat("")
        return _resultat("texte copié")

    monkeypatch.setattr(clipboard.subprocess, "run", faux_run)

    assert clipboard.read_clipboard() == "sélection x11"


def test_chaine_vide_si_aucun_outil(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda binaire: None)
    assert clipboard.read_clipboard() == ""


def test_windows_lit_le_presse_papiers_qt(monkeypatch):
    application = _application()
    application.clipboard().setText("texte windows")
    monkeypatch.setattr(clipboard.sys, "platform", "win32")

    appels = []
    monkeypatch.setattr(
        clipboard.subprocess, "run", lambda *a, **kw: appels.append((a, kw))
    )

    assert clipboard.read_clipboard() == "texte windows"
    assert appels == []


def test_windows_chaine_vide_sans_application_qt(monkeypatch):
    monkeypatch.setattr(clipboard.sys, "platform", "win32")
    monkeypatch.setattr(
        "PySide6.QtWidgets.QApplication.instance", staticmethod(lambda: None)
    )

    assert clipboard.read_clipboard() == ""


def test_outil_bloque_est_abandonne_apres_le_delai(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda binaire: f"/usr/bin/{binaire}")

    def faux_run(command, **kwargs):
        if command[0] == "wl-paste":
            raise subprocess.TimeoutExpired(command, kwargs["timeout"])
        return _resultat("texte x11")

    monkeypatch.setattr(clipboard.subprocess, "run", faux_run)
    assert clipboard.read_clipboard() == "texte x11"

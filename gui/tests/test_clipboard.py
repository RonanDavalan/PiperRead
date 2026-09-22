import subprocess

from piperread_gui import clipboard


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


def test_chaine_vide_si_aucun_outil(monkeypatch):
    monkeypatch.setattr(clipboard.shutil, "which", lambda binaire: None)
    assert clipboard.read_clipboard() == ""

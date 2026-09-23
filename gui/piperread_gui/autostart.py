"""
autostart.py — lancement de l'interface à l'ouverture de session, actif par défaut.

Pourquoi ce fichier existe :
    L'interface n'a de valeur que si elle est déjà là au moment du clic
    (décision « lancement à l'ouverture de session, actif par défaut »). L'état
    vit dans le mécanisme que le bureau affiche et modifie déjà, jamais dans
    `piperread.conf`, où le noyau signalerait une clé inconnue :
    - Linux : spécification XDG Autostart. Le paquet installe l'entrée
      système `/etc/xdg/autostart/piperread-gui.desktop` ; une entrée
      utilisateur de même nom, `Hidden=true`, la masque. Depuis un clone, sans
      entrée système, l'entrée utilisateur complète lance l'interpréteur en
      cours (celui du venv, chemin non résolu : le résoudre sortirait du venv).
    - Windows : valeur `PiperRead` de la clé `Run` de l'utilisateur. Une
      désactivation faite dans l'onglet Démarrage du Gestionnaire des tâches
      est rangée sous `StartupApproved\\Run` (premier octet impair) et lue
      comme telle.
    Le défaut n'est posé qu'au premier lancement, repéré par un fichier
    marqueur dans le dossier d'état : un choix de l'utilisateur n'est jamais
    réécrit.

Entrée / sortie :
    `est_active()`, `activer(icone)`, `desactiver()` ;
    `appliquer_defaut_premier_lancement(icone)` à chaque démarrage de
    l'interface (sous Windows, corrige aussi le chemin si le dossier de
    l'exécutable a été déplacé).
"""

import os
import sys
from pathlib import Path

NOM_ENTREE = "piperread-gui.desktop"
ENTREE_SYSTEME = Path("/etc/xdg/autostart") / NOM_ENTREE
NOM_MARQUEUR = "autostart-default-applied"
NOM_VALEUR_WINDOWS = "PiperRead"
CLE_RUN = r"Software\Microsoft\Windows\CurrentVersion\Run"
CLE_APPROBATION = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"

_CARACTERES_A_CITER = set(' \t\n"\'\\><~|&;$*?#()`')


def dossier_etat() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "piperread"
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "piperread"


def entree_utilisateur() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "autostart" / NOM_ENTREE


def _argument_exec(argument: str) -> str:
    # Spécification Desktop Entry : un argument qui contient un caractère
    # réservé est cité ; dans la citation, " ` $ \ sont précédés d'un \,
    # puis la règle des chaînes double chaque \. « % » s'écrit « %% ».
    argument = argument.replace("%", "%%")
    if not _CARACTERES_A_CITER.intersection(argument):
        return argument
    cite = "".join("\\" + c if c in '"`$\\' else c for c in argument)
    return '"' + cite.replace("\\", "\\\\") + '"'


def _lire_entree(chemin: Path) -> dict[str, str]:
    valeurs: dict[str, str] = {}
    section = None
    for ligne in chemin.read_text(encoding="utf-8", errors="replace").splitlines():
        ligne = ligne.strip()
        if ligne.startswith("["):
            section = ligne
        elif section == "[Desktop Entry]" and "=" in ligne:
            cle, valeur = ligne.split("=", 1)
            valeurs[cle.strip()] = valeur.strip()
    return valeurs


def _masquee(valeurs: dict[str, str]) -> bool:
    return (
        valeurs.get("Hidden", "").lower() == "true"
        or valeurs.get("X-GNOME-Autostart-enabled", "").lower() == "false"
    )


def _ecrire(chemin: Path, lignes: list[str]) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text("\n".join(["[Desktop Entry]", *lignes]) + "\n", encoding="utf-8")


def _commande_clone() -> list[str]:
    return [sys.executable, "-m", "piperread_gui.app"]


# --- Windows : registre, remplaçable dans les tests ---


class _RegistreWindows:
    def lire(self, cle: str, nom: str):
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cle) as poignee:
                return winreg.QueryValueEx(poignee, nom)[0]
        except FileNotFoundError:
            return None

    def ecrire(self, cle: str, nom: str, valeur: str) -> None:
        import winreg

        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, cle) as poignee:
            winreg.SetValueEx(poignee, nom, 0, winreg.REG_SZ, valeur)

    def supprimer(self, cle: str, nom: str) -> None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, cle, 0, winreg.KEY_SET_VALUE) as poignee:
                winreg.DeleteValue(poignee, nom)
        except FileNotFoundError:
            pass


registre = _RegistreWindows()


def _commande_windows() -> str:
    return f'"{Path(sys.executable).resolve()}"'


def _windows_desapprouve() -> bool:
    donnees = registre.lire(CLE_APPROBATION, NOM_VALEUR_WINDOWS)
    return bool(donnees) and donnees[0] % 2 == 1


def _windows_est_active() -> bool:
    return registre.lire(CLE_RUN, NOM_VALEUR_WINDOWS) is not None and not _windows_desapprouve()


def _windows_activer() -> None:
    registre.ecrire(CLE_RUN, NOM_VALEUR_WINDOWS, _commande_windows())
    registre.supprimer(CLE_APPROBATION, NOM_VALEUR_WINDOWS)


def _windows_desactiver() -> None:
    registre.supprimer(CLE_RUN, NOM_VALEUR_WINDOWS)
    registre.supprimer(CLE_APPROBATION, NOM_VALEUR_WINDOWS)


def _windows_corriger_chemin() -> None:
    valeur = registre.lire(CLE_RUN, NOM_VALEUR_WINDOWS)
    if valeur is not None and valeur != _commande_windows():
        registre.ecrire(CLE_RUN, NOM_VALEUR_WINDOWS, _commande_windows())


# --- Interface commune ---


def est_active() -> bool:
    if sys.platform == "win32":
        return _windows_est_active()
    utilisateur = entree_utilisateur()
    if utilisateur.is_file():
        return not _masquee(_lire_entree(utilisateur))
    return ENTREE_SYSTEME.is_file()


def activer(icone: Path | None = None) -> None:
    if sys.platform == "win32":
        _windows_activer()
        return
    utilisateur = entree_utilisateur()
    if ENTREE_SYSTEME.is_file():
        utilisateur.unlink(missing_ok=True)
        return
    lignes = [
        "Type=Application",
        "Name=PiperRead",
        "Comment=Read the selected text aloud, from the notification area",
        "Exec=" + " ".join(_argument_exec(a) for a in _commande_clone()),
        "Terminal=false",
        "X-GNOME-Autostart-enabled=true",
    ]
    if icone is not None:
        lignes.insert(3, f"Icon={icone}")
    _ecrire(utilisateur, lignes)


def desactiver() -> None:
    if sys.platform == "win32":
        _windows_desactiver()
        return
    _ecrire(
        entree_utilisateur(),
        ["Type=Application", "Name=PiperRead", "Exec=piperread-gui", "Hidden=true"],
    )


def appliquer_defaut_premier_lancement(icone: Path | None = None) -> bool:
    if sys.platform == "win32":
        _windows_corriger_chemin()
    marqueur = dossier_etat() / NOM_MARQUEUR
    if marqueur.exists():
        return False
    if not est_active():
        activer(icone)
    marqueur.parent.mkdir(parents=True, exist_ok=True)
    marqueur.touch()
    return True

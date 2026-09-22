"""
i18n.py — charge les mêmes fichiers `lang/*.txt` que le noyau, avec les clés propres à l'interface.

Pourquoi ce fichier existe :
    Décision arbitrée dans `CONCEPTION_PIPERREAD.md`, fiche « interface
    graphique » : l'interface lit les mêmes fichiers `lang/*.txt` que
    `read.sh` (mêmes clés existantes, plus les libellés de menu, l'info-bulle
    du tray et les textes de notification propres à l'interface). L'anglais
    est chargé en premier pour combler toute clé absente d'une autre langue —
    même règle que `load_messages` de `read.sh`.

Entrée / sortie :
    Entrée : un code de langue (`en`, `fr`, `de`, `es`). Sortie : le
    dictionnaire fusionné des messages, et `msg()` pour substituer `{1}`,
    `{2}`, `{3}` dans un message.

Dépend de :
    `flatfile.py` ; `<racine du dépôt>/lang/*.txt` du clone en priorité, sinon
    `/usr/lib/piperread/lang/` du paquet noyau installé (`piperread-gui` en
    dépend), même logique de résolution que `server.py` pour l'interpréteur
    du moteur. Sur l'exécutable Windows gelé, `frozen.installation_dir` (le
    dossier réel de `piperread-gui.exe`) remplace le dépôt cloné comme
    racine candidate — `Path(__file__)` y pointerait vers un dossier
    d'extraction temporaire, jamais vers l'installation.
"""

from pathlib import Path

from piperread_gui import frozen
from piperread_gui.flatfile import read_flat_file

_REPO_ROOT = frozen.installation_dir() or Path(__file__).resolve().parent.parent.parent


_LANG_DIR_INSTALLEE = Path("/usr/lib/piperread/lang")


def _lang_dir() -> Path:
    candidat = _REPO_ROOT / "lang"
    return candidat if candidat.is_dir() else _LANG_DIR_INSTALLEE


def load_messages(lang: str) -> dict[str, str]:
    messages = read_flat_file(_lang_dir() / "en.txt")
    if lang != "en":
        messages.update(read_flat_file(_lang_dir() / f"{lang}.txt"))
    return messages


def msg(messages: dict[str, str], key: str, *args: str) -> str:
    texte = messages.get(key, key)
    for indice, valeur in enumerate(args, start=1):
        texte = texte.replace(f"{{{indice}}}", str(valeur))
    return texte

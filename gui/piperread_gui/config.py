"""
config.py — résout et écrit les réglages de `piperread.conf`, à l'identique de `utils/config.sh`.

Pourquoi ce fichier existe :
    Le noyau et l'interface lisent le même fichier de configuration, les mêmes
    clés (`speed`, `voice`, `lang`) et le même ordre de priorité (option de
    ligne de commande > variable d'environnement > fichier > défaut) — décision
    arbitrée dans `CONCEPTION_PIPERREAD.md`, fiche « interface graphique ».
    Port Python fidèle de `utils/config.sh`, jamais un import du script Bash :
    aucun code n'est partagé entre les deux processus, seul le format l'est.
    Ce fichier ajoute l'écriture (`write_config_values`), absente côté noyau
    puisque `read.sh` ne modifie jamais son propre fichier de configuration.

Entrée / sortie :
    Entrée : les options de ligne de commande de l'appelant, les variables
    `PIPERREAD_SPEED`/`PIPERREAD_VOICE`/`PIPERREAD_LANG`, le fichier
    `$XDG_CONFIG_HOME/piperread/piperread.conf`. Sortie : `resolve_settings`
    rend la vitesse, la voix et la langue effectives, avec leur source et les
    avertissements des niveaux écartés ; `write_config_values` réécrit
    uniquement les clés fournies, en conservant le reste du fichier.

Dépend de :
    `flatfile.py` (lecture sans exécution).
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from piperread_gui.flatfile import read_flat_file

KNOWN_KEYS = ("speed", "voice", "lang")
LANGS = ("en", "fr", "de", "es")

_CLE_VALIDE = re.compile(r"[a-z][a-z_]*")
_NOM_VOIX_VALIDE = re.compile(r"[A-Za-z0-9_.-]+")


def config_file_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "piperread" / "piperread.conf"


def default_voices_dir(repo_root: Path) -> Path:
    candidat = repo_root / "voices"
    if candidat.is_dir():
        return candidat
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "piperread" / "voices"


def load_config_file() -> tuple[dict[str, str], list[str]]:
    brut = read_flat_file(config_file_path())
    valeurs: dict[str, str] = {}
    inconnues: list[str] = []
    for cle, valeur in brut.items():
        if cle in KNOWN_KEYS:
            valeurs[cle] = valeur.replace("\r", "").strip()
        else:
            inconnues.append(cle)
    return valeurs, inconnues


def normalize_speed(value: str) -> str | None:
    texte = value.replace(",", ".")
    if not re.fullmatch(r"[0-9]+(\.[0-9]+)?", texte):
        return None
    vitesse = float(texte)
    if vitesse < 0.5 or vitesse > 3.0:
        return None
    return texte


def speed_to_length_scale(speed: float) -> float:
    return 1 / speed


def valid_lang(value: str) -> str | None:
    return value if value in LANGS else None


def valid_voice_name(value: str) -> bool:
    return bool(_NOM_VOIX_VALIDE.fullmatch(value))


def validate_voice(value: str, voices_dir: Path) -> str | None:
    if not valid_voice_name(value):
        return None
    if (voices_dir / f"{value}.onnx").is_file():
        return value
    return None


def default_voice_name(voices_dir: Path) -> str | None:
    modeles = sorted(p.stem for p in voices_dir.glob("*.onnx") if p.is_file())
    return modeles[0] if modeles else None


@dataclass
class Resolved:
    value: str | None = None
    source: str = "default"
    warnings: list[tuple[str, str, str]] = field(default_factory=list)
    invalid: tuple[str, str, str] | None = None


def resolve_setting(
    key: str,
    validator: Callable[[str], str | None],
    option_value: str | None,
    config_values: dict[str, str],
) -> Resolved:
    warnings: list[tuple[str, str, str]] = []
    niveaux = (
        ("option", option_value, f"--{key}"),
        ("environment", os.environ.get(f"PIPERREAD_{key.upper()}"), f"PIPERREAD_{key.upper()}"),
        ("file", config_values.get(key), "piperread.conf"),
    )
    for niveau, valeur_brute, source in niveaux:
        if not valeur_brute:
            continue
        normalisee = validator(valeur_brute)
        if normalisee is not None:
            return Resolved(value=normalisee, source=source, warnings=warnings)
        if niveau == "option":
            return Resolved(warnings=warnings, invalid=(key, valeur_brute, source))
        warnings.append((key, valeur_brute, source))
    return Resolved(warnings=warnings)


@dataclass
class ResolvedSettings:
    speed: float
    speed_source: str
    voice: str | None
    voice_source: str
    model_path: Path | None
    lang: str
    lang_source: str
    warnings: list[tuple[str, str, str]]
    unknown_keys: list[str]
    invalid: tuple[str, str, str] | None


def resolve_settings(
    voices_dir: Path,
    speed_option: str | None = None,
    voice_option: str | None = None,
    lang_option: str | None = None,
) -> ResolvedSettings:
    config_values, unknown_keys = load_config_file()
    invalid: tuple[str, str, str] | None = None
    warnings: list[tuple[str, str, str]] = []

    lang_resolved = resolve_setting("lang", valid_lang, lang_option, config_values)
    warnings += lang_resolved.warnings
    if lang_resolved.invalid is not None:
        invalid = lang_resolved.invalid
    lang = lang_resolved.value
    lang_source = lang_resolved.source
    if not lang:
        repli = valid_lang(os.environ.get("LANG", "").split("_", 1)[0])
        lang = repli or "en"
        lang_source = "default"

    speed_resolved = resolve_setting("speed", normalize_speed, speed_option, config_values)
    warnings += speed_resolved.warnings
    if invalid is None and speed_resolved.invalid is not None:
        invalid = speed_resolved.invalid
    speed = float(speed_resolved.value) if speed_resolved.value else 1.0

    voice_resolved = resolve_setting(
        "voice", lambda valeur: validate_voice(valeur, voices_dir), voice_option, config_values
    )
    warnings += voice_resolved.warnings
    if invalid is None and voice_resolved.invalid is not None:
        invalid = voice_resolved.invalid
    voice_name = voice_resolved.value or default_voice_name(voices_dir)
    model_path = voices_dir / f"{voice_name}.onnx" if voice_name else None

    return ResolvedSettings(
        speed=speed,
        speed_source=speed_resolved.source,
        voice=voice_name,
        voice_source=voice_resolved.source,
        model_path=model_path,
        lang=lang,
        lang_source=lang_source,
        warnings=warnings,
        unknown_keys=unknown_keys,
        invalid=invalid,
    )


def write_config_values(values: dict[str, str]) -> None:
    chemin = config_file_path()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    try:
        chemin.parent.chmod(0o700)
    except OSError:
        pass

    lignes = chemin.read_text(encoding="utf-8").splitlines() if chemin.exists() else []
    a_ecrire = dict(values)

    for cle, valeur in values.items():
        derniere_position = None
        for position, ligne in enumerate(lignes):
            cle_ligne = ligne.split("=", 1)[0] if "=" in ligne else ligne
            if _CLE_VALIDE.fullmatch(cle_ligne) and cle_ligne == cle:
                derniere_position = position
        if derniere_position is not None:
            lignes[derniere_position] = f"{cle}={valeur}"
            del a_ecrire[cle]

    for cle, valeur in a_ecrire.items():
        lignes.append(f"{cle}={valeur}")

    chemin.write_text("\n".join(lignes) + "\n", encoding="utf-8")

#!/bin/bash
# diagnose.sh — vérifie l'installation et dit tout ce qui ne va pas.
#
# Pourquoi ce fichier existe :
#     Une lecture lancée par un raccourci clavier échoue sans que personne ne le
#     voie. Le diagnostic va jusqu'au bout au lieu de s'arrêter au premier
#     échec, ne joue aucun son et ne lit jamais le presse-papiers : il ne doit
#     rien révéler ni déranger, y compris dans un conteneur sans écran ni carte
#     son, où ces absences sont des avertissements.
#
# Usage :
#     Charger ce fichier après read.sh (msg, alert, runtime_dir, read_voice_rate,
#     VENV_PATH, MODEL_PATH, VOICES_DIR, SETTING_WARNINGS, CONFIG_UNKNOWN_KEYS),
#     puis run_diagnose. Chaque check_* affiche ses lignes et laisse son pire
#     statut (ok, warning ou fail) dans CHECK_STATUS. run_diagnose rend 1 s'il y
#     a au moins un échec, sinon 0.
#
# Dépend de : utils/config.sh (config_file_path), aplay, python du moteur.

DIAG_FAILURES=0
DIAG_WARNINGS=0
CHECK_STATUS="ok"

# finding <statut> <clé du contrôle> <clé du détail> [arguments du détail]
finding() {
    local status="$1" title="$2" detail="$3"
    shift 3
    case "$status" in
        fail) DIAG_FAILURES=$((DIAG_FAILURES + 1)); CHECK_STATUS="fail" ;;
        warning) DIAG_WARNINGS=$((DIAG_WARNINGS + 1)); [ "$CHECK_STATUS" == "fail" ] || CHECK_STATUS="warning" ;;
    esac
    printf '[%s] %s : %s\n' "$(msg "diag_status_$status")" "$(msg "$title")" "$(msg "$detail" "$@")"
}

check_engine() {
    local version
    CHECK_STATUS="ok"
    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        finding fail diag_title_engine venv_missing "$VENV_PATH"
        return
    fi
    if version=$("$VENV_PATH/bin/python3" -c 'import importlib.metadata as m, piper; print(m.version("piper-tts"))' 2>/dev/null); then
        finding ok diag_title_engine diag_engine_ok "$version" "$VENV_PATH"
    else
        finding fail diag_title_engine diag_engine_import_failed "$VENV_PATH"
    fi
}

check_voice() {
    local rate
    CHECK_STATUS="ok"
    if [ -z "$MODEL_PATH" ] || [ ! -f "$MODEL_PATH" ]; then
        finding fail diag_title_voice voice_missing
        return
    fi
    if rate=$(read_voice_rate "$MODEL_PATH"); then
        finding ok diag_title_voice diag_voice_ok "$(basename "$MODEL_PATH" .onnx)" "$rate"
    else
        finding warning diag_title_voice rate_unreadable
    fi
}

# aplay -l liste les cartes sans rien jouer.
check_player() {
    local cards
    CHECK_STATUS="ok"
    if ! command -v aplay &> /dev/null; then
        finding fail diag_title_player dependency_missing aplay
        return
    fi
    cards=$(LC_ALL=C aplay -l 2>/dev/null | grep -c '^card')
    if [ "$cards" -gt 0 ]; then
        finding ok diag_title_player diag_player_ok "$cards"
    else
        finding warning diag_title_player diag_player_no_card
    fi
}

check_tools() {
    local tool
    CHECK_STATUS="ok"
    for tool in setsid flock; do
        if command -v "$tool" &> /dev/null; then
            finding ok diag_title_tools diag_tool_ok "$tool"
        else
            finding fail diag_title_tools dependency_missing "$tool"
        fi
    done
}

# Seule la présence de l'outil est testée : le contenu du presse-papiers n'est jamais lu.
check_clipboard() {
    local tool
    CHECK_STATUS="ok"
    if command -v wl-paste &> /dev/null; then
        tool="wl-paste"
    elif command -v xsel &> /dev/null; then
        tool="xsel"
    else
        finding fail diag_title_clipboard dependency_missing "wl-paste / xsel"
        return
    fi
    finding ok diag_title_clipboard diag_tool_ok "$tool"
    if [ -z "$WAYLAND_DISPLAY" ] && [ -z "$DISPLAY" ]; then
        finding warning diag_title_clipboard diag_clipboard_no_session
    fi
}

check_config() {
    local file i key value source
    CHECK_STATUS="ok"
    file=$(config_file_path)
    if [ -r "$file" ]; then
        finding ok diag_title_config diag_config_ok "$file"
    else
        finding ok diag_title_config diag_config_defaults
    fi
    for key in "${CONFIG_UNKNOWN_KEYS[@]}"; do
        finding warning diag_title_config diag_config_unknown_key "$key"
    done
    for ((i = 0; i < ${#SETTING_WARNINGS[@]}; i += 3)); do
        key="${SETTING_WARNINGS[i]}"
        value="${SETTING_WARNINGS[i+1]}"
        source="${SETTING_WARNINGS[i+2]}"
        if [ "$key" == "voice" ] && [ -n "$MODEL_PATH" ]; then
            finding warning diag_title_config voice_fallback "$value" "$source" "$(basename "$MODEL_PATH" .onnx)"
        else
            finding warning diag_title_config setting_invalid "$key" "$value" "$source"
        fi
    done
}

# runtime_dir prévient par notification quand il refuse : ici le refus est un
# résultat du diagnostic, pas une alerte.
check_runtime() {
    local dir expected
    CHECK_STATUS="ok"
    if dir=$(alert() { :; }; runtime_dir); then
        finding ok diag_title_runtime diag_runtime_ok "$dir"
    else
        expected="${XDG_RUNTIME_DIR:+$XDG_RUNTIME_DIR/piperread}"
        finding fail diag_title_runtime runtime_dir_refused "${expected:-/tmp/piperread-$UID}"
    fi
}

run_diagnose() {
    local check
    for check in check_engine check_voice check_player check_tools check_clipboard check_config check_runtime; do
        "$check"
    done
    msg diag_summary "$DIAG_FAILURES" "$DIAG_WARNINGS"
    [ "$DIAG_FAILURES" -eq 0 ]
}

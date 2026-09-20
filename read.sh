#!/bin/bash

# read.sh — lit à voix haute le texte sélectionné ou copié, avec le moteur Piper.
#
# Pourquoi ce fichier existe :
#     Écouter un texte sans le confier à un service en ligne : la synthèse est
#     neuronale et entièrement locale, et le texte est pris dans la sélection
#     ou le presse-papiers, sous Wayland comme sous X11.
#
# Usage :
#     read.sh [auto|selection|clipboard]
#     auto (défaut) lit la sélection à la souris, à défaut le presse-papiers.
#
# Dépend de : utils/cleaner.sh, utils/flatfile.sh, lang/ (messages), piper-env/
#     (moteur), voices/ (voix .onnx), wl-paste ou xsel, aplay, notify-send.

VERSION="0.1.2-alpha"
APP_NAME="PiperRead"

# --- CONFIGURATION DYNAMIQUE ---
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Première voix par ordre alphabétique : celle que l'installation a téléchargée,
# quelle que soit la langue.
MODEL_PATH=""
for voice in "$BASE_DIR"/voices/*.onnx; do
    if [ -f "$voice" ]; then MODEL_PATH="$voice"; break; fi
done
if [ -z "$MODEL_PATH" ]; then MODEL_PATH="$BASE_DIR/voices/fr_FR-siwis-medium.onnx"; fi
VENV_PATH="$BASE_DIR/piper-env"

# --- NETTOYAGE ---
cleanup() {
    if [ -n "$VIRTUAL_ENV" ]; then deactivate; fi
}
trap cleanup SIGINT SIGTERM EXIT

# --- NETTOYAGE MARKDOWN ---
source "$BASE_DIR/utils/cleaner.sh"

# --- MESSAGES ---
source "$BASE_DIR/utils/flatfile.sh"
declare -A MSG

# L'anglais est chargé d'abord : il comble toute clé absente d'une autre langue.
load_messages() {
    local lang="${LANG%%_*}"
    read_flat_file "$BASE_DIR/lang/en.txt" MSG
    if [[ "$lang" =~ ^[a-z]{2}$ && "$lang" != "en" ]]; then
        read_flat_file "$BASE_DIR/lang/$lang.txt" MSG
    fi
}

msg() {
    local text="${MSG[$1]:-$1}"
    echo "${text//\{1\}/"$2"}"
}

alert() {
    local text
    text=$(msg "$@")
    if command -v notify-send &> /dev/null; then
        notify-send "$APP_NAME" "$text"
    else
        echo "$APP_NAME : $text" >&2
    fi
}

load_messages

# --- GESTION PRESSE-PAPIERS (Wayland & X11) ---
get_clipboard() {
    local mode="$1"
    local content=""
    
    # 1. Tentative Wayland
    if command -v wl-paste &> /dev/null; then
        if [ "$mode" == "primary" ]; then
            content=$(wl-paste --primary --no-newline 2>/dev/null)
        else
            content=$(wl-paste --no-newline 2>/dev/null)
        fi
        if [ -n "$content" ]; then
            echo "$content"
            return 0
        fi
    fi
    
    # 2. Tentative X11 (si Wayland a échoué ou est indisponible)
    if command -v xsel &> /dev/null; then
        if [ "$mode" == "primary" ]; then
            content=$(xsel --primary --output 2>/dev/null)
        else
            content=$(xsel --clipboard --output 2>/dev/null)
        fi
        if [ -n "$content" ]; then
            echo "$content"
            return 0
        fi
    fi
    
    # 3. Aucun contenu trouvé
    return 1
}

# --- LECTURE AUDIO ---
play_text() {
    local raw_text="$1"
    local text=$(clean_markdown "$raw_text")
    
    # Coupe la parole si relancé
    pkill -f "aplay -r 22050" 2>/dev/null
    
    if [ -z "$text" ]; then return 1; fi

    # Activation environnement virtuel
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
    else
        alert venv_missing "$VENV_PATH"
        exit 1
    fi

    # Synthèse vocale
    echo "$text" | piper --model "$MODEL_PATH" --length_scale 0.8 --output_raw | aplay -r 22050 -f S16_LE -t raw - 2>/dev/null
}

# --- LOGIQUE INTELLIGENTE ---
MODE="${1:-auto}"
TEXT=""

if [ "$MODE" == "selection" ]; then
    TEXT=$(get_clipboard "primary")
elif [ "$MODE" == "clipboard" ]; then
    TEXT=$(get_clipboard "clipboard")
else
    # Auto : Priorité sélection souris > Sinon presse-papiers
    TEXT=$(get_clipboard "primary")
    if [ -z "$TEXT" ]; then
        TEXT=$(get_clipboard "clipboard")
    fi
fi

if [ -n "$TEXT" ]; then
    play_text "$TEXT"
fi

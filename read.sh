#!/bin/bash

# ==================================================================================
# PROJET     : PiperRead
# VERSION    : 0.1-Alpha
# DESCRIPTION: Orchestrateur de synthèse vocale neuronale locale (Wayland & X11).
#              Lit le texte sélectionné ou le presse-papiers via le moteur Piper.
#
# ARCHITECTE : Ronan Davalan
# CO-PILOTES : Google Gemini, Claude (Anthropic), Perplexity
# LICENCE    : MIT
# DÉPÔT      : https://github.com/RonanDavalan/PiperRead
# SITE WEB   : https://piperread.davalan.fr
# ==================================================================================

# --- CONFIGURATION DYNAMIQUE ---
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MODEL_PATH="$BASE_DIR/voices/fr_FR-siwis-medium.onnx"
VENV_PATH="$BASE_DIR/piper-env"

# --- NETTOYAGE ---
cleanup() {
    if [ -n "$VIRTUAL_ENV" ]; then deactivate; fi
}
trap cleanup SIGINT SIGTERM EXIT

# --- NETTOYAGE MARKDOWN ---
source "$BASE_DIR/utils/cleaner.sh"

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
        notify-send "Erreur PiperRead" "Environnement virtuel introuvable : $VENV_PATH"
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

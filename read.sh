#!/bin/bash

# read.sh — lit à voix haute le texte sélectionné ou copié, avec le moteur Piper.
#
# Pourquoi ce fichier existe :
#     Écouter un texte sans le confier à un service en ligne : la synthèse est
#     neuronale et entièrement locale, et le texte est pris dans la sélection
#     ou le presse-papiers, sous Wayland comme sous X11.
#
# Usage :
#     read.sh [auto|selection|clipboard|--stop]
#     auto (défaut) lit la sélection à la souris, à défaut le presse-papiers.
#     --stop arrête la lecture en cours ; relancer read.sh coupe la précédente.
#
# Dépend de : utils/cleaner.sh, utils/flatfile.sh, lang/ (messages), piper-env/
#     (moteur), voices/ (voix .onnx), wl-paste ou xsel, aplay, setsid, flock,
#     notify-send.

VERSION="0.1.2-alpha"
APP_NAME="PiperRead"

# --- CONFIGURATION DYNAMIQUE ---
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/piperread"

# Un clone fonctionne sans installation : ses dossiers, s'ils existent, passent
# avant ceux d'un paquet, dont le moteur est système et les voix personnelles.
if [ -d "$BASE_DIR/voices" ]; then VOICES_DIR="$BASE_DIR/voices"; else VOICES_DIR="$DATA_DIR/voices"; fi
if [ -d "$BASE_DIR/piper-env" ]; then VENV_PATH="$BASE_DIR/piper-env"; else VENV_PATH="/usr/lib/piperread/venv"; fi

# Première voix par ordre alphabétique : celle que l'installation a téléchargée,
# quelle que soit la langue.
MODEL_PATH=""
for voice in "$VOICES_DIR"/*.onnx; do
    if [ -f "$voice" ]; then MODEL_PATH="$voice"; break; fi
done

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

# --- DOSSIER D'EXECUTION ---
# Sous /tmp le chemin est prévisible : un dossier ou un lien posé à l'avance par
# un autre utilisateur ferait écrire l'identifiant de groupe chez lui.
runtime_dir() {
    local dir
    if [ -n "$XDG_RUNTIME_DIR" ]; then
        dir="$XDG_RUNTIME_DIR/piperread"
    else
        dir="/tmp/piperread-$UID"
    fi
    if [ ! -e "$dir" ] && [ ! -L "$dir" ]; then mkdir -m 700 -- "$dir" 2>/dev/null; fi
    if [ -L "$dir" ] || [ ! -d "$dir" ] || [ "$(stat -c '%u %a' -- "$dir")" != "$UID 700" ]; then
        alert runtime_dir_refused "$dir"
        return 1
    fi
    echo "$dir"
}

check_dependencies() {
    local dep
    for dep in aplay setsid flock; do
        if ! command -v "$dep" &> /dev/null; then alert dependency_missing "$dep"; exit 1; fi
    done
    if ! command -v wl-paste &> /dev/null && ! command -v xsel &> /dev/null; then
        alert dependency_missing "wl-paste / xsel"
        exit 1
    fi
}

# --- TAUX D'ECHANTILLONNAGE ---
# Les voix de Piper vont de 16 000 à 44 100 Hz : jouées à un autre taux, elles
# sortent trop rapides ou trop lentes.
voice_rate() {
    local rate
    rate=$(sed -n 's/.*"sample_rate": *\([0-9][0-9]*\).*/\1/p' "$1.json" 2>/dev/null | head -n 1)
    if [[ "$rate" =~ ^[0-9]+$ ]] && [ "$rate" -ge 8000 ] && [ "$rate" -le 48000 ]; then
        echo "$rate"
    else
        alert rate_unreadable
        echo 22050
    fi
}

# --- ARRET ---
# Le verrou fd 9 doit être tenu par l'appelant. L'identifiant n'est utilisé que si
# le processus porte encore la marque du pipeline : un fichier périmé pourrait
# désigner un processus étranger qui a repris le même numéro.
stop_reading() {
    local file="$RUN/group" group
    local -a args
    [ -f "$file" ] || return 1
    group=$(<"$file")
    rm -f "$file"
    [[ "$group" =~ ^[0-9]+$ ]] && [ "$group" -gt 1 ] || return 1
    [ -r "/proc/$group/cmdline" ] || return 1
    mapfile -d '' -t args < "/proc/$group/cmdline"
    [ "${args[3]}" == "piperread-pipeline" ] || return 1
    kill -TERM -- "-$group" 2>/dev/null
}

# --- LECTURE AUDIO ---
play_text() {
    local raw_text="$1"
    local text=$(clean_markdown "$raw_text")
    local rate pid

    RUN=$(runtime_dir) || exit 1
    exec 9>"$RUN/lock"
    flock 9

    # Coupe la parole si relancé
    stop_reading

    if [ -z "$text" ]; then exec 9>&-; return 1; fi

    if [ -z "$MODEL_PATH" ]; then alert voice_missing; exit 1; fi
    rate=$(voice_rate "$MODEL_PATH")

    # Activation environnement virtuel
    if [ -f "$VENV_PATH/bin/activate" ]; then
        source "$VENV_PATH/bin/activate"
    else
        alert venv_missing "$VENV_PATH"
        exit 1
    fi

    # Synthèse vocale dans son propre groupe : un signal au groupe n'atteint ni
    # le terminal lanceur ni un autre lecteur audio. Le verrou est fermé pour le
    # pipeline, sinon il le tiendrait jusqu'à la fin de la lecture.
    setsid bash -c 'piper --model "$1" --length_scale 0.8 --output_raw | aplay -r "$2" -f S16_LE -t raw - 2>/dev/null' \
        piperread-pipeline "$MODEL_PATH" "$rate" 9>&- <<< "$text" &
    pid=$!
    echo "$pid" > "$RUN/group.$pid" && mv -f "$RUN/group.$pid" "$RUN/group"
    exec 9>&-

    wait "$pid"

    # Ne retire le fichier que s'il porte encore cette lecture : une relance a pu
    # le remplacer entre-temps.
    exec 9>"$RUN/lock"
    flock 9
    if [ "$(cat "$RUN/group" 2>/dev/null)" == "$pid" ]; then rm -f "$RUN/group"; fi
    exec 9>&-
}

# --- LOGIQUE INTELLIGENTE ---
MODE="${1:-auto}"
TEXT=""

case "$MODE" in
    --stop)
        RUN=$(runtime_dir) || exit 1
        exec 9>"$RUN/lock"
        flock 9
        if stop_reading; then alert stopped; else alert nothing_to_stop; fi
        exit 0
        ;;
    auto|selection|clipboard) ;;
    *)
        alert unknown_option "$MODE"
        exit 2
        ;;
esac

check_dependencies

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
else
    alert no_text
fi

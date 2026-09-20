#!/bin/bash

# read.sh — lit à voix haute le texte sélectionné ou copié, avec le moteur Piper.
#
# Pourquoi ce fichier existe :
#     Écouter un texte sans le confier à un service en ligne : la synthèse est
#     neuronale et entièrement locale, et le texte est pris dans la sélection
#     ou le presse-papiers, sous Wayland comme sous X11.
#
# Usage :
#     read.sh [auto|selection|clipboard] [--speed X] [--voice NOM] [--lang CODE]
#     read.sh --stop | --pause | --resume
#     read.sh --version | --diagnose
#     read.sh --list-voices | --download-voice [NOM...]
#     auto (défaut) lit la sélection à la souris, à défaut le presse-papiers.
#     --speed : multiplicateur de vitesse de 0,5 à 3,0 (1 = voix naturelle).
#     --stop arrête la lecture en cours ; relancer read.sh coupe la précédente.
#     --pause la suspend, --resume la reprend là où elle s'était arrêtée.
#     --diagnose contrôle l'installation (code 1 s'il y a un échec), sans rien lire ni jouer.
#     --list-voices affiche les voix proposées, avec leur licence, sans réseau.
#     --download-voice télécharge les voix nommées ; sans nom, propose celle de la langue.
#     Chaque réglage vient de l'option, sinon de PIPERREAD_SPEED, PIPERREAD_VOICE
#     ou PIPERREAD_LANG, sinon de ~/.config/piperread/piperread.conf.
#
# Dépend de : utils/cleaner.sh, utils/flatfile.sh, utils/config.sh, utils/diagnose.sh, utils/voices.sh,
#     lang/ (messages), piper-env/ (moteur), voices/ (voix .onnx), wl-paste ou xsel, aplay, setsid, flock,
#     notify-send.

VERSION="0.1.2-alpha"
APP_NAME="PiperRead"

# Avant tout le reste : aucun message, aucune dépendance ni dossier touchés.
for arg in "$@"; do
    if [ "$arg" == "--version" ]; then echo "piperread $VERSION"; exit 0; fi
done
unset arg

# --- CONFIGURATION DYNAMIQUE ---
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/piperread"

# Un clone fonctionne sans installation : ses dossiers, s'ils existent, passent
# avant ceux d'un paquet, dont le moteur est système et les voix personnelles.
if [ -d "$BASE_DIR/voices" ]; then VOICES_DIR="$BASE_DIR/voices"; else VOICES_DIR="$DATA_DIR/voices"; fi
if [ -d "$BASE_DIR/piper-env" ]; then VENV_PATH="$BASE_DIR/piper-env"; else VENV_PATH="/usr/lib/piperread/venv"; fi

# --- NETTOYAGE ---
cleanup() {
    if [ -n "$VIRTUAL_ENV" ]; then deactivate; fi
}
trap cleanup EXIT

# La lecture vit dans son propre groupe : sans ce piège, Ctrl-C ne l'atteindrait
# pas et elle continuerait sans que le fichier de suivi la désigne.
PIPELINE_PID=""
interrupt() {
    if [ -n "$PIPELINE_PID" ]; then
        kill -TERM -- "-$PIPELINE_PID" 2>/dev/null || kill -TERM "$PIPELINE_PID" 2>/dev/null
        kill -CONT -- "-$PIPELINE_PID" 2>/dev/null
        if [ "$(cat "$RUN/group" 2>/dev/null)" == "$PIPELINE_PID" ]; then rm -f "$RUN/group"; fi
    fi
    exit "$1"
}
trap 'interrupt 130' SIGINT
trap 'interrupt 143' SIGTERM

# --- NETTOYAGE MARKDOWN ---
source "$BASE_DIR/utils/cleaner.sh"

# --- MESSAGES ---
source "$BASE_DIR/utils/flatfile.sh"
source "$BASE_DIR/utils/config.sh"
source "$BASE_DIR/utils/diagnose.sh"
source "$BASE_DIR/utils/voices.sh"
declare -A MSG

# L'anglais est chargé d'abord : il comble toute clé absente d'une autre langue.
load_messages() {
    local lang="$1"
    read_flat_file "$BASE_DIR/lang/en.txt" MSG
    if [ "$lang" != "en" ]; then
        read_flat_file "$BASE_DIR/lang/$lang.txt" MSG
    fi
}

msg() {
    local text="${MSG[$1]:-$1}"
    text="${text//\{1\}/"$2"}"
    text="${text//\{2\}/"$3"}"
    echo "${text//\{3\}/"$4"}"
}

alert() {
    local text
    text=$(msg "$@")
    echo "$APP_NAME : $text" >&2
    if command -v notify-send &> /dev/null; then notify-send "$APP_NAME" "$text"; fi
}

# --- GESTION PRESSE-PAPIERS (Wayland & X11) ---
# Un contenu fait d'espaces et de retours à la ligne est traité comme vide.
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
        if [[ "$content" =~ [^[:space:]] ]]; then
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
        if [[ "$content" =~ [^[:space:]] ]]; then
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
read_voice_rate() {
    local rate
    rate=$(sed -n 's/.*"sample_rate": *\([0-9][0-9]*\).*/\1/p' "$1.json" 2>/dev/null | head -n 1)
    if [[ "$rate" =~ ^[0-9]+$ ]] && [ "$rate" -ge 8000 ] && [ "$rate" -le 48000 ]; then
        echo "$rate"
    else
        return 1
    fi
}

voice_rate() {
    read_voice_rate "$1" && return 0
    alert rate_unreadable
    echo 22050
}

# --- ARRET, PAUSE ET REPRISE ---
# Le verrou fd 9 doit être tenu par l'appelant. L'identifiant n'est utilisé que si
# le processus porte encore la marque du pipeline : un fichier périmé pourrait
# désigner un processus étranger qui a repris le même numéro.
active_group() {
    local file="$RUN/group" group
    local -a args
    [ -f "$file" ] || return 1
    group=$(<"$file")
    if [[ "$group" =~ ^[0-9]+$ ]] && [ "$group" -gt 1 ] && [ -r "/proc/$group/cmdline" ]; then
        mapfile -d '' -t args < "/proc/$group/cmdline"
        if [ "${args[3]}" == "piperread-pipeline" ]; then echo "$group"; return 0; fi
    fi
    rm -f "$file"
    return 1
}

# SIGCONT après SIGTERM : un groupe en pause ne traite pas SIGTERM avant d'être repris.
stop_reading() {
    local group
    group=$(active_group) || return 1
    rm -f "$RUN/group"
    kill -TERM -- "-$group" 2>/dev/null
    kill -CONT -- "-$group" 2>/dev/null
}

pause_reading() {
    local group
    group=$(active_group) || return 1
    kill -STOP -- "-$group" 2>/dev/null
}

resume_reading() {
    local group
    group=$(active_group) || return 1
    kill -CONT -- "-$group" 2>/dev/null
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
    setsid bash -c 'piper --model "$1" --length-scale "$3" --output_raw | aplay -r "$2" -f S16_LE -t raw - 2>/dev/null' \
        piperread-pipeline "$MODEL_PATH" "$rate" "$LENGTH_SCALE" 9>&- <<< "$text" &
    pid=$!
    PIPELINE_PID="$pid"
    echo "$pid" > "$RUN/group.$pid" && mv -f "$RUN/group.$pid" "$RUN/group"
    exec 9>&-

    wait "$pid"
    PIPELINE_PID=""

    # Ne retire le fichier que s'il porte encore cette lecture : une relance a pu
    # le remplacer entre-temps.
    exec 9>"$RUN/lock"
    flock 9
    if [ "$(cat "$RUN/group" 2>/dev/null)" == "$pid" ]; then rm -f "$RUN/group"; fi
    exec 9>&-
}

# --- ARGUMENTS ---
PARSE_ERROR=""
parse_arguments() {
    local name
    MODE="auto"
    while [ $# -gt 0 ]; do
        case "$1" in
            --stop|--pause|--resume|--diagnose|--list-voices|auto|selection|clipboard) MODE="$1" ;;
            --download-voice)
                MODE="$1"
                while [ $# -gt 1 ] && [[ "$2" != -* ]]; do DOWNLOAD_NAMES+=("$2"); shift; done
                ;;
            --download-voice=*) MODE="--download-voice"; DOWNLOAD_NAMES+=("${1#*=}") ;;
            --speed|--voice|--lang)
                if [ $# -lt 2 ]; then PARSE_ERROR="missing:$1"; return 1; fi
                OPT_VALUES["${1#--}"]="$2"
                shift
                ;;
            --speed=*|--voice=*|--lang=*)
                name="${1%%=*}"
                OPT_VALUES["${name#--}"]="${1#*=}"
                ;;
            *) PARSE_ERROR="$1"; return 1 ;;
        esac
        shift
    done
}

# --- REGLAGES ---
# Une option invalide refuse la lecture ; une valeur invalide de l'environnement
# ou du fichier prévient et laisse le niveau suivant s'appliquer.
refuse_option() {
    local key="${RESOLVED_INVALID[0]}" value="${RESOLVED_INVALID[1]}" source="${RESOLVED_INVALID[2]}"
    if [ "$key" == "voice" ] && valid_voice_name "$value" > /dev/null; then
        alert voice_not_found "$value"
    else
        alert option_invalid "$source" "$value"
    fi
    exit 2
}

emit_setting_warnings() {
    local i key value source
    for ((i = 0; i < ${#SETTING_WARNINGS[@]}; i += 3)); do
        key="${SETTING_WARNINGS[i]}"
        value="${SETTING_WARNINGS[i+1]}"
        source="${SETTING_WARNINGS[i+2]}"
        if [ "$key" == "voice" ] && [ -n "$MODEL_PATH" ]; then
            alert voice_fallback "$value" "$source" "$(basename "$MODEL_PATH" .onnx)"
        else
            alert setting_invalid "$key" "$value" "$source"
        fi
    done
}

parse_arguments "$@"
load_config_file

resolve_setting lang valid_lang
LANG_STATUS=$?
LANG_CODE="$RESOLVED_VALUE"
if [ -z "$LANG_CODE" ]; then LANG_CODE=$(valid_lang "${LANG%%_*}") || LANG_CODE="en"; fi
load_messages "$LANG_CODE"

if [[ "$PARSE_ERROR" == missing:* ]]; then
    alert option_invalid "${PARSE_ERROR#missing:}" ""
    exit 2
elif [ -n "$PARSE_ERROR" ]; then
    alert unknown_option "$PARSE_ERROR"
    exit 2
fi
if [ "$LANG_STATUS" -eq 2 ]; then refuse_option; fi

resolve_setting speed normalize_speed || refuse_option
LENGTH_SCALE=$(speed_to_length_scale "${RESOLVED_VALUE:-1}")

resolve_setting voice validate_voice || refuse_option
if [ -n "$RESOLVED_VALUE" ]; then
    MODEL_PATH="$VOICES_DIR/$RESOLVED_VALUE.onnx"
else
    MODEL_PATH=$(default_voice) || MODEL_PATH=""
fi
case "$MODE" in
    --diagnose|--list-voices|--download-voice) ;;
    *) emit_setting_warnings ;;
esac

# --- LOGIQUE INTELLIGENTE ---
TEXT=""

case "$MODE" in
    --diagnose)
        run_diagnose
        exit $?
        ;;
    --list-voices)
        list_voices
        exit 0
        ;;
    --download-voice)
        download_voices_command
        exit $?
        ;;
    --stop|--pause|--resume)
        RUN=$(runtime_dir) || exit 1
        exec 9>"$RUN/lock"
        flock 9
        case "$MODE" in
            --stop)   if stop_reading; then alert stopped; else alert nothing_to_stop; fi ;;
            --pause)  if pause_reading; then alert paused; else alert nothing_to_stop; fi ;;
            --resume) if resume_reading; then alert resumed; else alert nothing_to_stop; fi ;;
        esac
        exit 0
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

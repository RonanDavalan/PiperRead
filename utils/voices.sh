#!/bin/bash
# voices.sh — liste les voix proposées et télécharge celles que l'utilisateur choisit.
#
# Pourquoi ce fichier existe :
#     Aucune voix n'est livrée ni téléchargée sans demande : la lecture ne touche
#     jamais le réseau, et le choix d'une voix est personnel. Le catalogue de Piper
#     ne donne pas la licence de ses voix ; elle est écrite ici, pour que
#     l'utilisateur la connaisse avant de télécharger.
#
# Usage :
#     Charger ce fichier après read.sh (msg, alert, VOICES_DIR, VENV_PATH,
#     LANG_CODE), puis list_voices ou download_voices_command. Les noms à
#     télécharger sont dans DOWNLOAD_NAMES ; vide, la voix recommandée de la
#     langue est proposée.
#
# Dépend de : utils/config.sh (valid_voice_name), le module piper.download_voices du
#     moteur, mktemp.

VOICE_LISTEN_URL="https://rhasspy.github.io/piper-samples/"
VOICE_CATALOG_URL="https://huggingface.co/rhasspy/piper-voices"

# nom|langue|taux en Hz|taille en Mo|licence|locuteurs|rang|clé de la remarque
# Rang : recommended (proposée sans nom), alternative, light (16 000 Hz, jamais par défaut).
VOICE_CATALOG=(
    "en_US-ljspeech-medium|en|22050|61|public-domain|1|recommended|"
    "en_US-kristin-medium|en|22050|61|public-domain|1|alternative|"
    "en_GB-alba-medium|en|22050|60|CC-BY 4.0|1|alternative|"
    "en_US-kathleen-low|en|16000|60|CC0|1|light|"
    "fr_FR-siwis-medium|fr|22050|60|CC-BY 4.0|1|recommended|"
    "fr_FR-siwis-low|fr|16000|27|CC-BY 4.0|1|light|voices_note_siwis_low"
    "de_DE-thorsten-medium|de|22050|60|CC0|1|recommended|"
    "de_DE-thorsten-low|de|16000|60|CC0|1|light|"
    "es_ES-davefx-medium|es|22050|60|CC0|1|recommended|"
    "es_ES-sharvard-medium|es|22050|73|CC-BY 3.0|2|alternative|"
    "es_ES-carlfm-x_low|es|16000|27|public-domain|1|light|"
)

DOWNLOAD_NAMES=()
DOWNLOAD_TMP=""
DOWNLOAD_PID=""

voice_entry() {
    local entry
    for entry in "${VOICE_CATALOG[@]}"; do
        if [ "${entry%%|*}" == "$1" ]; then echo "$entry"; return 0; fi
    done
    return 1
}

recommended_voice() {
    local entry name lang rank
    for entry in "${VOICE_CATALOG[@]}"; do
        IFS='|' read -r name lang _ _ _ _ rank _ <<< "$entry"
        if [ "$lang" == "$1" ] && [ "$rank" == "recommended" ]; then echo "$name"; return 0; fi
    done
    return 1
}

voice_installed() {
    [ -s "$VOICES_DIR/$1.onnx" ] && [ -s "$VOICES_DIR/$1.onnx.json" ]
}

voice_license_label() {
    if [ "$1" == "public-domain" ]; then msg license_public_domain; else echo "$1"; fi
}

voice_language_name() {
    case "$1" in
        en) echo "English" ;;
        fr) echo "Français" ;;
        de) echo "Deutsch" ;;
        es) echo "Español" ;;
    esac
}

list_voices() {
    local lang wanted entry name entry_lang rate size license speakers rank note remark line
    local -a remarks

    msg voices_intro
    for lang in en fr de es; do
        echo
        voice_language_name "$lang"
        for wanted in recommended alternative light; do
            for entry in "${VOICE_CATALOG[@]}"; do
                IFS='|' read -r name entry_lang rate size license speakers rank note <<< "$entry"
                if [ "$entry_lang" != "$lang" ] || [ "$rank" != "$wanted" ]; then continue; fi
                remarks=()
                if [ "$rank" != "alternative" ]; then remarks+=("$(msg "voices_$rank")"); fi
                if [ "$speakers" -gt 1 ]; then remarks+=("$(msg voices_speakers "$speakers")"); fi
                if voice_installed "$name"; then remarks+=("$(msg voices_installed)"); fi
                printf -v remark '%s, ' "${remarks[@]}"
                printf -v line '  %-24s %-8s %-9s %-15s %s' \
                    "$name" "$(msg voices_size "$size")" "$rate Hz" "$(voice_license_label "$license")" "${remark%, }"
                echo "${line%"${line##*[![:space:]]}"}"
                if [ -n "$note" ]; then echo "      $(msg "$note")"; fi
            done
        done
    done
    echo
    msg voices_listen "$VOICE_LISTEN_URL"
    msg voices_catalog "$VOICE_CATALOG_URL"
    msg voices_howto
}

# Le module du moteur écrit dans le dossier final et ne rejette qu'un fichier vide :
# un téléchargement coupé y laisserait un modèle tronqué, pris ensuite pour une voix
# installée. Le téléchargement se fait donc à côté, et les fichiers ne sont déplacés
# qu'une fois complets, le modèle en dernier puisque c'est lui que la lecture cherche.
abort_download() {
    if [ -n "$DOWNLOAD_PID" ]; then
        kill "$DOWNLOAD_PID" 2>/dev/null
        wait "$DOWNLOAD_PID" 2>/dev/null
    fi
    if [ -n "$DOWNLOAD_TMP" ]; then rm -rf -- "$DOWNLOAD_TMP"; fi
    exit 130
}

download_voice() {
    local name="$1" entry size license status

    if voice_installed "$name"; then msg download_already "$name"; return 0; fi
    if [ ! -x "$VENV_PATH/bin/python" ]; then alert venv_missing "$VENV_PATH"; return 1; fi

    if entry=$(voice_entry "$name"); then
        IFS='|' read -r _ _ _ size license _ _ _ <<< "$entry"
        msg download_start "$name" "$(msg voices_size "$size")" "$(voice_license_label "$license")"
    else
        msg download_unlisted "$name" "$VOICE_CATALOG_URL"
    fi

    mkdir -p -- "$VOICES_DIR" && DOWNLOAD_TMP=$(mktemp -d "$VOICES_DIR/.download.XXXXXX")
    if [ -z "$DOWNLOAD_TMP" ]; then alert download_failed "$name"; return 1; fi

    trap abort_download INT TERM
    "$VENV_PATH/bin/python" -m piper.download_voices --download-dir "$DOWNLOAD_TMP" "$name" \
        > /dev/null 2> "$DOWNLOAD_TMP/log" &
    DOWNLOAD_PID=$!
    wait "$DOWNLOAD_PID"
    status=$?
    DOWNLOAD_PID=""

    if [ "$status" -eq 0 ] && [ -s "$DOWNLOAD_TMP/$name.onnx" ] && [ -s "$DOWNLOAD_TMP/$name.onnx.json" ] \
        && mv -f -- "$DOWNLOAD_TMP/$name.onnx.json" "$VOICES_DIR/" \
        && mv -f -- "$DOWNLOAD_TMP/$name.onnx" "$VOICES_DIR/"; then
        status=0
    else
        status=1
        tail -n 1 "$DOWNLOAD_TMP/log" >&2
    fi
    rm -rf -- "$DOWNLOAD_TMP"
    DOWNLOAD_TMP=""
    trap cleanup SIGINT SIGTERM

    if [ "$status" -ne 0 ]; then alert download_failed "$name"; return 1; fi
    msg download_done "$name"
}

# Une lecture lancée par un raccourci n'a pas de terminal : la confirmation ne
# peut se demander que dans un terminal.
confirm_download() {
    local name="$1" entry size license answer

    if [ ! -t 0 ]; then alert download_no_terminal; return 2; fi
    entry=$(voice_entry "$name")
    IFS='|' read -r _ _ _ size license _ _ _ <<< "$entry"
    read -r -p "$(msg download_confirm "$name" "$(msg voices_size "$size")" "$(voice_license_label "$license")") " answer
    if [ -n "$answer" ]; then msg download_cancelled; return 1; fi
}

download_voices_command() {
    local name status=0
    local -a names=("${DOWNLOAD_NAMES[@]}")

    if [ ${#names[@]} -eq 0 ]; then
        name=$(recommended_voice "$LANG_CODE")
        if voice_installed "$name"; then msg download_already "$name"; return 0; fi
        confirm_download "$name" || return $?
        names=("$name")
    fi
    for name in "${names[@]}"; do
        if ! valid_voice_name "$name" > /dev/null; then alert option_invalid "--download-voice" "$name"; return 2; fi
    done
    for name in "${names[@]}"; do
        download_voice "$name" || status=1
    done
    return $status
}

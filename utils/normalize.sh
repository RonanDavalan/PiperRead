#!/bin/bash
# normalize.sh — gain par voix qui ramène toutes les voix au même niveau perçu.
#
# Pourquoi ce fichier existe :
#     Piper normalise la crête de chaque phrase à 0 dBFS, mais deux voix de même crête
#     n'ont pas le même niveau perçu : sur les seize voix du poste de mesure, la valeur
#     efficace va de −12 à −21 dBFS. Le gain d'une voix est mesuré une fois, sur une phrase
#     de référence, puis gardé ; il ne dépend que du fichier de la voix.
#
# Usage :
#     Charger ce fichier après read.sh (msg), puis voice_gain <modèle .onnx> : affiche le
#     coefficient à passer à `piper --volume`, rend 1 si la mesure échoue. Le gain amène
#     la valeur efficace à NORMALIZE_TARGET_DB sans dépasser NORMALIZE_MAX_GAIN, soit
#     −1 dBFS de crête une fois la crête de Piper (0 dBFS) multipliée par ce gain.
#     Le fichier de mesures, `$XDG_STATE_HOME/piperread/voice-levels`, porte une ligne par
#     voix (nom, taille, date du fichier, valeur efficace en dBFS) et la même est lue par l'interface.
#
# Dépend de : piper et python3 du moteur ($VENV_PATH), awk, stat.

NORMALIZE_TARGET_DB="-22.2"
NORMALIZE_MAX_GAIN="0.8913"
NORMALIZE_REPEATS=6

declare -A NORMALIZE_REFERENCE=(
    [fr]="Le vieux pont de pierre enjambe la rivière, et les enfants y jouent chaque soir jusqu'à la tombée de la nuit."
    [en]="The old stone bridge crosses the river, and the children play there every evening until nightfall."
    [de]="Die alte Steinbrücke führt über den Fluss, und die Kinder spielen dort jeden Abend bis zur Dämmerung."
    [es]="El viejo puente de piedra cruza el río, y los niños juegan allí cada tarde hasta que cae la noche."
)

valid_normalize() {
    case "$1" in
        on|off) echo "$1" ;;
        *) return 1 ;;
    esac
}

normalize_state_file() {
    echo "${XDG_STATE_HOME:-$HOME/.local/state}/piperread/voice-levels"
}

# Langue de la voix : son champ « language », à défaut sa voix espeak ; l'anglais pour le reste.
voice_language() {
    local json="$1.json" code
    code=$(sed -n 's/.*"code": *"\([a-z][a-z]\)[_-].*/\1/p' "$json" 2>/dev/null | head -n 1)
    [ -n "$code" ] || code=$(sed -n 's/.*"voice": *"\([a-z][a-z]\).*/\1/p' "$json" 2>/dev/null | head -n 1)
    if [ -n "${NORMALIZE_REFERENCE[$code]}" ]; then echo "$code"; else echo "en"; fi
}

# Valeur efficace, en dBFS, de la phrase de référence synthétisée NORMALIZE_REPEATS fois.
measure_voice_level() {
    local model="$1" text="" i
    for ((i = 0; i < NORMALIZE_REPEATS; i++)); do text+="${NORMALIZE_REFERENCE[$(voice_language "$model")]}"$'\n'; done
    printf '%s' "$text" | "$VENV_PATH/bin/piper" --model "$model" --output_raw 2>/dev/null \
        | "$VENV_PATH/bin/python3" -c '
import array, math, sys
echantillons = array.array("h")
echantillons.frombytes(sys.stdin.buffer.read())
if not echantillons:
    sys.exit(1)
energie = sum(x * x for x in echantillons) / len(echantillons)
print("%.2f" % (10 * math.log10(max(energie, 1e-12) / 32768.0 ** 2)))
'
}

# Valeur efficace gardée pour ce fichier de voix, ou mesurée et gardée ; la ligne d'une voix
# dont le fichier a changé (taille ou date) est remplacée.
voice_level() {
    local model="$1" name signature file dir level tmp
    name=$(basename "$model" .onnx)
    signature=$(stat -c '%s %Y' -- "$model" 2>/dev/null) || return 1
    signature="${signature// /$'\t'}"
    file=$(normalize_state_file)
    level=$(LC_ALL=C awk -F '\t' -v n="$name" -v s="$signature" '$1 == n && $2 "\t" $3 == s { print $4; exit }' "$file" 2>/dev/null)
    if [ -n "$level" ]; then echo "$level"; return 0; fi

    alert normalize_measuring "$name"
    level=$(measure_voice_level "$model") && [[ "$level" =~ ^-?[0-9]+(\.[0-9]+)?$ ]] || return 1
    dir=$(dirname "$file")
    mkdir -p -m 700 -- "$dir" || return 1
    tmp=$(mktemp "$dir/voice-levels.XXXXXX") || return 1
    { LC_ALL=C awk -F '\t' -v n="$name" '$1 != n' "$file" 2>/dev/null; printf '%s\t%s\t%s\n' "$name" "$signature" "$level"; } > "$tmp"
    mv -f -- "$tmp" "$file"
    echo "$level"
}

voice_gain() {
    local level
    level=$(voice_level "$1") || { echo 1; return 1; }
    LC_ALL=C awk -v r="$level" -v t="$NORMALIZE_TARGET_DB" -v m="$NORMALIZE_MAX_GAIN" \
        'BEGIN { g = 10 ^ ((t - r) / 20); if (g > m) g = m; printf "%.4f\n", g }'
}

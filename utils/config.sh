#!/bin/bash
# config.sh — résout les réglages : option, variable d'environnement, fichier, défaut.
#
# Pourquoi ce fichier existe :
#     La vitesse, la voix et la langue se règlent de quatre façons ; une valeur
#     invalide ne doit ni exécuter quoi que ce soit ni bloquer une lecture lancée
#     par un raccourci clavier, qui n'a pas de terminal pour en rendre compte.
#
# Usage :
#     Charger ce fichier, puis load_config_file, puis resolve_setting <clé>
#     <validateur> pour speed, voice et lang. Le résultat est dans
#     RESOLVED_VALUE et RESOLVED_SOURCE. Les valeurs de l'utilisateur ne sont
#     jamais évaluées : elles sont comparées à des motifs, puis recopiées.
#
# Dépend de : utils/flatfile.sh (read_flat_file), awk.

declare -A OPT_VALUES
declare -A CONFIG_FILE_VALUES
CONFIG_UNKNOWN_KEYS=()
SETTING_WARNINGS=()
RESOLVED_VALUE=""
RESOLVED_SOURCE="default"
RESOLVED_INVALID=()

# Vitesse en multiplicateur : de 0,5 à 3,0, point ou virgule. Affiche la valeur
# normalisée (point). LC_ALL=C : sous une locale à virgule, awk pourrait lire ou
# écrire « 1,25 » autrement que « 1.25 ».
normalize_speed() {
    local value="${1//,/.}"
    [[ "$value" =~ ^[0-9]+(\.[0-9]+)?$ ]] || return 1
    LC_ALL=C awk -v s="$value" 'BEGIN { if (s + 0 < 0.5 || s + 0 > 3.0) exit 1; print s + 0 }'
}

# Piper mesure une durée : 1 divisé par la vitesse.
speed_to_length_scale() {
    LC_ALL=C awk -v s="$1" 'BEGIN { printf "%.4f\n", 1 / s }'
}

valid_voice_name() {
    [[ "$1" =~ ^[A-Za-z0-9_.-]+$ ]] && echo "$1"
}

valid_lang() {
    case "$1" in
        en|fr|de|es) echo "$1" ;;
        *) return 1 ;;
    esac
}

valid_telemetry() {
    case "$1" in
        on|off) echo "$1" ;;
        *) return 1 ;;
    esac
}

# Chemin du modèle d'un nom déjà validé, dans l'ordre de VOICES_DIRS : à nom
# égal, la voix du clone l'emporte.
find_voice() {
    local dir
    for dir in "${VOICES_DIRS[@]}"; do
        if [ -f "$dir/$1.onnx" ]; then echo "$dir/$1.onnx"; return 0; fi
    done
    return 1
}

# Un nom de voix n'est accepté que si le modèle existe dans l'un des dossiers des voix.
validate_voice() {
    valid_voice_name "$1" > /dev/null && find_voice "$1" > /dev/null && echo "$1"
}

# Première voix par ordre alphabétique, tous dossiers confondus : celle que
# l'installation a téléchargée, quelle que soit la langue.
default_voice() {
    local dir voice name first=""
    for dir in "${VOICES_DIRS[@]}"; do
        for voice in "$dir"/*.onnx; do
            [ -f "$voice" ] || continue
            name=$(basename "$voice" .onnx)
            if [ -z "$first" ] || [[ "$name" < "$first" ]]; then first="$name"; fi
        done
    done
    [ -n "$first" ] && find_voice "$first"
}

config_file_path() {
    echo "${XDG_CONFIG_HOME:-$HOME/.config}/piperread/piperread.conf"
}

load_config_file() {
    local file
    local -A raw=()
    local key value

    file=$(config_file_path)
    CONFIG_FILE_VALUES=()
    CONFIG_UNKNOWN_KEYS=()
    read_flat_file "$file" raw || return 0
    for key in "${!raw[@]}"; do
        value="${raw[$key]//$'\r'/}"
        value="${value#"${value%%[![:space:]]*}"}"
        value="${value%"${value##*[![:space:]]}"}"
        case "$key" in
            speed|voice|lang|telemetry) CONFIG_FILE_VALUES["$key"]="$value" ;;
            *) CONFIG_UNKNOWN_KEYS+=("$key") ;;
        esac
    done
}

# Rend 0 avec le premier niveau valide ; une valeur vide est absente. Une option
# invalide rend 2 et remplit RESOLVED_INVALID (clé, valeur, source) ; une valeur
# invalide d'un autre niveau est mise de côté dans SETTING_WARNINGS (clé, valeur
# et source, par groupes de trois) et le niveau suivant est essayé. Sans aucun niveau valide,
# RESOLVED_VALUE reste vide : l'appelant applique le défaut.
resolve_setting() {
    local key="$1" validator="$2"
    local level value source variable normalized

    RESOLVED_VALUE=""
    RESOLVED_SOURCE="default"
    for level in option environment file; do
        case "$level" in
            option)
                [[ -v OPT_VALUES[$key] ]] || continue
                value="${OPT_VALUES[$key]}"
                source="--$key"
                ;;
            environment)
                variable="PIPERREAD_${key^^}"
                value="${!variable}"
                [ -n "$value" ] || continue
                source="$variable"
                ;;
            file)
                value="${CONFIG_FILE_VALUES[$key]}"
                [ -n "$value" ] || continue
                source="piperread.conf"
                ;;
        esac
        if normalized=$("$validator" "$value"); then
            RESOLVED_VALUE="$normalized"
            RESOLVED_SOURCE="$source"
            return 0
        fi
        if [ "$level" == "option" ]; then
            RESOLVED_INVALID=("$key" "$value" "$source")
            return 2
        fi
        SETTING_WARNINGS+=("$key" "$value" "$source")
    done
    return 0
}

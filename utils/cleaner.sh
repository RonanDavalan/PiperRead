#!/bin/bash
# utils/cleaner.sh - Nettoyage Markdown pour PiperRead

clean_markdown() {
    local input="$1"
    echo "$input" | sed -E \
        -e 's/!\[.*\]\(.*\)//g' \
        -e 's/\[(.*)\]\(.*\)/\1/g' \
        -e 's/(\*\*|__|\*|_|`)//g' \
        -e 's/^#+ //g' \
        -e 's/^[[:space:]]*[-*+][[:space:]]//g' \
        -e 's/^>[[:space:]]?//g'
}
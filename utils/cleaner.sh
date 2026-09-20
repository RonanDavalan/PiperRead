#!/bin/bash
# cleaner.sh — retire le balisage Markdown d'un texte avant sa lecture à voix haute.
#
# Pourquoi ce fichier existe :
#     Le moteur vocal prononcerait les symboles (dièses, astérisques, crochets).
#     Le texte copié depuis une page ou un éditeur doit lui arriver sans eux.
#
# Usage :
#     Charger ce fichier, puis appeler clean_markdown "<texte>" ; le texte nettoyé
#     sort sur la sortie standard.

clean_markdown() {
    local input="$1"
    # Un marqueur d'emphase n'est retiré que s'il entoure un mot : ma_variable
    # et 2*3 restent intacts. Les expressions sont répétées : un marqueur fermant
    # consommé par une correspondance ne peut pas ouvrir la suivante.
    echo "$input" | sed -E \
        -e 's/!\[.*\]\(.*\)//g' \
        -e 's/\[(.*)\]\(.*\)/\1/g' \
        -e 's/`//g' \
        -e 's/(^|[^[:alnum:]*])\*\*([^*[:space:]]([^*]*[^*[:space:]])?)\*\*([^[:alnum:]*]|$)/\1\2\4/g' \
        -e 's/(^|[^[:alnum:]*])\*([^*[:space:]]([^*]*[^*[:space:]])?)\*([^[:alnum:]*]|$)/\1\2\4/g' \
        -e 's/(^|[^[:alnum:]_])__([^_[:space:]]([^_]*[^_[:space:]])?)__([^[:alnum:]_]|$)/\1\2\4/g' \
        -e 's/(^|[^[:alnum:]_])_([^_[:space:]]([^_]*[^_[:space:]])?)_([^[:alnum:]_]|$)/\1\2\4/g' \
        -e 's/(^|[^[:alnum:]*])\*\*([^*[:space:]]([^*]*[^*[:space:]])?)\*\*([^[:alnum:]*]|$)/\1\2\4/g' \
        -e 's/(^|[^[:alnum:]*])\*([^*[:space:]]([^*]*[^*[:space:]])?)\*([^[:alnum:]*]|$)/\1\2\4/g' \
        -e 's/(^|[^[:alnum:]_])__([^_[:space:]]([^_]*[^_[:space:]])?)__([^[:alnum:]_]|$)/\1\2\4/g' \
        -e 's/(^|[^[:alnum:]_])_([^_[:space:]]([^_]*[^_[:space:]])?)_([^[:alnum:]_]|$)/\1\2\4/g' \
        -e 's/^#+ //g' \
        -e 's/^[[:space:]]*[-*+][[:space:]]//g' \
        -e 's/^>[[:space:]]?//g'
}

#!/bin/bash
# flatfile.sh — lit un fichier « clé=valeur » sans jamais exécuter son contenu.
#
# Pourquoi ce fichier existe :
#     Les messages et la configuration sont édités par l'utilisateur. Les charger
#     par « source » exécuterait n'importe quelle commande écrite dans une valeur.
#
# Usage :
#     Charger ce fichier, puis appeler read_flat_file <fichier> <tableau> ; les
#     paires sont rangées dans le tableau associatif <tableau>, déclaré par
#     l'appelant. Les lignes vides, celles qui commencent par # et celles dont la
#     clé n'est pas en minuscules et tirets bas sont ignorées.

read_flat_file() {
    local file="$1"
    local -n target="$2"
    local key value

    [ -r "$file" ] || return 1
    while IFS='=' read -r key value || [ -n "$key" ]; do
        [[ "$key" =~ ^[a-z][a-z_]*$ ]] || continue
        target["$key"]="$value"
    done < "$file"
}

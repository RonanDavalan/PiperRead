"""
synth_client.py — envoie une phrase au serveur de synthèse local et récupère l'audio.

Pourquoi ce fichier existe :
    C'est la seule frontière entre l'interface et le moteur : un client HTTP
    ordinaire, sans rien connaître de l'implémentation du moteur de l'autre
    côté du port local.

Entrée / sortie :
    Entrée : l'URL de base du serveur (`http://127.0.0.1:<port>`), le texte
    d'une phrase et, en option, le `length_scale` calculé depuis la vitesse
    résolue (`config.speed_to_length_scale`), même calcul que `read.sh`.
    Sortie : les octets d'un fichier WAV.

Dépend de :
    `requests`.
"""

import requests

_DELAI_REQUETE_SECONDES = 30.0


class ErreurSynthese(RuntimeError):
    pass


def synthesize(base_url: str, text: str, length_scale: float | None = None) -> bytes:
    if not text.strip():
        raise ValueError("Texte vide : rien à synthétiser.")

    corps = {"text": text}
    if length_scale is not None:
        corps["length_scale"] = length_scale

    try:
        reponse = requests.post(
            f"{base_url}/synthesize",
            json=corps,
            timeout=_DELAI_REQUETE_SECONDES,
        )
    except requests.RequestException as erreur:
        raise ErreurSynthese(f"Requête vers {base_url} échouée : {erreur}") from erreur

    if reponse.status_code != 200:
        raise ErreurSynthese(
            f"Le serveur a répondu {reponse.status_code} : {reponse.text.strip()}"
        )
    if not reponse.content:
        raise ErreurSynthese("Réponse vide du serveur de synthèse.")
    return reponse.content

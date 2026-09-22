# PiperRead — interface graphique (en construction)

Projet Python autonome, distinct du noyau Bash (`read.sh`). L'interface ne lie
jamais le moteur Piper dans son propre processus : elle le pilote comme
programme externe, par le serveur HTTP que Piper fournit lui-même
(`python3 -m piper.http_server`), lancé en sous-processus et lié à
`127.0.0.1` uniquement. Décision et raison complètes dans
`_CADRE/SPECIFICATIONS/CONCEPTION_PIPERREAD.md`, fiche « interface graphique ».

État actuel (session 1 de `_CADRE/SPECIFICATIONS/ROADMAP.md`, chantier
« Interface graphique ») : la chaîne complète fonctionne en ligne de commande,
sans fenêtre — presse-papiers → découpage en phrases → serveur local →
lecture audio. La fenêtre, le tray et le menu sont la session suivante.

## Structure

```
gui/
├── pyproject.toml          — métadonnées et dépendances (PySide6, requests, pysbd, sounddevice)
├── piperread_gui/
│   ├── clipboard.py        — capture du presse-papiers (wl-paste puis xsel, ordre du noyau)
│   ├── sentences.py        — découpage en phrases (pysbd, langues en/fr/de/es)
│   ├── server.py           — cycle de vie du serveur HTTP local de Piper
│   ├── synth_client.py     — client HTTP vers /synthesize
│   ├── player.py           — lecture du WAV reçu (sounddevice)
│   └── cli.py               — boucle de test en ligne de commande
└── tests/                  — tests unitaires (pytest), sans dépendance réseau ni matériel audio
```

## Comment tester / Comment lancer

Dépôt cloné avec le noyau déjà installé (`../piper-env/` présent, comme pour
`read.sh`). Le serveur HTTP est un extra du moteur, pas installé par défaut :

```bash
cd ~/git/PiperRead/PiperRead/piper-env
bin/pip install "piper-tts[http]"
```

Mettre en place l'environnement de l'interface, puis lancer les tests
unitaires :

```bash
cd ~/git/PiperRead/PiperRead/gui
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 -m pytest
```

Essai réel de la chaîne complète, sans fenêtre — copier un texte, puis :

```bash
cd ~/git/PiperRead/PiperRead/gui
source .venv/bin/activate
python3 -m piperread_gui.cli --lang fr
```

`--model <chemin>` force une voix précise ; sans cette option, la première
voix trouvée dans `../voices/*.onnx` est utilisée. `--lang` choisit la langue
du découpeur de phrases parmi `en`, `fr`, `de`, `es` (défaut `fr`).

Contrôle d'isolation du moteur — le code de l'interface ne doit contenir
aucun `import` direct du module `piper` :

```bash
cd ~/git/PiperRead/PiperRead
grep -rnE 'import[[:space:]]piper' gui/
```

Contrôle de la liaison réseau — pendant une lecture, dans un autre terminal :

```bash
ss -tlnp
```

Le port du serveur n'apparaît que sur `127.0.0.1`, jamais sur `0.0.0.0`.

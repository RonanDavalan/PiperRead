# PiperRead — interface graphique (en construction)

Projet Python autonome, distinct du noyau Bash (`read.sh`). L'interface ne lie
jamais le moteur Piper dans son propre processus : elle le pilote comme
programme externe, par le serveur HTTP que Piper fournit lui-même
(`python3 -m piper.http_server`), lancé en sous-processus et lié à
`127.0.0.1` uniquement. Décision et raison complètes dans
`_CADRE/SPECIFICATIONS/CONCEPTION_PIPERREAD.md`, fiche « interface graphique ».

État actuel (session 2 de `_CADRE/SPECIFICATIONS/ROADMAP.md`, chantier
« Interface graphique ») : icône de tray et menu (Lire, Pause, Reprendre,
Arrêter, Phrase précédente/suivante, Réglages, Quitter) branchés sur la
chaîne de la session 1. Le dialogue de réglages, la configuration partagée
avec le noyau et le paquet sont les sessions suivantes.

## Structure

```
gui/
├── pyproject.toml          — métadonnées et dépendances (PySide6, requests, pysbd, sounddevice)
├── piperread_gui/
│   ├── clipboard.py        — capture du presse-papiers (wl-paste puis xsel, ordre du noyau)
│   ├── sentences.py        — découpage en phrases (pysbd, langues en/fr/de/es)
│   ├── server.py           — cycle de vie du serveur HTTP local de Piper
│   ├── synth_client.py     — client HTTP vers /synthesize
│   ├── player.py           — lecture du WAV reçu (sounddevice), interruptible (arrêt, pause)
│   ├── controller.py       — état de lecture (arrêt/lecture/pause), fil de fond
│   ├── notifier.py         — notification système par `notify-send`, indépendante du tray
│   ├── tray.py              — icône de tray, menu, détection de l'absence d'hôte de tray
│   ├── app.py                — point d'entrée : assemble tray, contrôleur et boucle Qt
│   └── cli.py                 — boucle de test en ligne de commande, sans fenêtre
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
env -u LD_LIBRARY_PATH QT_QPA_PLATFORM=offscreen python3 -m pytest
```

`LD_LIBRARY_PATH` neutralisé pour la même raison que plus bas (bibliothèques
Qt du système en conflit) ; `QT_QPA_PLATFORM=offscreen` pour que les tests du
tray (`test_tray.py`) s'exécutent sans écran réel.

Essai réel de la chaîne complète, sans fenêtre — copier un texte, puis :

```bash
cd ~/git/PiperRead/PiperRead/gui
source .venv/bin/activate
python3 -m piperread_gui.cli --lang fr
```

`--model <chemin>` force une voix précise ; sans cette option, la première
voix trouvée dans `../voices/*.onnx` est utilisée. `--lang` choisit la langue
du découpeur de phrases parmi `en`, `fr`, `de`, `es` (défaut `fr`).

Lancer l'interface graphique (icône de tray et menu) — copier un texte, puis :

```bash
cd ~/git/PiperRead/PiperRead/gui
source .venv/bin/activate
python3 -m piperread_gui.app --lang fr
```

**Piège de plateforme (constaté en session 2, KDE Plasma) :** si le shell
définit `LD_LIBRARY_PATH` (par exemple pour CUDA), il masque les
bibliothèques Qt embarquées par PySide6 au profit de celles, plus anciennes,
du système, avec un plantage immédiat (`undefined symbol` puis
segmentation fault). Neutraliser la variable avant de lancer l'interface :

```bash
env -u LD_LIBRARY_PATH python3 -m piperread_gui.app --lang fr
```

Menu du tray : Lire, Pause, Reprendre, Arrêter, Phrase précédente/suivante
(actifs pendant la lecture ou la pause), Réglages (désactivé, session
suivante), Quitter. Sur un bureau qui n'expose aucune zone de notification
système (GNOME sans l'extension « AppIndicator and KStatusNotifierItem
Support »), une notification de bureau unique explique la situation au
démarrage ; l'interface continue de fonctionner.

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

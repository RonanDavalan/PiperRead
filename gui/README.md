# PiperRead — interface graphique (en construction)

Projet Python autonome, distinct du noyau Bash (`read.sh`). L'interface ne lie
jamais le moteur Piper dans son propre processus : elle le pilote comme
programme externe, par le serveur HTTP que Piper fournit lui-même
(`python3 -m piper.http_server`), lancé en sous-processus et lié à
`127.0.0.1` uniquement. Décision et raison complètes dans
`_CADRE/SPECIFICATIONS/CONCEPTION_PIPERREAD.md`, fiche « interface graphique ».

État actuel : icône de tray et menu (Lire, Pause, Arrêter, Phrase
précédente/suivante, Réglages, Quitter) branchés sur la chaîne de lecture
(capture → nettoyage Markdown → phrases → serveur → audio) ; un clic gauche
sur l'icône lit, met en pause ou reprend selon l'état. Le texte lu est la
sélection souris, ou à défaut le presse-papiers (Linux, même ordre que le
mode `auto` du noyau ; presse-papiers seul sous Windows), débarrassé du
balisage Markdown par les mêmes règles que `utils/cleaner.sh`. Tous les
libellés sont tirés des mêmes fichiers `lang/*.txt` que le noyau. La
configuration (`piperread.conf`, mêmes clés `speed`/`voice`/`lang`, même
ordre de priorité) est lue et écrite en Python (`config.py`) ; le dialogue
de réglages (menu « Réglages… ») l'écrit réellement, et la vitesse choisie
s'applique à la synthèse (`length_scale`). Paquets Linux (`piperread-gui`)
et exécutable Windows (`packaging/windows/`).

## Structure

```
gui/
├── pyproject.toml          — métadonnées et dépendances (PySide6, requests, pysbd, sounddevice)
├── piperread_gui/
│   ├── clipboard.py        — capture : sélection souris puis presse-papiers (wl-paste puis xsel, ordre du noyau)
│   ├── cleaner.py          — retrait du balisage Markdown (port de `utils/cleaner.sh`)
│   ├── sentences.py        — découpage en phrases (pysbd, langues en/fr/de/es)
│   ├── server.py           — cycle de vie du serveur HTTP local de Piper
│   ├── synth_client.py     — client HTTP vers /synthesize, avec `length_scale` optionnel
│   ├── player.py           — lecture du WAV reçu (sounddevice), interruptible (arrêt, pause)
│   ├── flatfile.py         — lecture « clé=valeur » sans exécution (port de `utils/flatfile.sh`)
│   ├── config.py           — résolution et écriture de `piperread.conf` (port de `utils/config.sh`)
│   ├── i18n.py              — chargement des mêmes `lang/*.txt` que le noyau, plus les clés `gui_*`
│   ├── controller.py       — état de lecture (arrêt/lecture/pause), fil de fond, réglages courants
│   ├── notifier.py         — notification système par `notify-send`, indépendante du tray
│   ├── tray.py              — icône de tray, menu traduit, détection de l'absence d'hôte de tray
│   ├── settings_dialog.py  — dialogue de réglages (voix, vitesse, langue), écrit `piperread.conf`
│   ├── frozen.py            — dossier réel de l'exécutable gelé (PyInstaller), à la place de `Path(__file__)`
│   ├── piper_server_entry.py — point d'entrée gelé séparément pour `piper-http-server.exe` (paquet Windows)
│   ├── app.py                — point d'entrée : résout la configuration, assemble tray, contrôleur et boucle Qt
│   └── cli.py                 — boucle de test en ligne de commande, sans fenêtre
├── packaging/windows/       — `.spec` PyInstaller, icône `.ico`, `README.txt` livré avec le paquet Windows
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
du découpeur de phrases parmi `en`, `fr`, `de`, `es` (défaut `fr`). `cli.py`
ne lit pas `piperread.conf` — c'est une boucle de test minimale ; la
résolution de la configuration se fait dans `app.py` (ci-dessous).

Lancer l'interface graphique (icône de tray et menu) — copier un texte, puis :

```bash
cd ~/git/PiperRead/PiperRead/gui
source .venv/bin/activate
python3 -m piperread_gui.app
```

Sans option, la voix, la vitesse et la langue sont résolues dans le même
ordre que `read.sh` : variables `PIPERREAD_VOICE`/`PIPERREAD_SPEED`/
`PIPERREAD_LANG`, puis `$XDG_CONFIG_HOME/piperread/piperread.conf` (mêmes
clés), puis la première voix trouvée dans `../voices/*.onnx` (et l'anglais
pour la langue, à défaut de la locale système). `--lang` et `--speed`
remplacent cette résolution pour la session en cours :
`python3 -m piperread_gui.app --lang de --speed 1,5`. `--model` tient lieu
d'option de voix (chemin direct vers un `.onnx`, plutôt qu'un nom à
résoudre — choix de session 1, conservé) et prime sur tout le reste. Le menu
« Réglages… » ouvre un dialogue (voix, vitesse, langue) qui réécrit
`piperread.conf` sans toucher au reste de son contenu.

Contrôle du couple configuration/traduction, sans dépendre d'un fichier réel
(la configuration réelle de la machine n'est jamais touchée par les tests) :

```bash
cd ~/git/PiperRead/PiperRead/gui
env -u LD_LIBRARY_PATH QT_QPA_PLATFORM=offscreen .venv/bin/python3 -m pytest tests/test_config.py tests/test_i18n.py tests/test_settings_dialog.py
```

**Piège de plateforme (constaté en session 2, KDE Plasma) :** si le shell
définit `LD_LIBRARY_PATH` (par exemple pour CUDA), il masque les
bibliothèques Qt embarquées par PySide6 au profit de celles, plus anciennes,
du système, avec un plantage immédiat (`undefined symbol` puis
segmentation fault). Neutraliser la variable avant de lancer l'interface :

```bash
env -u LD_LIBRARY_PATH python3 -m piperread_gui.app --lang fr
```

Menu du tray (clic droit), libellés dans la langue résolue : Lire, Pause,
Arrêter, Phrase précédente/suivante (actifs pendant la lecture ou la pause),
Réglages…, Quitter. « Lire » pendant une pause reprend là où la lecture
s'était arrêtée. Clic gauche sur l'icône : lire à l'arrêt, mettre en pause
pendant la lecture, reprendre en pause. Sur un bureau qui n'expose aucune zone de notification
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

## Paquet Windows

Deux exécutables autonomes (`piperread-gui.exe`, `piper-http-server.exe` —
processus séparé, même frontière GPL que `server.py`), gelés par PyInstaller
sur un vrai runner Windows (pas de construction croisée depuis Linux) :
`_CADRE/SPECIFICATIONS/PROCEDURES_LLM/TACHE_construire-paquet-windows.md`. Déclencher
la construction (nécessite d'être poussé sur `main`) :

```bash
gh workflow run build-windows-gui.yml --repo RonanDavalan/PiperRead
gh run list --repo RonanDavalan/PiperRead --workflow build-windows-gui.yml --limit 1
gh run download <id-de-l-exécution> --repo RonanDavalan/PiperRead
```

L'archive produite (`piperread-gui-windows.zip`) contient les deux
exécutables, `lang/`, `piperread.ico`, un dossier `voices/` vide (voix jamais
livrées, voir la décision « voix jamais livrées ni téléchargées sans
demande ») et `README.txt` (anglais, instructions de lancement).

Essai à blanc reproductible côté Linux (ELF, inutilisable tel quel, mais
révèle un piège de résolution de chemin ou de données Piper embarquées avant
de dépenser une exécution CI Windows) :

```bash
cd gui
.venv/bin/pip install pyinstaller "piper-tts[http]"
env -u LD_LIBRARY_PATH .venv/bin/pyinstaller --noconfirm --distpath /tmp/dist-essai packaging/windows/piper-http-server.spec
env -u LD_LIBRARY_PATH .venv/bin/pyinstaller --noconfirm --distpath /tmp/dist-essai packaging/windows/piperread-gui.spec
```

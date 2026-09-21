% PIPERREAD(1) piperread | Commandes utilisateur
% Ronan Davalan
% 2026-09-21

# NOM

piperread - lire à voix haute le texte sélectionné ou copié, hors ligne, avec le moteur Piper

# SYNOPSIS

**piperread** [*auto* | *selection* | *clipboard*] [**\--speed** *X*] [**\--voice** *NOM*] [**\--lang** *CODE*]

**piperread** {**\--stop** | **\--pause** | **\--resume**}

**piperread** {**\--version** | **\--diagnose**}

**piperread** **\--list-voices**

**piperread** **\--download-voice** [*NOM*...]

# DESCRIPTION

**piperread** lit à voix haute le texte que vous avez sélectionné à la souris
ou copié dans le presse-papiers, sous Wayland comme sous X11. La voix est
synthétisée localement par le moteur neuronal Piper : aucun texte et aucun son
ne quittent jamais la machine. Les symboles Markdown sont retirés avant la
lecture, de sorte qu'un texte mis en forme est dit comme de la prose.

Une seule lecture s'exécute à la fois : relancer **piperread** arrête la
lecture précédente. La commande est prévue pour être liée à un raccourci
clavier du bureau.

Le moteur ne fait pas partie du programme lui-même. Il s'installe à part, par
`pip install piper-tts`, et cette étape demande une connexion réseau et de
l'espace disque. Ni les paquets ni le moteur ne contiennent de voix : une voix
se télécharge une fois avec **\--download-voice**, puis fonctionne sans réseau.

# SOURCE DU TEXTE

*selection*
:   Lire le texte sélectionné à la souris.

*clipboard*
:   Lire le texte copié dans le presse-papiers.

*auto*
:   Valeur par défaut. Lire la sélection à la souris, ou le presse-papiers si
    rien n'est sélectionné. Un contenu fait uniquement d'espaces et de sauts de
    ligne compte pour vide.

# OPTIONS

**\--speed** *X*
:   Multiplicateur de vitesse, de `0.5` à `3.0`. `1` est le rythme naturel de
    la voix.

**\--voice** *NOM*
:   Voix à utiliser, telle que **\--list-voices** la liste.

**\--lang** *CODE*
:   Langue des messages et de la voix par défaut (`en`, `fr`, `de` ou `es`).

**\--stop**
:   Arrêter la lecture en cours.

**\--pause**, **\--resume**
:   Suspendre la lecture, puis la reprendre là où elle s'était arrêtée.

**\--diagnose**
:   Vérifier l'installation (moteur, voix, audio, outils de presse-papiers)
    sans rien lire ni jouer, puis quitter. Le code de sortie est `1` quand une
    vérification échoue.

**\--list-voices**
:   Afficher les voix proposées, avec leur licence. Aucun accès au réseau.

**\--download-voice** [*NOM*...]
:   Télécharger les voix nommées dans le dossier des voix. Sans nom, proposer
    la voix de la langue courante.

**\--version**
:   Afficher la version et quitter.

# CONFIGURATION

Chaque réglage (`speed`, `voice`, `lang`) est pris dans la première de ces
sources qui le définit :

1. l'option de la ligne de commande ;
2. la variable d'environnement `PIPERREAD_SPEED`, `PIPERREAD_VOICE` ou `PIPERREAD_LANG` ;
3. le fichier de configuration.

# FICHIERS

`$XDG_CONFIG_HOME/piperread/piperread.conf`
:   Fichier de configuration, `~/.config/piperread/piperread.conf` quand
    `XDG_CONFIG_HOME` n'est pas définie.

`$XDG_DATA_HOME/piperread/voices/`
:   Voix téléchargées, `~/.local/share/piperread/voices/` quand `XDG_DATA_HOME`
    n'est pas définie.

`/usr/lib/piperread/venv`
:   Environnement Python qui contient le moteur Piper, pour une installation
    par paquet.

# VOIX

Les voix viennent du catalogue Piper,
<https://huggingface.co/rhasspy/piper-voices>. Chaque voix a sa propre licence,
affichée par **\--list-voices**. Des échantillons s'écoutent sur
<https://rhasspy.github.io/piper-samples/>.

# CODE DE SORTIE

`0` en cas de succès, `1` quand une dépendance, le moteur ou une voix manque ou
qu'une vérification du diagnostic échoue, `2` en cas d'erreur d'usage.

# AUTEUR

Ronan Davalan. Sources et signalement des anomalies : <https://github.com/RonanDavalan/PiperRead>.

# LICENCE

MIT.

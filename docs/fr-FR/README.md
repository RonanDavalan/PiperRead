# PiperRead

<p align="center">
  <img src="https://img.shields.io/static/v1?label=Version&message=v0.1.2-alpha&color=orange" alt="Version">
  <img src="https://img.shields.io/badge/Licence-MIT-green" alt="Licence">
  <img src="https://img.shields.io/badge/Plateforme-Linux_(Wayland_|_X11)-black" alt="OS supporté">
  <img src="https://img.shields.io/badge/Moteur-Piper_Neural_TTS-blueviolet" alt="Moteur audio">
  <img src="https://img.shields.io/badge/Langage-Python_|_Bash-blue" alt="Code">
</p>

[English](../../README.md) | **Français** | [Deutsch](../de-DE/README.md) | [Español](../es-ES/README.md)

## Description

**PiperRead** est une solution d'automatisation légère conçue pour apporter une synthèse vocale neuronale (TTS) de haute qualité sur les bureaux Linux.

**Site officiel** : [piperread.davalan.fr](https://piperread.davalan.fr)

Contrairement aux solutions cloud, PiperRead fonctionne entièrement hors-ligne (local) grâce au moteur [Piper](https://github.com/OHF-voice/piper1-gpl). Il fait le pont entre votre environnement de bureau (presse-papiers/souris) et le moteur de synthèse.

Il permet de lire à haute voix n'importe quel texte sélectionné à la souris ou copié dans le presse-papiers, sans nécessiter de lecteur d'écran complexe.

## Cas d'usage

*   **Accessibilité** : lecture rapide de contenus pour les personnes ayant une déficience visuelle légère ou une fatigue oculaire.
*   **Productivité** : écoute d'articles ou de documents pendant l'exécution d'une autre tâche.
*   **Correction** : relecture de ses propres textes par une voix tierce pour détecter les erreurs.

## Fonctionnalités clés

*   **Confidentialité totale** : traitement 100% local. Aucune donnée n'est envoyée vers un cloud.
*   **Latence nulle** : lecture instantanée adaptée à un usage temps réel.
*   **Compatibilité universelle** : détecte et s'adapte automatiquement à **Wayland** (Debian 12/13) ou **X11**.
*   **Sélection intelligente** : priorise la sélection souris (primaire) et bascule sur le presse-papiers si aucune sélection n'est active.
*   **Isolation** : s'exécute dans son propre environnement virtuel Python pour ne pas polluer votre système.

---

## Installation par paquet

La voie la plus simple. Téléchargez le paquet de votre système depuis la [page de téléchargement](https://piperread.davalan.fr/fr/download/) ou depuis la [dernière Release](https://github.com/RonanDavalan/PiperRead/releases/latest), puis installez-le :

```bash
# Debian 12 et 13, Ubuntu 22.04 et 24.04, Linux Mint
sudo apt install ./piperread_0.2.0~alpha_all.deb

# Fedora 42
sudo dnf install ./piperread-0.2.0~alpha-1.fc42.noarch.rpm

# openSUSE Leap 15.6
sudo zypper install ./piperread-0.2.0~alpha-1.leap156.noarch.rpm

# Arch Linux
sudo pacman -U piperread-0.2.0alpha-1-any.pkg.tar.zst
```

Le paquet installe le moteur Piper avec `pip` à sa configuration : environ 75 Mo à télécharger (200 à 250 Mo une fois installé), avec un accès réseau à ce seul moment. Il ne contient aucune voix. Téléchargez-en une, puis vérifiez l'installation :

```bash
piperread --download-voice
piperread --diagnose
```

Les paquets ont été validés en conteneur (installation, diagnostic et retrait) sur chaque distribution et chaque version listées ci-dessus. Le manuel existe sous forme de page (`man piperread`) et de PDF en quatre langues sur la page de téléchargement.

## Prérequis

Avant l'installation depuis les sources, assurez-vous que votre système dispose des outils audio et presse-papiers nécessaires.

```bash
# Mise à jour du système
sudo apt update

# Installation de Python, audio et outils presse-papiers
# (Installe à la fois wl-clipboard pour Wayland et xsel pour X11 pour garantir la compatibilité)
sudo apt install -y python3 python3-venv python3-pip alsa-utils wl-clipboard xsel libnotify-bin
```

---

## Installation depuis les sources

Puisque ce projet repose sur des modèles vocaux lourds et un environnement virtuel spécifique, vous devez initialiser le projet après l'avoir cloné.

### 1. Cloner le dépôt

```bash
mkdir -p $HOME/git/piper
cd $HOME/git/piper
git clone https://github.com/RonanDavalan/PiperRead.git
cd PiperRead
```

### 2. Initialiser l'environnement (critique)

Cette étape crée l'isolation Python, installe le moteur, puis télécharge la voix que vous choisissez. `./read.sh --list-voices` liste les voix proposées avec leur licence, leur taille et des liens d'écoute ; la qualité d'une voix reste à l'appréciation de chacun.

```bash
# Création de l'environnement virtuel
python3 -m venv piper-env

# Installation du moteur Piper TTS
./piper-env/bin/pip install piper-tts

# Téléchargement d'une voix (choix : ./read.sh --list-voices)
./read.sh --download-voice fr_FR-siwis-medium
```

### 3. Configuration des permissions

```bash
chmod 700 read.sh
```

### 4. Intégration au bureau (icône et menu)

Pour lancer PiperRead comme une application native :

```bash
# Création du dossier d'applications locales
mkdir -p $HOME/.local/share/applications

# Copie du fichier desktop
cp Ressources/PiperRead.desktop $HOME/.local/share/applications/

# Mise à jour de la base de données des menus
update-desktop-database $HOME/.local/share/applications
```

---

## Utilisation

### Méthode 1 : Sélection souris (recommandé)

1.  **Surlignez du texte** dans n'importe quelle application (navigateur, PDF, éditeur).
2.  Cliquez sur l'icône **PiperRead** dans votre menu (ou utilisez votre raccourci clavier personnalisé).
3.  Le texte est lu immédiatement.

### Méthode 2 : Presse-papiers

1.  Copiez du texte (**Ctrl+C**).
2.  Lancez PiperRead.

### Arrêter la lecture

Lancez `piperread --stop` (ou `./read.sh --stop` depuis un clone) pour terminer la lecture, `--pause` pour la suspendre et `--resume` pour la reprendre là où elle s'est arrêtée. Liez ces commandes à des raccourcis clavier si vous le souhaitez.

---

## Qualité

Ce projet est né d'une découverte : la qualité impressionnante du moteur **Piper** pour une solution entièrement libre et locale.

*   **Rendu vocal naturel** : le choix de cette technologie neuronale permet une lecture fluide et posée, rendant l'écoute confortable sur la durée.
*   **Architecture légère** : PiperRead n'est pas une application lourde, mais un orchestrateur minimaliste. Il fait le lien entre votre bureau et le moteur audio avec une empreinte système quasi-nulle.
*   **Installation propre** : l'utilisation stricte d'environnements virtuels (venv) garantit que le logiciel reste confiné et ne modifie pas les bibliothèques de votre système principal.

---

## Origine du projet

L'impulsion de ce projet vient de mon frère, utilisateur historique de Debian, qui a identifié Piper comme la solution utile pour du TTS local.

---

## Crédits & "Vibe Coding"

Le projet **PiperRead** est le résultat d'une collaboration hybride **Humain-IA** :

*   **Ronan Davalan** : architecte et arbitre. Vision produit, exigences de sécurité, direction du projet, validation et tests. Toutes les décisions d'architecture sont validées par lui.
*   **Claude Code (Anthropic)** : ingénieur systèmes et développeur principal. Implémentation des scripts Bash, de la documentation et du site ; choix techniques dans l'architecture validée. Auteur principal du code source.
*   **Google Gemini** : synthétiseur et conseiller stratégique. Analyse d'architecture indépendante, résolution de conflits logiques, optimisation du flux de travail, validation croisée des décisions techniques.
*   **Muse Spark** : synthétiseur et conseiller stratégique. Remplace Gemini lors de certaines sessions, avec de bons résultats ; certaines de ses réponses ont été transmises à Claude Code.
*   **DeepSeek** : nettoyage du cadre de travail du projet, au départ.
*   **Moteur Core** : [Piper TTS](https://github.com/OHF-voice/piper1-gpl), sous licence GPL-3.0-or-later. Il est installé sur votre machine par `pip` et appelé comme programme externe ; PiperRead ne le redistribue pas.

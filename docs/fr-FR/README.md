# PiperRead

<p align="center">
  <img src="https://img.shields.io/static/v1?label=Version&message=v0.1.2-alpha&color=orange" alt="Version">
  <img src="https://img.shields.io/badge/Licence-MIT-green" alt="Licence">
  <img src="https://img.shields.io/badge/Plateforme-Linux_(Wayland_|_X11)-black" alt="OS supporté">
  <img src="https://img.shields.io/badge/Moteur-Piper_Neural_TTS-blueviolet" alt="Moteur audio">
  <img src="https://img.shields.io/badge/Langage-Python_|_Bash-blue" alt="Code">
</p>

[🇺🇸 English](../../README.md) | **🇫🇷 Français** | [🇩🇪 Deutsch](../de-DE/README.md) | [🇪🇸 Español](../es-ES/README.md)

## Description

**PiperRead** est une solution d'automatisation légère conçue pour apporter une synthèse vocale neuronale (TTS) de haute qualité sur les bureaux Linux.

🌐 **Site officiel** : [piperread.davalan.fr](https://piperread.davalan.fr)

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

## 🛠️ Prérequis

Avant l'installation, assurez-vous que votre système dispose des outils audio et presse-papiers nécessaires.

```bash
# Mise à jour du système
sudo apt update

# Installation de Python, audio et outils presse-papiers
# (Installe à la fois wl-clipboard pour Wayland et xsel pour X11 pour garantir la compatibilité)
sudo apt install -y python3 python3-venv python3-pip alsa-utils wl-clipboard xsel libnotify-bin
```

---

## 💾 Installation

Puisque ce projet repose sur des modèles vocaux lourds et un environnement virtuel spécifique, vous devez initialiser le projet après l'avoir cloné.

### 1. Cloner le dépôt

```bash
mkdir -p $HOME/git/piper
cd $HOME/git/piper
git clone https://github.com/RonanDavalan/PiperRead.git
cd PiperRead
```

### 2. Initialiser l'environnement (critique)

Cette étape crée l'isolation Python et télécharge le modèle vocal neuronal (français - Siwis Medium).

```bash
# Création de l'environnement virtuel
python3 -m venv piper-env

# Installation du moteur Piper TTS
./piper-env/bin/pip install piper-tts

# Téléchargement du modèle vocal
mkdir -p voices
cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
cd ..
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

## 🚀 Utilisation

### Méthode 1 : Sélection souris (recommandé)

1.  **Surlignez du texte** dans n'importe quelle application (navigateur, PDF, éditeur).
2.  Cliquez sur l'icône **PiperRead** dans votre menu (ou utilisez votre raccourci clavier personnalisé).
3.  Le texte est lu immédiatement.

### Méthode 2 : Presse-papiers

1.  Copiez du texte (**Ctrl+C**).
2.  Lancez PiperRead.

### Arrêter la lecture

*Limitation Alpha actuelle* : pour stopper la lecture en cours de route, exécutez `pkill -f aplay` dans un terminal.

---

## 💎 Qualité

Ce projet est né d'une découverte : la qualité impressionnante du moteur **Piper** pour une solution entièrement libre et locale.

*   **Rendu vocal naturel** : le choix de cette technologie neuronale permet une lecture fluide et posée, rendant l'écoute confortable sur la durée.
*   **Architecture légère** : PiperRead n'est pas une application lourde, mais un orchestrateur minimaliste. Il fait le lien entre votre bureau et le moteur audio avec une empreinte système quasi-nulle.
*   **Installation propre** : l'utilisation stricte d'environnements virtuels (venv) garantit que le logiciel reste confiné et ne modifie pas les bibliothèques de votre système principal.

---

## 💡 Origine du projet

L'impulsion de ce projet vient de mon frère, utilisateur historique de Debian, qui a identifié Piper comme la solution utile pour du TTS local.

---

## 🤖 Crédits & "Vibe Coding"

Le projet **PiperRead** est le résultat d'une collaboration hybride **Humain-IA** :

*   **Ronan Davalan** : chef de projet, architecte principal, assurance qualité (QA).
*   **Google Gemini** : architecte IA, planificateur, rédacteur technique.
*   **Claude (Anthropic)** & **Perplexity** : consultants techniques IA (revue de code et optimisation).
*   **Moteur Core** : [Piper TTS](https://github.com/OHF-voice/piper1-gpl), sous licence GPL-3.0-or-later. Il est installé sur votre machine par `pip` et appelé comme programme externe ; PiperRead ne le redistribue pas.

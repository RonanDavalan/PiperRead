
# PiperRead

<p align="center">
  <img src="https://img.shields.io/static/v1?label=Version&message=v0.2.0-alpha&color=orange" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Platform-Linux_(Wayland_|_X11)-black" alt="Supported OS">
  <img src="https://img.shields.io/badge/Engine-Piper_Neural_TTS-blueviolet" alt="Audio Engine">
  <img src="https://img.shields.io/badge/Language-Python_|_Bash-blue" alt="Code">
</p>

**English** | [Français](docs/fr-FR/README.md) | [Deutsch](docs/de-DE/README.md) | [Español](docs/es-ES/README.md)

## Description

**PiperRead** is a lightweight automation solution designed to bring high-quality neural text-to-speech (TTS) to Linux desktops.

**Official Website**: [piperread.davalan.fr](https://piperread.davalan.fr)

Unlike cloud-based solutions, PiperRead operates entirely offline (locally) thanks to the [Piper](https://github.com/OHF-voice/piper1-gpl) engine. It acts as a bridge between your desktop environment (Clipboard/Mouse) and the synthesis engine.

It allows you to read aloud any text selected with the mouse or copied to the clipboard, without requiring a complex screen reader.

## Use Cases

*   **Accessibility**: Quick reading of content for people with mild visual impairment or eye fatigue.
*   **Productivity**: Listening to articles or documents while performing another task.
*   **Proofreading**: Hearing your own text read by a third-party voice to detect errors.

## Key Features

*   **Total Privacy**: 100% local processing. No data is sent to any cloud.
*   **Zero Latency**: Instant playback suitable for real-time usage.
*   **Universal Compatibility**: Automatically detects and adapts to **Wayland** (Debian 12/13) or **X11**.
*   **Smart Selection**: Prioritizes mouse selection (primary) and switches to clipboard if no selection is active.
*   **Isolation**: Runs in its own Python virtual environment to avoid polluting your system.

---

## Installation from a package

The simplest way. Download the package for your system from the [download page](https://piperread.davalan.fr/download/) or from the [latest release](https://github.com/RonanDavalan/PiperRead/releases/latest), then install it:

```bash
# Debian 12 and 13, Ubuntu 22.04 and 24.04, Linux Mint
sudo apt install ./piperread_0.2.0~alpha_all.deb

# Fedora 42
sudo dnf install ./piperread-0.2.0~alpha-1.fc42.noarch.rpm

# openSUSE Leap 15.6
sudo zypper install ./piperread-0.2.0~alpha-1.leap156.noarch.rpm

# Arch Linux
sudo pacman -U piperread-0.2.0alpha-1-any.pkg.tar.zst
```

The package installs the Piper engine with `pip` when it is configured: about 75 MB to download (200 to 250 MB once installed), with network access needed at that moment only. It ships no voice. Download one, then check the installation:

```bash
piperread --download-voice
piperread --diagnose
```

The packages were validated in containers (installation, diagnostic and removal) on each distribution and version listed above. The manual is available as a page (`man piperread`) and as a PDF in four languages on the download page.

## Prerequisites

Before installing from the sources, ensure your system has the required audio and clipboard tools.

```bash
# System update
sudo apt update

# Install Python, Audio, and Clipboard tools
# (Installs both wl-clipboard for Wayland and xsel for X11 to ensure compatibility)
sudo apt install -y python3 python3-venv python3-pip alsa-utils wl-clipboard xsel libnotify-bin
```

---

## Installation from the sources

Since this project relies on large voice models and a specific virtual environment, you must initialize the project after cloning it.

### 1. Clone the repository

```bash
mkdir -p $HOME/git/piper
cd $HOME/git/piper
git clone https://github.com/RonanDavalan/PiperRead.git
cd PiperRead
```

### 2. Initialize the environment (Critical)

This step creates the Python isolation, installs the engine, then downloads the voice you choose. `./read.sh --list-voices` lists the proposed voices with their licence, size and listening links; the voice quality is a matter of personal taste.

```bash
# Create virtual environment
python3 -m venv piper-env

# Install Piper TTS Engine
./piper-env/bin/pip install piper-tts

# Download a voice (see the choices with ./read.sh --list-voices)
./read.sh --download-voice en_US-ljspeech-medium
```

### 3. Configure permissions

```bash
chmod 700 read.sh
```

### 4. Desktop Integration (Icon and Menu)

To launch PiperRead like a native application:

```bash
# Create local applications and icons folders
mkdir -p $HOME/.local/share/applications $HOME/.local/share/icons/hicolor/scalable/apps

# Install the icon
cp Ressources/piperread.svg $HOME/.local/share/icons/hicolor/scalable/apps/

# Generate the desktop file with the actual installation path
sed "s|\$HOME/git/piper/PiperRead|$(pwd)|g" Ressources/PiperRead.desktop > $HOME/.local/share/applications/piperread.desktop

# Update menu database
update-desktop-database $HOME/.local/share/applications
```

---

## Usage

### Method 1: Mouse Selection (Recommended)

1.  **Highlight text** in any application (Browser, PDF, Editor).
2.  Click the **PiperRead** icon in your menu (or use your custom keyboard shortcut).
3.  The text is read immediately.

### Method 2: Clipboard

1.  Copy text (**Ctrl+C**).
2.  Launch PiperRead.

### Stopping Playback

Run `piperread --stop` (or `./read.sh --stop` from a clone) to end the reading, `--pause` to suspend it and `--resume` to continue where it stopped. Bind these commands to keyboard shortcuts if you like.

---

## Quality

This project was born from a discovery: the impressive quality of the **Piper** engine for a fully free and local solution.

*   **Natural Vocal Rendering**: The choice of this neural technology allows for fluid and poised reading, making listening comfortable over time.
*   **Lightweight Architecture**: PiperRead is not a heavy application, but a minimalist orchestrator. It connects your desktop and the audio engine with an almost non-existent system footprint.
*   **Clean Installation**: The strict use of virtual environments (venv) ensures that the software remains confined and does not modify your main system libraries.

---

## Project Origin

The impetus for this project comes from my brother, a historic Debian user, who identified Piper as a useful solution for local TTS.

---

## Credits & "Vibe Coding"

The **PiperRead** project is the result of a hybrid **Human-AI** collaboration:

*   **Ronan Davalan**: Architect & Arbiter. Product vision, security requirements, project direction, validation and testing. All architectural decisions are validated by him.
*   **Claude Code (Anthropic)**: Systems Engineer & Lead Developer. Implementation of the Bash scripts, the documentation and the website; technical choices within the validated architecture. Principal author of the source code.
*   **Google Gemini**: Synthesizer & Strategic Advisor. Independent architectural analysis, logical conflict resolution, workflow optimisation, cross-validation of technical decisions.
*   **Muse Spark**: Synthesizer & Strategic Advisor. Replaces Gemini in some sessions, with good results; some of its answers were passed on to Claude Code.
*   **DeepSeek**: Cleanup of the project's working framework at the start of the project.
*   **Core Engine**: [Piper TTS](https://github.com/OHF-voice/piper1-gpl), licensed GPL-3.0-or-later. It is installed on your machine by `pip` and called as an external program; PiperRead does not redistribute it.

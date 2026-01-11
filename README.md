
# PiperRead 0.1-Alpha

<p align="center">
  <img src="https://img.shields.io/badge/Version-v0.1--Alpha-orange" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Platform-Linux_(Wayland_|_X11)-black" alt="Supported OS">
  <img src="https://img.shields.io/badge/Engine-Piper_Neural_TTS-blueviolet" alt="Audio Engine">
  <img src="https://img.shields.io/badge/Language-Python_|_Bash-blue" alt="Code">
</p>

**🇺🇸 English** | [🇫🇷 Français](docs/fr-FR/README.md) | [🇩🇪 Deutsch](docs/de-DE/README.md) | [🇪🇸 Español](docs/es-ES/README.md)

## Description

**PiperRead** is a lightweight automation solution designed to bring high-quality neural text-to-speech (TTS) to Linux desktops.

🌐 **Official Website**: [piperread.davalan.fr](https://piperread.davalan.fr)

Unlike cloud-based solutions, PiperRead operates entirely offline (locally) thanks to the [Piper](https://github.com/rhasspy/piper) engine. It acts as a bridge between your desktop environment (Clipboard/Mouse) and the synthesis engine.

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

## 🛠️ Prerequisites

Before installing, ensure your system has the required audio and clipboard tools.

```bash
# System update
sudo apt update

# Install Python, Audio, and Clipboard tools
# (Installs both wl-clipboard for Wayland and xsel for X11 to ensure compatibility)
sudo apt install -y python3 python3-venv python3-pip alsa-utils wl-clipboard xsel
```

---

## 💾 Installation

Since this project relies on large voice models and a specific virtual environment, you must initialize the project after cloning it.

### 1. Clone the repository

```bash
mkdir -p $HOME/git/piper
cd $HOME/git/piper
git clone https://github.com/RonanDavalan/PiperRead.git
cd PiperRead
```

### 2. Initialize the environment (Critical)

This step creates the Python isolation and downloads the neural voice model (French - Siwis Medium).

```bash
# Create virtual environment
python3 -m venv piper-env

# Install Piper TTS Engine
./piper-env/bin/pip install piper-tts

# Download voice model
mkdir -p voices
cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json
cd ..
```

### 3. Configure permissions

```bash
chmod 700 read.sh
```

### 4. Desktop Integration (Icon and Menu)

To launch PiperRead like a native application:

```bash
# Create local applications folder
mkdir -p $HOME/.local/share/applications

# Copy desktop file
cp Ressources/PiperRead.desktop $HOME/.local/share/applications/

# Update menu database
update-desktop-database $HOME/.local/share/applications
```

---

## 🚀 Usage

### Method 1: Mouse Selection (Recommended)

1.  **Highlight text** in any application (Browser, PDF, Editor).
2.  Click the **PiperRead** icon in your menu (or use your custom keyboard shortcut).
3.  The text is read immediately.

### Method 2: Clipboard

1.  Copy text (**Ctrl+C**).
2.  Launch PiperRead.

### Stopping Playback

*Current Alpha Limitation*: To stop reading while it is playing, run `pkill -f aplay` in a terminal.

---

## 💎 Quality

This project was born from a discovery: the impressive quality of the **Piper** engine for a fully free and local solution.

*   **Natural Vocal Rendering**: The choice of this neural technology allows for fluid and poised reading, making listening comfortable over time.
*   **Lightweight Architecture**: PiperRead is not a heavy application, but a minimalist orchestrator. It connects your desktop and the audio engine with an almost non-existent system footprint.
*   **Clean Installation**: The strict use of virtual environments (venv) ensures that the software remains confined and does not modify your main system libraries.

---

## 💡 Project Origin

The impetus for this project comes from my brother, a historic Debian user, who identified Piper as a useful solution for local TTS.

---

## 🤖 Credits & "Vibe Coding"

The **PiperRead** project is the result of a hybrid **Human-AI** collaboration:

*   **Ronan Davalan**: Project Lead, Chief Architect, Quality Assurance (QA).
*   **Google Gemini**: AI Architect, Planner, Technical Writer.
*   **Claude (Anthropic)** & **Perplexity**: AI Technical Consultants (Code review and optimization).
*   **Core Engine**: [Piper TTS](https://github.com/rhasspy/piper) by Rhasspy.

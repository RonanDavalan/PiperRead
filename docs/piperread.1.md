% PIPERREAD(1) piperread | User Commands
% Ronan Davalan
% 2026-09-29

# NAME

piperread - read the selected or copied text aloud, offline, with the Piper engine

# SYNOPSIS

**piperread** [*auto* | *selection* | *clipboard*] [**\--speed** *X*] [**\--voice** *NAME*] [**\--lang** *CODE*] [**\--voices-dir** *PATH*] [**\--normalize** *on*|*off*]

**piperread** {**\--stop** | **\--pause** | **\--resume**}

**piperread** {**\--version** | **\--diagnose** | **\--help**}

**piperread** **\--list-voices**

**piperread** **\--download-voice** [*NAME*...]

# DESCRIPTION

**piperread** reads aloud the text you have selected with the mouse or copied
to the clipboard, under Wayland as well as X11. Speech is synthesized locally
by the neural Piper engine: no text and no audio ever leave the machine.
Markdown symbols are removed before reading, so that a formatted text is
spoken as prose.

Only one reading runs at a time: starting **piperread** again stops the
previous reading. It is meant to be bound to a desktop keyboard shortcut.

The engine is not part of the program itself. It is installed apart, with
`pip install piper-tts`, and needs a network connection and some disk space
for that step. Neither the packages nor the engine ship any voice: a voice is
downloaded once with **\--download-voice**, then works without network.

# SOURCE OF THE TEXT

*selection*
:   Read the text selected with the mouse.

*clipboard*
:   Read the text copied to the clipboard.

*auto*
:   The default. Read the mouse selection, or the clipboard when nothing is
    selected. A content made only of spaces and line breaks counts as empty.

# OPTIONS

**\--speed** *X*
:   Speed multiplier, from `0.5` to `3.0`. `1` is the natural pace of the voice.

**\--voice** *NAME*
:   Voice to use, as listed by **\--list-voices**.

**\--lang** *CODE*
:   Language of the messages and of the default voice (`en`, `fr`, `de` or `es`).

**\--voices-dir** *PATH*
:   Folder of voices of your own, read before PiperRead's own folders. An
    absolute path or one starting with `~/`; the folder must exist, otherwise
    the command stops with exit status `2`. It is read flat: a voice is two
    files, `NAME.onnx` and `NAME.onnx.json`, directly in it.

**\--normalize** *on*|*off*
:   `on` brings the voices to the same level with a gain measured once per
    voice (`off` by default).

**\--stop**
:   Stop the reading in progress.

**\--pause**, **\--resume**
:   Suspend the reading, then resume it where it stopped.

**\--diagnose**
:   Check the installation (engine, voice, audio, clipboard tools) without
    reading or playing anything, then exit. A last line says whether the
    graphical interface (**piperread-gui**) is present and, when it is not,
    which package to install; it never counts as a failure. Exit status is `1`
    when a check fails.

**\--list-voices**
:   Print the voices on offer, with their size and licence. The first line is
    the exact command that installs the recommended voice of the current
    language, followed by "(installed)" when it already is. No network access. The installed voices follow, each with its folder.

**\--download-voice** [*NAME*...]
:   Download the named voices into the voice directory. Without a name,
    offer the voice of the current language. With a chosen voices folder, the voices go into it; the command stops with exit status `1` when that folder is not writable.

**\--version**
:   Print the version and exit.

**\--help**
:   Print a summary of the options, in the language of the messages,
    and exit.

# CONFIGURATION

Each setting (`speed`, `voice`, `lang`, `voices_dir`, `normalize`) is taken from the first of these
sources that defines it:

1. the command-line option;
2. the environment variable `PIPERREAD_SPEED`, `PIPERREAD_VOICE`, `PIPERREAD_LANG`, `PIPERREAD_VOICES_DIR` or `PIPERREAD_NORMALIZE`;
3. the configuration file.

The setting `telemetry` (`on` or `off`, `off` by default) has no command-line
option: it is taken from the environment variable `PIPERREAD_TELEMETRY`, then
from the configuration file. It controls the usage events of the inference
library that the engine pulls in (onnxruntime), which are turned off by default
so that reading stays offline.

The setting `voices_dir` names a folder of voices of your own, read before
PiperRead's own folders: a voice present in both comes from yours.
**\--download-voice** saves into it and **\--diagnose** names it. It has the
option **\--voices-dir**.

The setting `normalize` (`on` or `off`, `off` by default) brings the voices to the same
level: each voice is measured once, the first time it is read, and the
measurement is kept in `$XDG_STATE_HOME/piperread/voice-levels`. It has the
option **\--normalize**. It is not a volume control. It was measured on Linux only.

# GRAPHICAL INTERFACE

The **piperread-gui** package provides a tray interface that starts with the session, keeps the voice loaded and adds pause, resume and sentence-by-sentence navigation. It is a separate package that depends on **piperread**: the "all in one" archive of the download page holds both, and one command installs them together (the installation guide gives it for each distribution).

The interface is started with the command `piperread-gui`, or from the PiperRead entry of the applications menu. It is driven with **piperread-gui** {**\--play** | **\--pause** | **\--resume** | **\--stop** | **\--next** | **\--previous** | **\--quit**}; except **\--play**, these commands report an error when no interface is running. With no voice installed, it opens a window that offers to download one; nothing is downloaded before the click on Download.

From a clone of the repository, once the environment in `gui/` is set up, the command is `gui/.venv/bin/python3 -m piperread_gui.app`. **piperread** itself never starts the interface.

# FILES

`$XDG_CONFIG_HOME/piperread/piperread.conf`
:   Configuration file, `~/.config/piperread/piperread.conf` when
    `XDG_CONFIG_HOME` is unset.

`$XDG_DATA_HOME/piperread/voices/`
:   Downloaded voices, `~/.local/share/piperread/voices/` when `XDG_DATA_HOME`
    is unset.

`$XDG_STATE_HOME/piperread/voice-levels`
:   Level measured for each voice, `~/.local/state/piperread/voice-levels` when
    `XDG_STATE_HOME` is unset. Written when `normalize` is `on`.

`/usr/lib/piperread/venv`
:   Python environment holding the Piper engine, for an installation by package.

# VOICES

The voices come from the Piper catalogue,
<https://huggingface.co/rhasspy/piper-voices>. Each voice has its own licence,
shown by **\--list-voices**. Samples can be heard at
<https://rhasspy.github.io/piper-samples/>.

In the sound mixer, the playback appears as « PiperRead », with the
launcher and with the interface; **\--diagnose** says the name. PiperRead sets
`PIPEWIRE_PROPS` before it opens the stream and keeps your value when you set
one. The mixer remembers a volume by application name, so the volume of that
stream restarts from the default one the first time. Checked with PipeWire and
its PulseAudio layer; PulseAudio alone, ALSA alone, macOS and Windows not
checked.

# PLATFORMS

On Linux, PiperRead ships as native packages: **Debian** and Ubuntu (`sudo apt install ./piperread_*_all.deb`), **Fedora** (`sudo dnf install ./piperread-*.noarch.rpm`), **openSUSE** Leap (`sudo zypper install ./piperread-*.noarch.rpm`) and **Arch** Linux (`sudo pacman -U ./piperread-*.pkg.tar.zst`), validated in containers: installation, update, diagnosis and removal on Debian 12 and 13, Ubuntu 22.04 and 24.04, Fedora 44 and Arch Linux; installation, diagnosis and removal on openSUSE Leap 16.0. A container proves neither the sound, nor the clipboard, nor the menu entry, nor the display. On **Windows** only the graphical interface exists, as the self-contained folder `piperread-gui-windows.zip`; it is an executable built on Windows and tried without a screen, with no automated test matrix.

# EXIT STATUS

`0` on success, `1` when a dependency, the engine or a voice is missing or a
diagnostic check fails, `2` on a usage error.

# AUTHOR

Ronan Davalan. Source and issues: <https://github.com/RonanDavalan/PiperRead>.

# LICENSE

MIT.

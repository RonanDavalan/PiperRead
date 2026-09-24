% PIPERREAD(1) piperread | User Commands
% Ronan Davalan
% 2026-09-21

# NAME

piperread - read the selected or copied text aloud, offline, with the Piper engine

# SYNOPSIS

**piperread** [*auto* | *selection* | *clipboard*] [**\--speed** *X*] [**\--voice** *NAME*] [**\--lang** *CODE*]

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

**\--stop**
:   Stop the reading in progress.

**\--pause**, **\--resume**
:   Suspend the reading, then resume it where it stopped.

**\--diagnose**
:   Check the installation (engine, voice, audio, clipboard tools) without
    reading or playing anything, then exit. Exit status is `1` when a check
    fails.

**\--list-voices**
:   Print the voices on offer, with their licence. No network access.

**\--download-voice** [*NAME*...]
:   Download the named voices into the voice directory. Without a name,
    offer the voice of the current language.

**\--version**
:   Print the version and exit.

**\--help**
:   Print a summary of the options, in the language of the messages,
    and exit.

# CONFIGURATION

Each setting (`speed`, `voice`, `lang`) is taken from the first of these
sources that defines it:

1. the command-line option;
2. the environment variable `PIPERREAD_SPEED`, `PIPERREAD_VOICE` or `PIPERREAD_LANG`;
3. the configuration file.

The setting `telemetry` (`on` or `off`, `off` by default) has no command-line
option: it is taken from the environment variable `PIPERREAD_TELEMETRY`, then
from the configuration file. It controls the usage events of the inference
library that the engine pulls in (onnxruntime), which are turned off by default
so that reading stays offline.

# GRAPHICAL INTERFACE

The optional **piperread-gui** package provides a tray interface, started with the command `piperread-gui`. From a clone of the repository, once the environment in `gui/` is set up, the command is `gui/.venv/bin/python3 -m piperread_gui.app`. **piperread** itself never starts it.

# FILES

`$XDG_CONFIG_HOME/piperread/piperread.conf`
:   Configuration file, `~/.config/piperread/piperread.conf` when
    `XDG_CONFIG_HOME` is unset.

`$XDG_DATA_HOME/piperread/voices/`
:   Downloaded voices, `~/.local/share/piperread/voices/` when `XDG_DATA_HOME`
    is unset.

`/usr/lib/piperread/venv`
:   Python environment holding the Piper engine, for an installation by package.

# VOICES

The voices come from the Piper catalogue,
<https://huggingface.co/rhasspy/piper-voices>. Each voice has its own licence,
shown by **\--list-voices**. Samples can be heard at
<https://rhasspy.github.io/piper-samples/>.

# EXIT STATUS

`0` on success, `1` when a dependency, the engine or a voice is missing or a
diagnostic check fails, `2` on a usage error.

# AUTHOR

Ronan Davalan. Source and issues: <https://github.com/RonanDavalan/PiperRead>.

# LICENSE

MIT.

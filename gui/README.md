# PiperRead — interface

A standalone Python project, separate from the Bash core (`read.sh`). The
interface never links the Piper engine into its own process: it drives it as an
external program, through the HTTP server Piper itself provides
(`piper.http_server`), started as a subprocess by `piper_server_entry.py` with
the engine's own interpreter and bound to `127.0.0.1` only. Keeping the engine
in a separate process is what keeps its GPL-3.0-or-later code out of this one.

The interface is the comfortable way to use PiperRead; the "Read the selection"
launcher (`read.sh auto`) stays the minimal way, independent of it. Neither
drives the other. The interface starts with your session (on by default; the
"Start with the session" box in the settings turns it off) and keeps the voice
loaded while it runs: reading starts without reloading the engine, and the next
sentence is synthesized while the current one plays. The server stops with the
interface, even if the interface disappears abruptly.

What it does: a tray icon and menu (Play, Pause, Stop, Previous/Next sentence,
Settings, Quit) wired to the reading chain (capture, Markdown cleanup, sentence
splitting, server, audio). A left click on the icon plays, pauses or resumes
according to the state. The text read is the mouse selection, or the clipboard
when nothing is selected (Linux, the same order as the core's `auto` mode; the
clipboard only on Windows), stripped of Markdown markup by the same rules as
`utils/cleaner.sh`. Every label comes from the same `lang/*.txt` files as the
core. The configuration (`piperread.conf`, the same `speed`/`voice`/`lang` keys,
the same order of priority) is read and written in Python (`config.py`); the
settings dialog writes it for real, and the chosen speed applies to synthesis
(`length_scale`). Linux packages (`piperread-gui`) and a Windows executable
(`packaging/windows/`) are available.

## Layout

```
gui/
├── pyproject.toml          — metadata and dependencies (PySide6, requests, pysbd, sounddevice)
├── piperread_gui/
│   ├── clipboard.py        — capture: mouse selection, then clipboard (wl-paste, then xsel, the core's order)
│   ├── cleaner.py          — Markdown markup removal (port of `utils/cleaner.sh`)
│   ├── sentences.py        — sentence splitting (pysbd, languages en/fr/de/es)
│   ├── server.py           — lifecycle of Piper's local HTTP server
│   ├── piper_server_entry.py — runs the server in the engine's process: telemetry off, watches the interface, UTF-8 paths on Windows
│   ├── synth_client.py     — HTTP client for /synthesize, with an optional `length_scale`
│   ├── player.py           — plays the received WAV (sounddevice), interruptible (stop, pause)
│   ├── flatfile.py         — reads "key=value" files without executing them (port of `utils/flatfile.sh`)
│   ├── config.py           — resolution and writing of `piperread.conf` (port of `utils/config.sh`)
│   ├── i18n.py             — loads the same `lang/*.txt` as the core, plus the `gui_*` keys
│   ├── controller.py       — reading state, server kept loaded, next sentence prepared, current settings
│   ├── notifier.py         — desktop notification through `notify-send`, independent of the tray
│   ├── tray.py             — tray icon, translated menu, detection of a missing tray host
│   ├── settings_dialog.py  — settings dialog (voice, speed, language, start with the session)
│   ├── autostart.py        — start with the session: XDG autostart (Linux), Run key (Windows)
│   ├── control_server.py   — local control channel: Unix socket (POSIX), token-protected TCP on loopback (Windows)
│   ├── control_client.py   — sends a command to the running interface
│   ├── frozen.py           — real folder of the frozen executable (PyInstaller), instead of `Path(__file__)`
│   ├── app.py              — entry point: resolves the configuration, assembles tray, controller and Qt loop
│   └── cli.py              — command-line test loop, without a window
├── packaging/windows/      — PyInstaller `.spec` files, `.ico` icon, `README.txt` shipped with the Windows package
└── tests/                  — unit tests (pytest), with no network or audio hardware needed
```

## Running it from a clone

The clone must already have the core installed (`../piper-env/` present, as for
`read.sh`). The HTTP server is an extra of the engine, not installed by default:

```bash
cd ~/git/PiperRead/PiperRead/piper-env
bin/pip install "piper-tts[http]"
```

Set up the interface environment, then run the unit tests:

```bash
cd ~/git/PiperRead/PiperRead/gui
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
env -u LD_LIBRARY_PATH QT_QPA_PLATFORM=offscreen python3 -m pytest
```

`LD_LIBRARY_PATH` is unset for the reason given below (system Qt libraries in
conflict); `QT_QPA_PLATFORM=offscreen` lets the tray tests (`test_tray.py`) run
without a real display.

Run the interface (tray icon and menu), after copying some text:

```bash
cd ~/git/PiperRead/PiperRead/gui
source .venv/bin/activate
python3 -m piperread_gui.app
```

With no option, the voice, the speed and the language are resolved in the same
order as `read.sh`: the variables `PIPERREAD_VOICE`/`PIPERREAD_SPEED`/
`PIPERREAD_LANG`, then `$XDG_CONFIG_HOME/piperread/piperread.conf` (the same
keys), then the first voice found in `../voices/*.onnx` (and English for the
language, unless the system locale says otherwise). `--lang` and `--speed`
override this for the instance being launched, for example
`python3 -m piperread_gui.app --lang de --speed 1,5`. `--model` stands for the
voice option (a direct path to an `.onnx` file rather than a name to resolve)
and takes precedence over everything else. The "Settings…" menu entry opens a
dialog (voice, speed, language, start with the session) that rewrites
`piperread.conf` without touching the rest of its content.

A test loop without a window, for the whole chain: copy some text, then

```bash
cd ~/git/PiperRead/PiperRead/gui
source .venv/bin/activate
python3 -m piperread_gui.cli --lang fr
```

`--model <path>` forces a given voice; without it, the first voice found in
`../voices/*.onnx` is used. `--lang` picks the language of the sentence splitter
among `en`, `fr`, `de`, `es` (default `fr`). `cli.py` does not read
`piperread.conf`: it is a minimal test loop, and the configuration is resolved
in `app.py`.

**Platform trap (seen on KDE Plasma):** if the shell defines `LD_LIBRARY_PATH`
(for CUDA, for example), it hides the Qt libraries bundled with PySide6 in favour
of the older ones of the system, with an immediate crash (`undefined symbol`, then
a segmentation fault). Unset the variable before launching the interface:

```bash
env -u LD_LIBRARY_PATH python3 -m piperread_gui.app --lang fr
```

## Start with the session

At the first launch, the interface writes its startup entry
(`~/.config/autostart/piperread-gui.desktop` from a clone; the package installs
`/etc/xdg/autostart/piperread-gui.desktop`) and a marker,
`$XDG_STATE_HOME/piperread/autostart-default-applied`: a choice made afterwards in
the settings is never overwritten. On Windows, the value `PiperRead` under
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` plays the same role, and a
deactivation made in the Startup tab of the Task Manager is respected.

## Controlling a running interface

`piperread-gui --play` reads through the running instance, or starts it and then
reads if none is running; this is the command of the package's menu launcher. The
six other options (`--pause`, `--resume`, `--stop`, `--next`, `--previous`,
`--quit`) act on the running instance and report an error when there is none.

Tray menu (right click), labels in the resolved language: Play, Pause, Stop,
Previous/Next sentence (active while reading or paused), Settings…, Quit. "Play"
during a pause resumes where the reading stopped. A left click on the icon plays
when stopped, pauses while reading, resumes when paused. On a desktop that
exposes no system notification area (GNOME without the "AppIndicator and
KStatusNotifierItem Support" extension), a single desktop notification explains
the situation at startup; the interface keeps working and the options above
still drive it.

The channel behind those options is a Unix socket on POSIX systems
(`$XDG_RUNTIME_DIR/piperread/gui.sock`, or `/tmp/piperread-$UID/gui.sock`), and a
TCP socket on `127.0.0.1` protected by a random one-time token on Windows, where
Unix sockets are not reliable.

## Checks

The interface code must contain no direct `import` of the `piper` module:

```bash
cd ~/git/PiperRead/PiperRead
grep -rnE 'import[[:space:]]piper' gui/
```

Network binding, during a reading, in another terminal:

```bash
ss -tlnp
```

The server port only appears on `127.0.0.1`, never on `0.0.0.0`.

## Windows package

Two self-contained folder-mode executables (`piperread-gui.exe` and, in the
`piper-http-server\` subfolder, `piper-http-server.exe`, a separate process with
the same GPL boundary as `server.py`), frozen by PyInstaller on a real Windows
(no cross-build from Linux). Starting the build requires the code to be pushed to
`main`:

```bash
gh workflow run build-windows-gui.yml --repo RonanDavalan/PiperRead
gh run list --repo RonanDavalan/PiperRead --workflow build-windows-gui.yml --limit 1
gh run download <run-id> --repo RonanDavalan/PiperRead
```

The archive produced (`piperread-gui-windows.zip`) holds the two executables with
their `_internal\` folders, `lang/`, `piperread.ico`, an empty `voices/` folder
(voices are never shipped) and `README.txt` (English, how to launch it). The
manifest of `piper-http-server.exe` declares the UTF-8 code page for the whole
process, so that `espeak-ng` finds its data whatever the name of the Windows
account, accents included.

A dry run on Linux (an ELF binary, unusable as it is, but it reveals a path
resolution or bundled-data trap before spending a Windows CI run):

```bash
cd gui
.venv/bin/pip install pyinstaller "piper-tts[http]"
env -u LD_LIBRARY_PATH .venv/bin/pyinstaller --noconfirm --distpath /tmp/dist-essai packaging/windows/piper-http-server.spec
env -u LD_LIBRARY_PATH .venv/bin/pyinstaller --noconfirm --distpath /tmp/dist-essai packaging/windows/piperread-gui.spec
```

PiperRead for Windows
======================

This folder is self-contained: no separate Python install, no separate
Piper install. Two programs are included:

  piperread-gui.exe                        the application itself (tray
                                           icon and menu)
  piper-http-server\piper-http-server.exe  the Piper speech engine, started
                                           automatically by piperread-gui.exe;
                                           never run it by hand

Keep the folder whole: each program needs the "_internal" folder next to it.

Before the first run
---------------------

No voice is shipped. With no voice installed, the first launch opens a
window called "Download a voice": choose a voice and click Download.
Nothing is downloaded before that click.

To add a voice by hand instead, put two files with the same name,
"<name>.onnx" and "<name>.onnx.json", in the "voices" folder. Voices can
be downloaded from:

  https://huggingface.co/rhasspy/piper-voices

Running
-------

Double-click piperread-gui.exe. A tray icon appears; right-click it for
the menu (Play, Pause, Stop, Previous/Next sentence, Settings, Quit).
Copy some text to the clipboard, then left-click the icon: it plays when
stopped, pauses while playing, and resumes when paused. Markdown markup
(**bold**, # headings, [links](...)) is not read aloud.

The voice stays loaded while the application runs, so reading starts at
once. From the first run on, PiperRead starts with your Windows session;
untick "Start with the session" in Settings to stop that (the Startup tab
of the Task Manager shows the same setting). If you move the folder, run
piperread-gui.exe once from its new place.

Settings (voice, speed, language) are saved in the file below; the
Settings dialog also has a "Download a voice..." button:

  %USERPROFILE%\.config\piperread\piperread.conf

Nothing this application does reaches the network beyond the local
machine: the speech engine listens only on 127.0.0.1, and the usage events
of its inference library (onnxruntime) are turned off. To turn them back
on, add the line telemetry=on to piperread.conf.

This is a community build, not signed with a certificate recognized by
Windows: SmartScreen may warn on first launch ("Windows protected your
PC"). Choose "More info", then "Run anyway".


Licenses
--------

PiperRead itself is released under the MIT license (licenses\PiperRead-MIT.txt).
This folder also contains two programs and libraries that are not covered
by it. Their license texts are in the "licenses" folder next to this file,
and licenses\COMPONENTS.txt gives the exact version of each component of
this build.

  Piper speech engine (piper-http-server\piper-http-server.exe)
      SPDX: GPL-3.0-or-later      text: licenses\GPL-3.0.txt
      It is a separate program that piperread-gui.exe starts as its own
      process; the two are only distributed together in this folder.
      It includes eSpeak NG (data and library), also under the GPL.

  Qt for Python (PySide6, shiboken6) and the Qt 6 libraries in
  _internal\PySide6
      SPDX: LGPL-3.0-only         texts: licenses\LGPL-3.0.txt and
                                         licenses\GPL-3.0.txt
      piperread-gui.exe uses these libraries, which are covered by the
      LGPL. They are separate files (the .dll files in _internal\PySide6):
      you may replace them with a modified, interface-compatible version
      and run the application with it.

Source code (written offer)
---------------------------

The complete corresponding source code of the GPL and LGPL components
above is available at no charge, for as long as this version of PiperRead
is distributed and for at least three years:

  Piper (piper-tts, the version in licenses\COMPONENTS.txt):
      https://github.com/OHF-voice/piper1-gpl
  Qt for Python (PySide6, the version in licenses\COMPONENTS.txt):
      https://code.qt.io/cgit/pyside/pyside-setup.git/
      Qt 6 libraries: https://code.qt.io/
  PiperRead (MIT, with the .spec files that build this folder):
      https://github.com/RonanDavalan/PiperRead

If one of these addresses no longer serves the source, open an issue at
https://github.com/RonanDavalan/PiperRead/issues and a copy is sent.

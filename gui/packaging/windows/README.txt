PiperRead for Windows
======================

This folder is self-contained: no separate Python install, no separate
Piper install. Two programs are included:

  piperread-gui.exe        the application itself (tray icon and menu)
  piper-http-server.exe    the Piper speech engine, started automatically
                            by piperread-gui.exe; never run it by hand

Before the first run
---------------------

Put a voice model in the "voices" folder: two files with the same name,
"<name>.onnx" and "<name>.onnx.json". Voices can be downloaded from:

  https://huggingface.co/rhasspy/piper-voices

Running
-------

Double-click piperread-gui.exe. A tray icon appears; right-click it for
the menu (Play, Pause, Resume, Stop, Previous/Next sentence, Settings,
Quit). Copy some text to the clipboard, then choose "Play" from the menu.

Settings (voice, speed, language) are saved in:

  %USERPROFILE%\.config\piperread\piperread.conf

Nothing this application does reaches the network beyond the local
machine: the speech engine listens only on 127.0.0.1.

This is a community build, not signed with a certificate recognized by
Windows: SmartScreen may warn on first launch ("Windows protected your
PC"). Choose "More info", then "Run anyway".

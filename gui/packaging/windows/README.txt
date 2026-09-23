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

Put a voice model in the "voices" folder: two files with the same name,
"<name>.onnx" and "<name>.onnx.json". Voices can be downloaded from:

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

Settings (voice, speed, language) are saved in:

  %USERPROFILE%\.config\piperread\piperread.conf

Nothing this application does reaches the network beyond the local
machine: the speech engine listens only on 127.0.0.1, and the usage events
of its inference library (onnxruntime) are turned off. To turn them back
on, add the line telemetry=on to piperread.conf.

This is a community build, not signed with a certificate recognized by
Windows: SmartScreen may warn on first launch ("Windows protected your
PC"). Choose "More info", then "Run anyway".

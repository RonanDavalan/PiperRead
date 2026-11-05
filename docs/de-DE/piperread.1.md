% PIPERREAD(1) piperread | Benutzerbefehle
% Ronan Davalan
% 2026-09-29

# NAME

piperread - markierten oder kopierten Text offline mit der Piper-Engine vorlesen

# ÜBERSICHT

**piperread** [*auto* | *selection* | *clipboard*] [**\--speed** *X*] [**\--voice** *NAME*] [**\--lang** *CODE*] [**\--voices-dir** *PFAD*] [**\--normalize** *on*|*off*]

**piperread** {**\--stop** | **\--pause** | **\--resume**}

**piperread** {**\--version** | **\--diagnose** | **\--help**}

**piperread** **\--list-voices**

**piperread** **\--download-voice** [*NAME*...]

# BESCHREIBUNG

**piperread** liest den Text vor, den Sie mit der Maus markiert oder in die
Zwischenablage kopiert haben, unter Wayland ebenso wie unter X11. Die Sprache
wird lokal von der neuronalen Piper-Engine erzeugt: Weder Text noch Audio
verlassen jemals den Rechner. Markdown-Zeichen werden vor dem Vorlesen
entfernt, sodass ein formatierter Text wie Fließtext gesprochen wird.

Es läuft immer nur ein Vorlesevorgang: Ein erneuter Aufruf von **piperread**
beendet den vorherigen. Der Befehl ist dafür gedacht, an ein Tastenkürzel der
Arbeitsumgebung gebunden zu werden.

Die Engine ist nicht Teil des Programms selbst. Sie wird getrennt mit
`pip install piper-tts` installiert; dieser Schritt braucht eine
Netzwerkverbindung und Speicherplatz. Weder die Pakete noch die Engine
enthalten eine Stimme: Eine Stimme wird einmal mit **\--download-voice**
heruntergeladen und funktioniert danach ohne Netzwerk.

# TEXTQUELLE

*selection*
:   Den mit der Maus markierten Text vorlesen.

*clipboard*
:   Den in die Zwischenablage kopierten Text vorlesen.

*auto*
:   Die Voreinstellung. Die Mausauswahl vorlesen, oder die Zwischenablage,
    wenn nichts markiert ist. Ein Inhalt, der nur aus Leerzeichen und
    Zeilenumbrüchen besteht, gilt als leer.

# OPTIONEN

**\--speed** *X*
:   Geschwindigkeitsfaktor von `0.5` bis `3.0`. `1` ist das natürliche Tempo
    der Stimme.

**\--voice** *NAME*
:   Zu verwendende Stimme, wie **\--list-voices** sie auflistet.

**\--lang** *CODE*
:   Sprache der Meldungen und der Standardstimme (`en`, `fr`, `de` oder `es`).

**\--voices-dir** *PFAD*
:   Ordner mit eigenen Stimmen, der vor den Ordnern von PiperRead gelesen wird.
    Ein absoluter Pfad oder einer, der mit `~/` beginnt; der Ordner muss
    existieren, sonst bricht der Befehl mit Exitcode `2` ab. Er wird flach
    gelesen: Eine Stimme besteht aus zwei Dateien, `NAME.onnx` und
    `NAME.onnx.json`, die direkt darin liegen.

**\--normalize** *on*|*off*
:   `on` bringt die Stimmen mit einer einmal pro Stimme gemessenen Verstärkung
    auf denselben Pegel (standardmäßig `off`).

**\--stop**
:   Das laufende Vorlesen beenden.

**\--pause**, **\--resume**
:   Das Vorlesen anhalten und an der Stelle fortsetzen, an der es stehen
    geblieben ist.

**\--diagnose**
:   Die Installation prüfen (Engine, Stimme, Audio, Zwischenablage-Werkzeuge),
    ohne etwas vorzulesen oder abzuspielen, und dann beenden. Eine letzte Zeile
    sagt, ob die grafische Oberfläche (**piperread-gui**) vorhanden ist und, wenn
    nicht, welches Paket zu installieren ist; sie zählt nie als Fehler. Der
    Exit-Status ist `1`, wenn eine Prüfung fehlschlägt.

**\--list-voices**
:   Die angebotenen Stimmen mit ihrer Größe und Lizenz ausgeben. Die erste Zeile
    ist der genaue Befehl, der die empfohlene Stimme der aktuellen Sprache
    installiert, gefolgt von „(installiert)“, wenn sie schon vorhanden ist. Kein
    Netzwerkzugriff. Danach folgen die installierten Stimmen, jede mit ihrem Ordner.

**\--download-voice** [*NAME*...]
:   Die genannten Stimmen in das Stimmenverzeichnis herunterladen. Ohne Namen
    wird die Stimme der aktuellen Sprache angeboten. Ist ein Stimmenordner gewählt, landen die Stimmen darin; der Befehl bricht mit Exitcode `1` ab, wenn dieser Ordner nicht beschreibbar ist.

**\--version**
:   Die Version ausgeben und beenden.

**\--help**
:   Eine Übersicht der Optionen in der Sprache der Meldungen ausgeben und
    beenden.

# KONFIGURATION

Jede Einstellung (`speed`, `voice`, `lang`, `voices_dir`, `normalize`) stammt aus der ersten der folgenden
Quellen, die sie definiert:

1. die Kommandozeilenoption;
2. die Umgebungsvariable `PIPERREAD_SPEED`, `PIPERREAD_VOICE`, `PIPERREAD_LANG`, `PIPERREAD_VOICES_DIR` oder `PIPERREAD_NORMALIZE`;
3. die Konfigurationsdatei.

Die Einstellung `telemetry` (`on` oder `off`, standardmäßig `off`) hat keine
Befehlszeilenoption: Sie wird der Umgebungsvariable `PIPERREAD_TELEMETRY`
entnommen, danach der Konfigurationsdatei. Sie steuert die Nutzungsereignisse
der Inferenzbibliothek, die die Engine mitbringt (onnxruntime); standardmäßig
sind sie ausgeschaltet, damit das Vorlesen offline bleibt.

Die Einstellung `voices_dir` benennt einen Ordner mit eigenen Stimmen, der
vor den Ordnern von PiperRead gelesen wird: Eine Stimme, die in beiden vorkommt,
stammt aus Ihrem. **\--download-voice** speichert darin, und **\--diagnose**
nennt ihn. Sie hat die Option **\--voices-dir**.

Die Einstellung `normalize` (`on` oder `off`, standardmäßig `off`) bringt die
Stimmen auf denselben Pegel: Jede Stimme wird beim ersten Vorlesen einmal
gemessen, und die Messung wird in `$XDG_STATE_HOME/piperread/voice-levels`
gespeichert. Sie hat die Option **\--normalize**. Es ist keine
Lautstärkeregelung. Gemessen wurde nur unter Linux.

# GRAFISCHE OBERFLÄCHE

Das Paket **piperread-gui** stellt eine Tray-Oberfläche bereit, die mit der Sitzung startet, die Stimme geladen hält und Pause, Fortsetzen und satzweise Navigation hinzufügt. Es ist ein separates Paket, das von **piperread** abhängt: Das „Alles-in-einem“-Archiv der Download-Seite enthält beide, und ein einziger Befehl installiert sie zusammen (die Installationsanleitung nennt ihn für jede Distribution).

Die Oberfläche wird mit dem Befehl `piperread-gui` oder über den Eintrag PiperRead im Anwendungsmenü gestartet. Gesteuert wird sie mit **piperread-gui** {**\--play** | **\--pause** | **\--resume** | **\--stop** | **\--next** | **\--previous** | **\--quit**}; außer **\--play** melden diese Befehle einen Fehler, wenn keine Oberfläche läuft. Ohne installierte Stimme öffnet sie ein Fenster, das anbietet, eine herunterzuladen; vor dem Klick auf Herunterladen wird nichts heruntergeladen.

Aus einem Klon des Repositorys lautet der Befehl, sobald die Umgebung in `gui/` eingerichtet ist, `gui/.venv/bin/python3 -m piperread_gui.app`. **piperread** selbst startet die Oberfläche nie.

# DATEIEN

`$XDG_CONFIG_HOME/piperread/piperread.conf`
:   Konfigurationsdatei, `~/.config/piperread/piperread.conf`, wenn
    `XDG_CONFIG_HOME` nicht gesetzt ist.

`$XDG_DATA_HOME/piperread/voices/`
:   Heruntergeladene Stimmen, `~/.local/share/piperread/voices/`, wenn
    `XDG_DATA_HOME` nicht gesetzt ist.

`$XDG_STATE_HOME/piperread/voice-levels`
:   Gemessener Pegel jeder Stimme, `~/.local/state/piperread/voice-levels`,
    wenn `XDG_STATE_HOME` nicht gesetzt ist. Wird geschrieben, wenn `normalize`
    `on` ist.

`/usr/lib/piperread/venv`
:   Python-Umgebung mit der Piper-Engine, bei einer Installation per Paket.

# STIMMEN

Die Stimmen stammen aus dem Piper-Katalog,
<https://huggingface.co/rhasspy/piper-voices>. Jede Stimme hat ihre eigene
Lizenz, die **\--list-voices** anzeigt. Hörproben finden sich unter
<https://rhasspy.github.io/piper-samples/>.

Im Klang-Mixer erscheint die Wiedergabe unter dem Namen « PiperRead », mit
dem Starter wie mit der Oberfläche; **\--diagnose** nennt den Namen. PiperRead
setzt `PIPEWIRE_PROPS`, bevor es den Stream öffnet, und behält Ihren Wert, falls
Sie einen gesetzt haben. Der Mixer merkt sich die Lautstärke pro
Anwendungsname, daher beginnt die Lautstärke dieses Streams beim ersten Mal
wieder beim Standardwert. Geprüft mit PipeWire und seiner PulseAudio-Schicht;
PulseAudio allein, ALSA allein, macOS und Windows wurden nicht geprüft.

# PLATTFORMEN

Unter Linux wird PiperRead als native Pakete ausgeliefert: **Debian** und Ubuntu (`sudo apt install ./piperread_*_all.deb`), **Fedora** (`sudo dnf install ./piperread-*.noarch.rpm`), **openSUSE** Leap (`sudo zypper install ./piperread-*.noarch.rpm`) und **Arch** Linux (`sudo pacman -U ./piperread-*.pkg.tar.zst`), im Container validiert: Installation, Aktualisierung, Diagnose und Entfernung unter Debian 12 und 13, Ubuntu 22.04 und 24.04, Fedora 44 und Arch Linux; Installation, Diagnose und Entfernung unter openSUSE Leap 16.0. Ein Container belegt weder den Ton noch die Zwischenablage, den Menüeintrag oder die Anzeige. Unter **Windows** gibt es nur die grafische Oberfläche, als eigenständigen Ordner `piperread-gui-windows.zip`; sie ist eine unter Windows gebaute ausführbare Datei, die ohne Bildschirm ausprobiert wurde, ohne automatisierte Testmatrix.

# EXIT-STATUS

`0` bei Erfolg, `1`, wenn eine Abhängigkeit, die Engine oder eine Stimme fehlt
oder eine Prüfung der Diagnose fehlschlägt, `2` bei einem Aufruffehler.

# AUTOR

Ronan Davalan. Quellcode und Fehlerverfolgung: <https://github.com/RonanDavalan/PiperRead>.

# LIZENZ

MIT.

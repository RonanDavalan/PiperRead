% PIPERREAD(1) piperread | Benutzerbefehle
% Ronan Davalan
% 2026-09-21

# NAME

piperread - markierten oder kopierten Text offline mit der Piper-Engine vorlesen

# ÜBERSICHT

**piperread** [*auto* | *selection* | *clipboard*] [**\--speed** *X*] [**\--voice** *NAME*] [**\--lang** *CODE*]

**piperread** {**\--stop** | **\--pause** | **\--resume**}

**piperread** {**\--version** | **\--diagnose**}

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

**\--stop**
:   Das laufende Vorlesen beenden.

**\--pause**, **\--resume**
:   Das Vorlesen anhalten und an der Stelle fortsetzen, an der es stehen
    geblieben ist.

**\--diagnose**
:   Die Installation prüfen (Engine, Stimme, Audio, Zwischenablage-Werkzeuge),
    ohne etwas vorzulesen oder abzuspielen, und dann beenden. Der Exit-Status
    ist `1`, wenn eine Prüfung fehlschlägt.

**\--list-voices**
:   Die angebotenen Stimmen mit ihrer Lizenz ausgeben. Kein Netzwerkzugriff.

**\--download-voice** [*NAME*...]
:   Die genannten Stimmen in das Stimmenverzeichnis herunterladen. Ohne Namen
    wird die Stimme der aktuellen Sprache angeboten.

**\--version**
:   Die Version ausgeben und beenden.

# KONFIGURATION

Jede Einstellung (`speed`, `voice`, `lang`) stammt aus der ersten der folgenden
Quellen, die sie definiert:

1. die Kommandozeilenoption;
2. die Umgebungsvariable `PIPERREAD_SPEED`, `PIPERREAD_VOICE` oder `PIPERREAD_LANG`;
3. die Konfigurationsdatei.

# DATEIEN

`$XDG_CONFIG_HOME/piperread/piperread.conf`
:   Konfigurationsdatei, `~/.config/piperread/piperread.conf`, wenn
    `XDG_CONFIG_HOME` nicht gesetzt ist.

`$XDG_DATA_HOME/piperread/voices/`
:   Heruntergeladene Stimmen, `~/.local/share/piperread/voices/`, wenn
    `XDG_DATA_HOME` nicht gesetzt ist.

`/usr/lib/piperread/venv`
:   Python-Umgebung mit der Piper-Engine, bei einer Installation per Paket.

# STIMMEN

Die Stimmen stammen aus dem Piper-Katalog,
<https://huggingface.co/rhasspy/piper-voices>. Jede Stimme hat ihre eigene
Lizenz, die **\--list-voices** anzeigt. Hörproben finden sich unter
<https://rhasspy.github.io/piper-samples/>.

# EXIT-STATUS

`0` bei Erfolg, `1`, wenn eine Abhängigkeit, die Engine oder eine Stimme fehlt
oder eine Prüfung der Diagnose fehlschlägt, `2` bei einem Aufruffehler.

# AUTOR

Ronan Davalan. Quellcode und Fehlermeldungen: <https://github.com/RonanDavalan/PiperRead>.

# LIZENZ

MIT.

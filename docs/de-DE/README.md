# PiperRead

<p align="center">
  <img src="https://img.shields.io/static/v1?label=Version&message=v0.1.2-alpha&color=orange" alt="Version">
  <img src="https://img.shields.io/badge/Lizenz-MIT-green" alt="Lizenz">
  <img src="https://img.shields.io/badge/Plattform-Linux_(Wayland_|_X11)-black" alt="Unterstütztes OS">
  <img src="https://img.shields.io/badge/Engine-Piper_Neural_TTS-blueviolet" alt="Audio-Engine">
  <img src="https://img.shields.io/badge/Sprache-Python_|_Bash-blue" alt="Code">
</p>

[English](../../README.md) | [Français](../fr-FR/README.md) | **Deutsch** | [Español](../es-ES/README.md)

## Beschreibung

**PiperRead** ist eine leichtgewichtige Automatisierungslösung, die entwickelt wurde, um hochwertige neuronale Sprachsynthese (TTS) auf Linux-Desktops zu bringen.

**Offizielle Website**: [piperread.davalan.fr](https://piperread.davalan.fr)

Im Gegensatz zu Cloud-Lösungen arbeitet PiperRead dank der [Piper](https://github.com/OHF-voice/piper1-gpl)-Engine vollständig offline (lokal). Es fungiert als Brücke zwischen Ihrer Desktop-Umgebung (Zwischenablage/Maus) und der Synthese-Engine.

Es ermöglicht das Vorlesen jedes mit der Maus ausgewählten oder in die Zwischenablage kopierten Textes, ohne dass ein komplexer Screenreader erforderlich ist.

## Anwendungsfälle

*   **Barrierefreiheit**: Schnelles Vorlesen von Inhalten für Menschen mit leichter Sehbehinderung oder Augenermüdung.
*   **Produktivität**: Anhören von Artikeln oder Dokumenten während der Erledigung einer anderen Aufgabe.
*   **Korrektur**: Vorlesen eigener Texte durch eine fremde Stimme, um Fehler zu erkennen.

## Hauptfunktionen

*   **Vollständige Privatsphäre**: 100% lokale Verarbeitung. Keine Daten werden an eine Cloud gesendet.
*   **Null Latenz**: Sofortige Wiedergabe, geeignet für Echtzeit-Nutzung.
*   **Universelle Kompatibilität**: Erkennt und adaptiert automatisch **Wayland** (Debian 12/13) oder **X11**.
*   **Intelligente Auswahl**: Priorisiert die Mausauswahl (primär) und wechselt zur Zwischenablage, wenn keine Auswahl aktiv ist.
*   **Isolation**: Läuft in einer eigenen virtuellen Python-Umgebung, um Ihr System nicht zu verunreinigen.

---

## Voraussetzungen

Stellen Sie vor der Installation sicher, dass Ihr System über die erforderlichen Audio- und Zwischenablage-Tools verfügt.

```bash
# Systemaktualisierung
sudo apt update

# Installation von Python, Audio und Zwischenablage-Tools
# (Installiert sowohl wl-clipboard für Wayland als auch xsel für X11, um Kompatibilität zu gewährleisten)
sudo apt install -y python3 python3-venv python3-pip alsa-utils wl-clipboard xsel libnotify-bin
```

---

## Installation

Da dieses Projekt auf großen Sprachmodellen und einer spezifischen virtuellen Umgebung basiert, müssen Sie das Projekt nach dem Klonen initialisieren.

### 1. Repository klonen

```bash
mkdir -p $HOME/git/piper
cd $HOME/git/piper
git clone https://github.com/RonanDavalan/PiperRead.git
cd PiperRead
```

### 2. Umgebung initialisieren (Kritisch)

Dieser Schritt erstellt die Python-Isolation und lädt das neuronale Sprachmodell herunter (Französisch - Siwis Medium).

```bash
# Erstellung der virtuellen Umgebung
python3 -m venv piper-env

# Installation der Piper TTS Engine
./piper-env/bin/pip install piper-tts

# Herunterladen des Sprachmodells
mkdir -p voices
cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json
cd ..
```

### 3. Berechtigungen konfigurieren

```bash
chmod 700 read.sh
```

### 4. Desktop-Integration (Icon und Menü)

Um PiperRead wie eine native Anwendung zu starten:

```bash
# Erstellung des Ordners für lokale Anwendungen
mkdir -p $HOME/.local/share/applications

# Kopieren der Desktop-Datei
cp Ressources/PiperRead.desktop $HOME/.local/share/applications/

# Aktualisierung der Menü-Datenbank
update-desktop-database $HOME/.local/share/applications
```

---

## Verwendung

### Methode 1: Mausauswahl (Empfohlen)

1.  **Markieren Sie Text** in einer beliebigen Anwendung (Browser, PDF, Editor).
2.  Klicken Sie auf das **PiperRead**-Symbol in Ihrem Menü (oder verwenden Sie Ihr benutzerdefiniertes Tastaturkürzel).
3.  Der Text wird sofort vorgelesen.

### Methode 2: Zwischenablage

1.  Kopieren Sie Text (**Strg+C**).
2.  Starten Sie PiperRead.

### Wiedergabe stoppen

*Aktuelle Alpha-Einschränkung*: Um die laufende Wiedergabe zu stoppen, führen Sie `pkill -f aplay` in einem Terminal aus.

---

## Qualität

Dieses Projekt entstand aus einer Entdeckung: der beeindruckenden Qualität der **Piper**-Engine für eine vollständig freie und lokale Lösung.

*   **Natürliche Sprachwiedergabe**: Die Wahl dieser neuronalen Technologie ermöglicht ein flüssiges und ruhiges Vorlesen, was das Zuhören auf Dauer angenehm macht.
*   **Leichte Architektur**: PiperRead ist keine schwere Anwendung, sondern ein minimalistischer Orchestrator. Es verbindet Ihren Desktop und die Audio-Engine mit einem fast nicht vorhandenen System-Fußabdruck.
*   **Saubere Installation**: Die strikte Verwendung von virtuellen Umgebungen (venv) garantiert, dass die Software isoliert bleibt und die Bibliotheken Ihres Hauptsystems nicht verändert.

---

## Projektursprung

Der Anstoß zu diesem Projekt kam von meinem Bruder, einem langjährigen Debian-Nutzer, der Piper als nützliche Lösung für lokales TTS identifizierte.

---

## Credits & "Vibe Coding"

Das Projekt **PiperRead** ist das Ergebnis einer hybriden **Mensch-KI**-Zusammenarbeit:

*   **Ronan Davalan**: Architekt und Schiedsrichter. Produktvision, Sicherheitsanforderungen, Projektrichtung, Validierung und Tests. Alle Architekturentscheidungen werden von ihm validiert.
*   **Claude Code (Anthropic)**: Systemingenieur und Hauptentwickler. Umsetzung der Bash-Skripte, der Dokumentation und der Website; technische Entscheidungen innerhalb der validierten Architektur. Hauptautor des Quellcodes.
*   **Google Gemini**: Synthetisierer und strategischer Berater. Unabhängige Architekturanalyse, Auflösung logischer Konflikte, Optimierung des Arbeitsablaufs, Gegenprüfung technischer Entscheidungen.
*   **Kern-Engine**: [Piper TTS](https://github.com/OHF-voice/piper1-gpl), lizenziert unter GPL-3.0-or-later. Es wird per `pip` auf Ihrem Rechner installiert und als externes Programm aufgerufen; PiperRead verteilt es nicht weiter.

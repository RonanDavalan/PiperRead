# PiperRead

<p align="center">
  <img src="https://img.shields.io/static/v1?label=Version&message=v0.1.2-alpha&color=orange" alt="Version">
  <img src="https://img.shields.io/badge/Licencia-MIT-green" alt="Licencia">
  <img src="https://img.shields.io/badge/Plataforma-Linux_(Wayland_|_X11)-black" alt="OS soportado">
  <img src="https://img.shields.io/badge/Motor-Piper_Neural_TTS-blueviolet" alt="Motor de audio">
  <img src="https://img.shields.io/badge/Lenguaje-Python_|_Bash-blue" alt="Código">
</p>

[🇺🇸 English](../../README.md) | [🇫🇷 Français](../fr-FR/README.md) | [🇩🇪 Deutsch](../de-DE/README.md) | **🇪🇸 Español**

## Descripción

**PiperRead** es una solución de automatización ligera diseñada para llevar la síntesis de voz neuronal (TTS) de alta calidad a los escritorios Linux.

🌐 **Sitio web oficial**: [piperread.davalan.fr](https://piperread.davalan.fr)

A diferencia de las soluciones en la nube, PiperRead funciona completamente sin conexión (local) gracias al motor [Piper](https://github.com/OHF-voice/piper1-gpl). Actúa como un puente entre su entorno de escritorio (portapapeles/ratón) y el motor de síntesis.

Permite leer en voz alta cualquier texto seleccionado con el ratón o copiado en el portapapeles, sin necesidad de un lector de pantalla complejo.

## Casos de uso

*   **Accesibilidad**: lectura rápida de contenidos para personas con discapacidad visual leve o fatiga visual.
*   **Productividad**: escucha de artículos o documentos mientras se realiza otra tarea.
*   **Corrección**: relectura de textos propios mediante una voz externa para detectar errores.

## Funcionalidades clave

*   **Privacidad total**: procesamiento 100% local. No se envían datos a ninguna nube.
*   **Latencia cero**: lectura instantánea adaptada para uso en tiempo real.
*   **Compatibilidad universal**: detecta y se adapta automáticamente a **Wayland** (Debian 12/13) o **X11**.
*   **Selección inteligente**: prioriza la selección del ratón (primaria) y cambia al portapapeles si no hay ninguna selección activa.
*   **Aislamiento**: se ejecuta en su propio entorno virtual de Python para no contaminar su sistema.

---

## 🛠️ Requisitos previos

Antes de la instalación, asegúrese de que su sistema dispone de las herramientas de audio y portapapeles necesarias.

```bash
# Actualización del sistema
sudo apt update

# Instalación de Python, audio y herramientas de portapapeles
# (Instala tanto wl-clipboard para Wayland como xsel para X11 para garantizar la compatibilidad)
sudo apt install -y python3 python3-venv python3-pip alsa-utils wl-clipboard xsel libnotify-bin
```

---

## 💾 Instalación

Dado que este proyecto se basa en modelos vocales pesados y un entorno virtual específico, debe inicializar el proyecto después de clonarlo.

### 1. Clonar el repositorio

```bash
mkdir -p $HOME/git/piper
cd $HOME/git/piper
git clone https://github.com/RonanDavalan/PiperRead.git
cd PiperRead
```

### 2. Inicializar el entorno (crítico)

Este paso crea el aislamiento de Python y descarga el modelo vocal neuronal (francés - Siwis Medium).

```bash
# Creación del entorno virtual
python3 -m venv piper-env

# Instalación del motor Piper TTS
./piper-env/bin/pip install piper-tts

# Descarga del modelo vocal
mkdir -p voices
cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/sharvard/medium/es_ES-sharvard-medium.onnx.json
cd ..
```

### 3. Configuración de permisos

```bash
chmod 700 read.sh
```

### 4. Integración en el escritorio (icono y menú)

Para lanzar PiperRead como una aplicación nativa:

```bash
# Creación de la carpeta de aplicaciones locales
mkdir -p $HOME/.local/share/applications

# Copia del archivo desktop
cp Ressources/PiperRead.desktop $HOME/.local/share/applications/

# Actualización de la base de datos de menús
update-desktop-database $HOME/.local/share/applications
```

---

## 🚀 Uso

### Método 1: Selección con ratón (recomendado)

1.  **Resalte texto** en cualquier aplicación (navegador, PDF, editor).
2.  Haga clic en el icono **PiperRead** en su menú (o use su atajo de teclado personalizado).
3.  El texto se lee inmediatamente.

### Método 2: Portapapeles

1.  Copie texto (**Ctrl+C**).
2.  Lance PiperRead.

### Detener la lectura

*Limitación Alpha actual*: para detener la lectura en curso, ejecute `pkill -f aplay` en una terminal.

---

## 💎 Calidad

Este proyecto nació de un descubrimiento: la calidad impresionante del motor **Piper** para una solución totalmente libre y local.

*   **Renderizado de voz natural**: la elección de esta tecnología neuronal permite una lectura fluida y pausada, haciendo la escucha cómoda a largo plazo.
*   **Arquitectura ligera**: PiperRead no es una aplicación pesada, sino un orquestador minimalista. Conecta su escritorio y el motor de audio con una huella de sistema casi nula.
*   **Instalación limpia**: el uso estricto de entornos virtuales (venv) garantiza que el software permanezca confinado y no modifique las bibliotecas de su sistema principal.

---

## 💡 Origen del proyecto

El impulso de este proyecto proviene de mi hermano, usuario histórico de Debian, quien identificó a Piper como la solución útil para TTS local.

---

## 🤖 Créditos y "Vibe Coding"

El proyecto **PiperRead** es el resultado de una colaboración híbrida **Humano-IA**:

*   **Ronan Davalan**: jefe de proyecto, arquitecto principal, aseguramiento de calidad (QA).
*   **Google Gemini**: arquitecto de IA, planificador, redactor técnico.
*   **Claude (Anthropic)** & **Perplexity**: consultores técnicos de IA (revisión de código y optimización).
*   **Motor Core**: [Piper TTS](https://github.com/OHF-voice/piper1-gpl), con licencia GPL-3.0-or-later. Se instala en su equipo mediante `pip` y se invoca como programa externo; PiperRead no lo redistribuye.

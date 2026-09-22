# PiperRead

<p align="center">
  <img src="https://img.shields.io/static/v1?label=Version&message=v0.2.0-alpha&color=orange" alt="Version">
  <img src="https://img.shields.io/badge/Licencia-MIT-green" alt="Licencia">
  <img src="https://img.shields.io/badge/Plataforma-Linux_(Wayland_|_X11)-black" alt="OS soportado">
  <img src="https://img.shields.io/badge/Motor-Piper_Neural_TTS-blueviolet" alt="Motor de audio">
  <img src="https://img.shields.io/badge/Lenguaje-Python_|_Bash-blue" alt="Código">
</p>

[English](../../README.md) | [Français](../fr-FR/README.md) | [Deutsch](../de-DE/README.md) | **Español**

## Descripción

**PiperRead** es una solución de automatización ligera diseñada para llevar la síntesis de voz neuronal (TTS) de alta calidad a los escritorios Linux.

**Sitio web oficial**: [piperread.davalan.fr](https://piperread.davalan.fr)

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

## Instalación desde un paquete

La vía más sencilla. Descargue el paquete de su sistema desde la [página de descargas](https://piperread.davalan.fr/es/download/) o desde la [última Release](https://github.com/RonanDavalan/PiperRead/releases/latest) e instálelo:

```bash
# Debian 12 y 13, Ubuntu 22.04 y 24.04, Linux Mint
sudo apt install ./piperread_0.2.0~alpha_all.deb

# Fedora 42
sudo dnf install ./piperread-0.2.0~alpha-1.fc42.noarch.rpm

# openSUSE Leap 15.6
sudo zypper install ./piperread-0.2.0~alpha-1.leap156.noarch.rpm

# Arch Linux
sudo pacman -U piperread-0.2.0alpha-1-any.pkg.tar.zst
```

El paquete instala el motor Piper con `pip` al configurarse: unos 75 MB de descarga (200 a 250 MB una vez instalado), con acceso a la red solo en ese momento. No incluye ninguna voz. Descargue una y compruebe después la instalación:

```bash
piperread --download-voice
piperread --diagnose
```

Los paquetes se validaron en contenedores (instalación, diagnóstico y desinstalación) en cada distribución y versión indicadas arriba. El manual está disponible como página (`man piperread`) y como PDF en cuatro idiomas en la página de descargas.

## Requisitos previos

Antes de la instalación desde las fuentes, asegúrese de que su sistema dispone de las herramientas de audio y portapapeles necesarias.

```bash
# Actualización del sistema
sudo apt update

# Instalación de Python, audio y herramientas de portapapeles
# (Instala tanto wl-clipboard para Wayland como xsel para X11 para garantizar la compatibilidad)
sudo apt install -y python3 python3-venv python3-pip alsa-utils wl-clipboard xsel libnotify-bin
```

---

## Instalación desde las fuentes

Dado que este proyecto se basa en modelos vocales pesados y un entorno virtual específico, debe inicializar el proyecto después de clonarlo.

### 1. Clonar el repositorio

```bash
mkdir -p $HOME/git/piper
cd $HOME/git/piper
git clone https://github.com/RonanDavalan/PiperRead.git
cd PiperRead
```

### 2. Inicializar el entorno (crítico)

Este paso crea el aislamiento de Python, instala el motor y descarga la voz que usted elija. `./read.sh --list-voices` muestra las voces propuestas con su licencia, su tamaño y enlaces para escucharlas; la calidad de una voz queda a la apreciación de cada uno.

```bash
# Creación del entorno virtual
python3 -m venv piper-env

# Instalación del motor Piper TTS
./piper-env/bin/pip install piper-tts

# Descarga de una voz (opciones: ./read.sh --list-voices)
./read.sh --download-voice es_ES-davefx-medium
```

### 3. Configuración de permisos

```bash
chmod 700 read.sh
```

### 4. Integración en el escritorio (icono y menú)

Para lanzar PiperRead como una aplicación nativa:

```bash
# Creación de las carpetas de aplicaciones e iconos locales
mkdir -p $HOME/.local/share/applications $HOME/.local/share/icons/hicolor/scalable/apps

# Instalación del icono
cp Ressources/piperread.svg $HOME/.local/share/icons/hicolor/scalable/apps/

# Generación del archivo desktop con la ruta de instalación real
sed "s|\$HOME/git/piper/PiperRead|$(pwd)|g" Ressources/PiperRead.desktop > $HOME/.local/share/applications/piperread.desktop

# Actualización de la base de datos de menús
update-desktop-database $HOME/.local/share/applications
```

---

## Uso

### Método 1: Selección con ratón (recomendado)

1.  **Resalte texto** en cualquier aplicación (navegador, PDF, editor).
2.  Haga clic en el icono **PiperRead** en su menú (o use su atajo de teclado personalizado).
3.  El texto se lee inmediatamente.

### Método 2: Portapapeles

1.  Copie texto (**Ctrl+C**).
2.  Lance PiperRead.

### Detener la lectura

Ejecute `piperread --stop` (o `./read.sh --stop` desde un clon) para terminar la lectura, `--pause` para suspenderla y `--resume` para reanudarla donde se detuvo. Asigne estos comandos a atajos de teclado si lo desea.

### Configuración

Se pueden ajustar tres parámetros: la velocidad de lectura `speed` (un multiplicador de 0,5 a 3,0; 1 es la voz natural), la voz `voice` (el nombre del modelo, tal como aparece con `--list-voices`) y el idioma `lang` de los mensajes (`en`, `fr`, `de` o `es`). Cada uno se resuelve en este orden — el primer nivel que aporte un valor válido prevalece:

1.  **Opción en la línea de comandos** — `--speed 1.25`, `--voice es_ES-davefx-medium`, `--lang es`.
2.  **Variable de entorno** — `PIPERREAD_SPEED`, `PIPERREAD_VOICE`, `PIPERREAD_LANG`.
3.  **Archivo de configuración** — `~/.config/piperread/piperread.conf`, una línea `clave=valor` por parámetro:
    ```
    speed=1.25
    voice=es_ES-davefx-medium
    lang=es
    ```
4.  **Predeterminado** — velocidad natural, primera voz instalada por orden alfabético, mensajes en inglés.

Un valor inválido en cualquier nivel distinto de la opción se ignora y se intenta el siguiente nivel; una opción de línea de comandos inválida detiene la lectura.

---

## Calidad

Este proyecto nació de un descubrimiento: la calidad impresionante del motor **Piper** para una solución totalmente libre y local.

*   **Renderizado de voz natural**: la elección de esta tecnología neuronal permite una lectura fluida y pausada, haciendo la escucha cómoda a largo plazo.
*   **Arquitectura ligera**: PiperRead no es una aplicación pesada, sino un orquestador minimalista. Conecta su escritorio y el motor de audio con una huella de sistema casi nula.
*   **Instalación limpia**: el uso estricto de entornos virtuales (venv) garantiza que el software permanezca confinado y no modifique las bibliotecas de su sistema principal.

---

## Origen del proyecto

El impulso de este proyecto proviene de mi hermano, usuario histórico de Debian, quien identificó a Piper como la solución útil para TTS local.

---

## Créditos y "Vibe Coding"

El proyecto **PiperRead** es el resultado de una colaboración híbrida **Humano-IA**:

*   **Ronan Davalan**: arquitecto y árbitro. Visión de producto, requisitos de seguridad, dirección del proyecto, validación y pruebas. Todas las decisiones de arquitectura son validadas por él.
*   **Claude Code (Anthropic)**: ingeniero de sistemas y desarrollador principal. Implementación de los scripts Bash, de la documentación y del sitio web; decisiones técnicas dentro de la arquitectura validada. Autor principal del código fuente.
*   **Google Gemini**: sintetizador y asesor estratégico. Análisis de arquitectura independiente, resolución de conflictos lógicos, optimización del flujo de trabajo, validación cruzada de decisiones técnicas.
*   **Muse Spark**: sintetizador y asesor estratégico. Sustituye a Gemini en algunas sesiones, con buenos resultados; algunas de sus respuestas se transmitieron a Claude Code.
*   **DeepSeek**: limpieza del marco de trabajo del proyecto, al inicio.
*   **Motor Core**: [Piper TTS](https://github.com/OHF-voice/piper1-gpl), con licencia GPL-3.0-or-later. Se instala en su equipo mediante `pip` y se invoca como programa externo; PiperRead no lo redistribuye.

% PIPERREAD(1) piperread | Comandos de usuario
% Ronan Davalan
% 2026-09-29

# NOMBRE

piperread - leer en voz alta el texto seleccionado o copiado, sin conexión, con el motor Piper

# SINOPSIS

**piperread** [*auto* | *selection* | *clipboard*] [**\--speed** *X*] [**\--voice** *NOMBRE*] [**\--lang** *CÓDIGO*] [**\--voices-dir** *RUTA*] [**\--normalize** *on*|*off*]

**piperread** {**\--stop** | **\--pause** | **\--resume**}

**piperread** {**\--version** | **\--diagnose** | **\--help**}

**piperread** **\--list-voices**

**piperread** **\--download-voice** [*NOMBRE*...]

# DESCRIPCIÓN

**piperread** lee en voz alta el texto que ha seleccionado con el ratón o
copiado al portapapeles, tanto en Wayland como en X11. La voz se sintetiza
localmente con el motor neuronal Piper: ningún texto ni ningún audio sale
jamás del equipo. Los símbolos de Markdown se eliminan antes de la lectura,
de modo que un texto con formato se dice como prosa.

Solo se ejecuta una lectura a la vez: volver a lanzar **piperread** detiene la
lectura anterior. El comando está pensado para asociarse a un atajo de teclado
del escritorio.

El motor no forma parte del programa. Se instala aparte, con
`pip install piper-tts`, y ese paso necesita conexión a la red y espacio en
disco. Ni los paquetes ni el motor incluyen ninguna voz: una voz se descarga
una vez con **\--download-voice** y después funciona sin red.

# ORIGEN DEL TEXTO

*selection*
:   Leer el texto seleccionado con el ratón.

*clipboard*
:   Leer el texto copiado al portapapeles.

*auto*
:   Valor por defecto. Leer la selección del ratón o, si no hay nada
    seleccionado, el portapapeles. Un contenido formado solo por espacios y
    saltos de línea se considera vacío.

# OPCIONES

**\--speed** *X*
:   Multiplicador de velocidad, de `0.5` a `3.0`. `1` es el ritmo natural de
    la voz.

**\--voice** *NOMBRE*
:   Voz que se usará, tal como aparece en **\--list-voices**.

**\--lang** *CÓDIGO*
:   Idioma de los mensajes y de la voz por defecto (`en`, `fr`, `de` o `es`).

**\--voices-dir** *RUTA*
:   Carpeta de voces propias, que se lee antes que las carpetas de PiperRead.
    Una ruta absoluta o que empiece por `~/`; la carpeta debe existir, si no
    el comando se detiene con el código `2`. Se lee en plano: una voz son dos
    archivos, `NOMBRE.onnx` y `NOMBRE.onnx.json`, colocados directamente en ella.

**\--normalize** *on*|*off*
:   `on` lleva las voces al mismo nivel con una ganancia medida una vez por voz
    (`off` por defecto).

**\--stop**
:   Detener la lectura en curso.

**\--pause**, **\--resume**
:   Suspender la lectura y reanudarla donde se detuvo.

**\--diagnose**
:   Comprobar la instalación (motor, voz, audio, herramientas del
    portapapeles) sin leer ni reproducir nada, y salir. Una última línea indica si
    la interfaz gráfica (**piperread-gui**) está presente y, si no lo está, qué
    paquete instalar; nunca cuenta como fallo. El código de salida es `1` cuando
    falla una comprobación.

**\--list-voices**
:   Mostrar las voces disponibles, con su tamaño y su licencia. La primera línea
    es el comando exacto que instala la voz recomendada para el idioma actual,
    seguida de «(instalada)» cuando ya lo está. Sin acceso a la red. Siguen las voces instaladas, cada una con su carpeta.

**\--download-voice** [*NOMBRE*...]
:   Descargar las voces indicadas en el directorio de voces. Sin nombre,
    ofrecer la voz del idioma actual. Con una carpeta de voces elegida, las voces se guardan en ella; el comando se detiene con el código `1` cuando no se puede escribir en esa carpeta.

**\--version**
:   Mostrar la versión y salir.

**\--help**
:   Mostrar un resumen de las opciones, en el idioma de los mensajes, y
    salir.

# CONFIGURACIÓN

Cada ajuste (`speed`, `voice`, `lang`, `voices_dir`, `normalize`) se toma de la primera de estas fuentes
que lo define:

1. la opción de la línea de comandos;
2. la variable de entorno `PIPERREAD_SPEED`, `PIPERREAD_VOICE`, `PIPERREAD_LANG`, `PIPERREAD_VOICES_DIR` o `PIPERREAD_NORMALIZE`;
3. el archivo de configuración.

El ajuste `telemetry` (`on` u `off`, `off` por defecto) no tiene opción de
línea de comandos: se toma de la variable de entorno `PIPERREAD_TELEMETRY` y
después del archivo de configuración. Controla los eventos de uso de la
biblioteca de inferencia que incorpora el motor (onnxruntime), desactivados por
defecto para que la lectura siga funcionando sin conexión.

El ajuste `voices_dir` indica una carpeta de voces propias, que se lee antes
que las carpetas de PiperRead: una voz presente en ambas procede de la suya.
**\--download-voice** guarda en ella y **\--diagnose** la nombra. Tiene la
opción **\--voices-dir**.

El ajuste `normalize` (`on` u `off`, `off` por defecto) lleva las voces al mismo
nivel: cada voz se mide una vez, la primera vez que se lee, y la medición se
guarda en `$XDG_STATE_HOME/piperread/voice-levels`. Tiene la opción
**\--normalize**. No es un control de volumen. Solo se midió en Linux.

# INTERFAZ GRÁFICA

El paquete **piperread-gui** ofrece una interfaz de bandeja que se inicia con la sesión, mantiene la voz cargada y añade pausa, reanudación y navegación frase por frase. Es un paquete aparte que depende de **piperread**: el archivo «todo en uno» de la página de descargas contiene ambos, y un solo comando los instala juntos (la guía de instalación lo indica para cada distribución).

La interfaz se inicia con el comando `piperread-gui`, o desde la entrada PiperRead del menú de aplicaciones. Se controla con **piperread-gui** {**\--play** | **\--pause** | **\--resume** | **\--stop** | **\--next** | **\--previous** | **\--quit**}; salvo **\--play**, estos comandos señalan un error cuando no hay ninguna interfaz en marcha. Sin ninguna voz instalada, abre una ventana que ofrece descargar una; no se descarga nada antes de pulsar Descargar.

Desde un clon del repositorio, una vez preparado el entorno de `gui/`, el comando es `gui/.venv/bin/python3 -m piperread_gui.app`. **piperread** nunca inicia la interfaz por sí mismo.

# ARCHIVOS

`$XDG_CONFIG_HOME/piperread/piperread.conf`
:   Archivo de configuración, `~/.config/piperread/piperread.conf` cuando
    `XDG_CONFIG_HOME` no está definida.

`$XDG_DATA_HOME/piperread/voices/`
:   Voces descargadas, `~/.local/share/piperread/voices/` cuando
    `XDG_DATA_HOME` no está definida.

`$XDG_STATE_HOME/piperread/voice-levels`
:   Nivel medido de cada voz, `~/.local/state/piperread/voice-levels` cuando
    `XDG_STATE_HOME` no está definida. Se escribe cuando `normalize` vale `on`.

`/usr/lib/piperread/venv`
:   Entorno de Python que contiene el motor Piper, en una instalación por
    paquete.

# VOCES

Las voces proceden del catálogo de Piper,
<https://huggingface.co/rhasspy/piper-voices>. Cada voz tiene su propia
licencia, que muestra **\--list-voices**. Se pueden escuchar muestras en
<https://rhasspy.github.io/piper-samples/>.

En el mezclador de sonido, la reproducción aparece con el nombre « PiperRead »,
tanto con el lanzador como con la interfaz; **\--diagnose** dice el nombre.
PiperRead define `PIPEWIRE_PROPS` antes de abrir el flujo y conserva su valor si
ha definido uno. El mezclador recuerda un volumen por nombre de aplicación, así
que el volumen de ese flujo vuelve al valor por defecto la primera vez.
Comprobado con PipeWire y su capa PulseAudio; PulseAudio solo, ALSA solo, macOS
y Windows no se comprobaron.

# PLATAFORMAS

En Linux, PiperRead se entrega en paquetes nativos: **Debian** y Ubuntu (`sudo apt install ./piperread_*_all.deb`), **Fedora** (`sudo dnf install ./piperread-*.noarch.rpm`), **openSUSE** Leap (`sudo zypper install ./piperread-*.noarch.rpm`) y **Arch** Linux (`sudo pacman -U ./piperread-*.pkg.tar.zst`), validados en contenedor: instalación, actualización, diagnóstico y retirada en Debian 12 y 13, Ubuntu 22.04 y 24.04, Fedora 44 y Arch Linux; instalación, diagnóstico y retirada en openSUSE Leap 16.0. Un contenedor no demuestra ni el sonido, ni el portapapeles, ni la entrada de menú, ni la pantalla. En **Windows** solo existe la interfaz gráfica, como la carpeta autónoma `piperread-gui-windows.zip`; es un ejecutable construido en Windows y ensayado sin pantalla, sin matriz de pruebas automatizada.

# CÓDIGO DE SALIDA

`0` si todo va bien, `1` cuando falta una dependencia, el motor o una voz, o
falla una comprobación del diagnóstico, `2` en caso de error de uso.

# AUTOR

Ronan Davalan. Código fuente e incidencias: <https://github.com/RonanDavalan/PiperRead>.

# LICENCIA

MIT.

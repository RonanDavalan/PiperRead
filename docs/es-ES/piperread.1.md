% PIPERREAD(1) piperread | Comandos de usuario
% Ronan Davalan
% 2026-09-21

# NOMBRE

piperread - leer en voz alta el texto seleccionado o copiado, sin conexión, con el motor Piper

# SINOPSIS

**piperread** [*auto* | *selection* | *clipboard*] [**\--speed** *X*] [**\--voice** *NOMBRE*] [**\--lang** *CÓDIGO*]

**piperread** {**\--stop** | **\--pause** | **\--resume**}

**piperread** {**\--version** | **\--diagnose**}

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

**\--stop**
:   Detener la lectura en curso.

**\--pause**, **\--resume**
:   Suspender la lectura y reanudarla donde se detuvo.

**\--diagnose**
:   Comprobar la instalación (motor, voz, audio, herramientas del
    portapapeles) sin leer ni reproducir nada, y salir. El código de salida es
    `1` cuando falla una comprobación.

**\--list-voices**
:   Mostrar las voces disponibles, con su licencia. Sin acceso a la red.

**\--download-voice** [*NOMBRE*...]
:   Descargar las voces indicadas en el directorio de voces. Sin nombre,
    ofrecer la voz del idioma actual.

**\--version**
:   Mostrar la versión y salir.

# CONFIGURACIÓN

Cada ajuste (`speed`, `voice`, `lang`) se toma de la primera de estas fuentes
que lo define:

1. la opción de la línea de comandos;
2. la variable de entorno `PIPERREAD_SPEED`, `PIPERREAD_VOICE` o `PIPERREAD_LANG`;
3. el archivo de configuración.

# ARCHIVOS

`$XDG_CONFIG_HOME/piperread/piperread.conf`
:   Archivo de configuración, `~/.config/piperread/piperread.conf` cuando
    `XDG_CONFIG_HOME` no está definida.

`$XDG_DATA_HOME/piperread/voices/`
:   Voces descargadas, `~/.local/share/piperread/voices/` cuando
    `XDG_DATA_HOME` no está definida.

`/usr/lib/piperread/venv`
:   Entorno de Python que contiene el motor Piper, en una instalación por
    paquete.

# VOCES

Las voces proceden del catálogo de Piper,
<https://huggingface.co/rhasspy/piper-voices>. Cada voz tiene su propia
licencia, que muestra **\--list-voices**. Se pueden escuchar muestras en
<https://rhasspy.github.io/piper-samples/>.

# CÓDIGO DE SALIDA

`0` si todo va bien, `1` cuando falta una dependencia, el motor o una voz, o
falla una comprobación del diagnóstico, `2` en caso de error de uso.

# AUTOR

Ronan Davalan. Código fuente e incidencias: <https://github.com/RonanDavalan/PiperRead>.

# LICENCIA

MIT.

"""
Acceso de MiClaw a tu PC: leer/escribir archivos y ejecutar comandos.

SEGURIDAD: ninguna herramienta se ejecuta sin tu confirmación. El asistente
propone la acción; el frontend te muestra una tarjeta con el comando/ruta y
tú la apruebas o la rechazas. Además, la escritura y la terminal solo operan
dentro de rutas permitidas (por defecto tu carpeta de usuario y la carpeta
del proyecto; ajustable en Ajustes → PC).

El token @@PC:...@@ es el "contrato" entre el agente y la interfaz:
  - @@PC:ver@@           → ver un archivo (se aprueba solo si es pequeño)
  - @@PC:escribir@@       → crear/sobrescribir un archivo (pedir permiso)
  - @@PC:terminal@@       → ejecutar un comando (pedir permiso)
  - @@PC:apuntes@@        → lista de tus apuntes (memoria) — sin permiso
"""

import os
import subprocess
import tempfile
from pathlib import Path

from . import config

# ---------------------------------------------------------------------------
# Rutas permitidas (sandbox)
# ---------------------------------------------------------------------------
def rutas_permitidas():
    """Devuelve la lista de directorios donde se permite escribir/ejecutar."""
    raiz = Path(config.BASE_DIR)
    custom = (config.load_config().get("pc") or {}).get("carpeta_extra", "")
    rutas = [raiz, Path.home()]
    if custom:
        p = Path(custom).expanduser()
        if p.is_dir():
            rutas.append(p)
    return rutas


def _esta_permitido(path):
    try:
        target = Path(path).expanduser().resolve()
    except OSError:
        return False
    for base in rutas_permitidas():
        try:
            target.relative_to(base.resolve())
            return True
        except ValueError:
            continue
    return False


def _info_error_permiso():
    return ("Acción bloqueada: la ruta está fuera de las carpetas permitidas "
            "(tu carpeta de usuario o la del proyecto).")


# ---------------------------------------------------------------------------
# Herramientas (llamadas DESPUÉS de la aprobación del usuario)
# ---------------------------------------------------------------------------
def ver_archivo(ruta):
    try:
        path = Path(ruta).expanduser()
        if not path.is_file():
            return f"No encuentro el archivo: {ruta}"
        tamano = path.stat().st_size
        if tamano > 200_000:
            return f"El archivo es muy grande ({tamano} bytes). Ábrelo tú mismo."
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            contenido = f.read(200_000)
        return (f"Contenido de {path}:\n\n{contenido}"[:15_000])
    except OSError as e:
        return f"No pude leer el archivo: {e}"


def escribir_archivo(ruta, contenido):
    if not _esta_permitido(ruta):
        return _info_error_permiso()
    try:
        path = Path(ruta).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(contenido)
        return f"Archivo guardado: {path}"
    except OSError as e:
        return f"No pude escribir el archivo: {e}"


def ejecutar_comando(comando):
    if not _esta_permitido("."):
        return _info_error_permiso()
    try:
        proc = subprocess.run(
            comando, shell=True, capture_output=True, text=True,
            timeout=120, cwd=config.BASE_DIR,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        salida = (proc.stdout or "") + (proc.stderr or "")
        codigo = proc.returncode
        resumen = f"Salida (código {codigo}):\n{salida}" if salida else f"Comando terminado (código {codigo}) sin salida."
        return resumen[:10_000]
    except subprocess.TimeoutExpired:
        return "El comando tardó más de 120 segundos y se canceló."
    except OSError as e:
        return f"No pude ejecutar el comando: {e}"


# ---------------------------------------------------------------------------
# Parseo del token @@PC:...@@
# ---------------------------------------------------------------------------
def parsear(texto):
    """
    Devuelve (accion, datos) si el texto empieza por @@PC:accion@@.
    Para 'escribir' y 'terminal', los datos pueden ir en el propio texto
    (si el modelo usa líneas 'RUTA:'/'COMANDO:') o en la siguiente línea.
    """
    texto = texto.strip()
    if not texto.startswith("@@"):
        return None, None
    fin = texto.find("@@", 2)
    if fin == -1:
        return None, None
    token = texto[2:fin].strip()
    if not token.startswith("PC:"):
        return None, None
    accion = token[3:].strip()
    resto = texto[fin + 2:].strip()
    if accion not in ("ver", "escribir", "terminal", "apuntes"):
        return None, None

    if accion == "ver":
        return accion, resto or None

    if accion == "escribir":
        ruta = None
        contenido = resto
        for linea in resto.splitlines():
            if linea.lower().startswith("ruta:"):
                ruta = linea.split(":", 1)[1].strip()
                contenido = "\n".join(resto.splitlines()[1:])
                break
        if ruta is None:
            # Si no hay 'RUTA:', el primer bloque no vacío es la ruta y el
            # resto (tras un salto de línea) es el contenido.
            partes = resto.split("\n", 1)
            if len(partes) == 2 and partes[0].strip():
                ruta, contenido = partes[0].strip(), partes[1].strip()
        return accion, {"ruta": ruta, "contenido": contenido.strip()}

    if accion == "terminal":
        comando = resto
        for linea in resto.splitlines():
            if linea.lower().startswith("comando:"):
                comando = linea.split(":", 1)[1].strip()
                break
        return accion, comando

    return accion, None


def ejecutar(accion, datos):
    """Ejecuta la acción YA aprobada por el usuario."""
    if accion == "ver":
        return ver_archivo(datos or "")
    if accion == "escribir":
        if not datos or not datos.get("ruta"):
            return "Falta la ruta del archivo."
        return escribir_archivo(datos["ruta"], datos.get("contenido", ""))
    if accion == "terminal":
        return ejecutar_comando(datos or "")
    if accion == "apuntes":
        from . import memory
        return memory.read_memory() or "(sin apuntes)"
    return "Acción desconocida."

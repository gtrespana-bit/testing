"""
Herramientas de MiClaw: búsqueda web, notas y acceso al PC.

Cuando una petición encaja con una herramienta, la respuesta se compone
como:
  @@TOOL:NOMBRE@@\n{datos}      → se ejecuta automáticamente
  @@PC:ACCION@@\n{datos}        → pide confirmación al usuario antes de ejecutar

El servidor ejecuta la herramienta y devuelve el resultado como un mensaje
"tool" que el modelo puede usar para responder.
"""

import datetime

# Búsqueda web con DuckDuckGo (gratis y sin clave)
try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

from . import pc

# Con esta lista se decide (en el prompt) qué puede hacer el asistente.
# Las de tipo "auto" se ejecutan solas; las de tipo "permiso" piden
# confirmación al usuario antes de tocar nada.
TOOLS = [
    {
        "id": "web",
        "nombre": "Buscar en internet",
        "descripcion": ("Busca información actualizada en la web (noticias, datos, "
                        "precios...). Úsala cuando necesites información que no sabes "
                        "con seguridad."),
        "tipo": "auto",
        "formato": '@@TOOL:web@@\n{consulta}',
    },
    {
        "id": "nota",
        "nombre": "Guardar nota rápida",
        "descripcion": ("Guarda un dato en la memoria (nombre de un amigo, fechas, "
                        "preferencias...). Usa SOLO para datos importantes que quieras "
                        "recordar en el futuro."),
        "tipo": "auto",
        "formato": '@@TOOL:nota@@\n{texto a recordar}',
    },
    {
        "id": "ver",
        "nombre": "Ver un archivo de tu PC",
        "descripcion": ("Lee el contenido de un archivo de tu ordenador para "
                        "resumirlo, corregirlo o trabajar con él."),
        "tipo": "permiso",
        "formato": '@@PC:ver@@\n{ruta completa del archivo}',
    },
    {
        "id": "escribir",
        "nombre": "Crear o editar un archivo",
        "descripcion": ("Crea un archivo nuevo o sobrescribe uno existente en tu "
                        "ordenador (texto, código, scripts...)."),
        "tipo": "permiso",
        "formato": '@@PC:escribir@@\nRUTA: {ruta completa}\n{contenido}',
    },
    {
        "id": "terminal",
        "nombre": "Ejecutar un comando en tu terminal",
        "descripcion": ("Ejecuta un comando en tu ordenador (instalar programas, "
                        "ver carpetas, etc.). El usuario SIEMPRE debe aprobarlo."),
        "tipo": "permiso",
        "formato": '@@PC:terminal@@\nCOMANDO: {comando}',
    },
    {
        "id": "apuntes",
        "nombre": "Leer mis apuntes de memoria",
        "descripcion": ("Muestra todos los apuntes guardados (la memoria de MiClaw). "
                        "Úsala cuando el usuario pregunte por cosas guardadas."),
        "tipo": "auto",
        "formato": '@@PC:apuntes@@',
    },
]


def ejecutar(tool_id, argumento):
    if tool_id == "web":
        return _buscar_web(argumento)
    if tool_id == "nota":
        return _guardar_nota(argumento)
    if tool_id in ("ver", "escribir", "terminal", "apuntes"):
        return pc.ejecutar(tool_id, argumento)
    return "Herramienta desconocida."


def _buscar_web(query):
    query = query.strip()[:300]
    if not query:
        return "Búsqueda vacía."
    if DDGS is None:
        return "El paquete 'ddgs' no está instalado (pip install -r requirements.txt)."
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return f"Sin resultados para: {query}"
        lines = []
        for i, r in enumerate(results[:5], 1):
            lines.append(f"{i}. {r.get('title', '')} — {r.get('href', '')}\n   {r.get('body', '')}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"No he podido buscar en DuckDuckGo (¿sin internet?). Detalle: {e}"


def _guardar_nota(texto):
    from . import memory
    nombre = memory.remember(texto)
    return f"Nota guardada como {nombre}. Ya la consultaré cuando haga falta."

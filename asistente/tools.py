"""
Herramientas básicas de MiClaw: búsqueda web y notas rápidas.

Cuando una petición encaja con una herramienta, la respuesta se compone
como:  @@TOOL:NOMBRE@@\n{datos}
El servidor ejecuta la herramienta y devuelve el resultado como un mensaje
"tool" que el modelo puede usar para responder.
"""

import datetime

# Búsqueda web con DuckDuckGo (gratis y sin clave)
try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

# Con esta lista se decide (en el prompt) qué puede hacer el asistente.
TOOLS = [
    {
        "id": "web",
        "nombre": "Buscar en internet",
        "descripcion": "Busca información actualizada en la web (noticias, datos, precios...). "
                       "Úsala cuando necesites información que no sabes con seguridad.",
        "formato": '@@TOOL:web@@\\n{consulta}',
    },
    {
        "id": "nota",
        "nombre": "Guardar nota rápida",
        "descripcion": "Guarda un dato en la memoria (nombre de un amigo, fechas, preferencias...). "
                       "Usa SOLO para datos importantes que quieras recordar en el futuro.",
        "formato": '@@TOOL:nota@@\\n{texto a recordar}',
    },
]


def ejecutar(tool_id, argumento):
    if tool_id == "web":
        return _buscar_web(argumento)
    if tool_id == "nota":
        return _guardar_nota(argumento)
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

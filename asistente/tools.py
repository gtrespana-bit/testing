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
    {
        "id": "calc",
        "nombre": "Calculadora",
        "descripcion": ("Hace operaciones matemáticas exactas (sumas, raíces, "
                        "trigonometría...). Úsala cuando el usuario pida calcular algo."),
        "tipo": "auto",
        "formato": '@@TOOL:calc@@\n{expresión, ej: 25*4+10 o sqrt(144)}',
    },
    {
        "id": "recordatorio",
        "nombre": "Crear recordatorio",
        "descripcion": ("Guarda un recordatorio con fecha y hora para avisar al "
                        "usuario. Úsala cuando pida que le recuerdes algo en un momento."),
        "tipo": "auto",
        "formato": '@@TOOL:recordatorio@@\n{qué recordar} | {cuándo}',
    },
    {
        "id": "clima",
        "nombre": "Clima del tiempo",
        "descripcion": ("Consulta el tiempo meteorológico actual de una ciudad "
                        "o lugar (gratis, sin clave)."),
        "tipo": "auto",
        "formato": '@@TOOL:clima@@\n{ciudad o lugar}',
    },
]


def ejecutar(tool_id, argumento):
    if tool_id == "web":
        return _buscar_web(argumento)
    if tool_id == "nota":
        return _guardar_nota(argumento)
    if tool_id == "calc":
        return _calcular(argumento)
    if tool_id == "recordatorio":
        return _crear_recordatorio(argumento)
    if tool_id == "clima":
        return _clima(argumento)
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


def _calcular(expr):
    """Calculadora segura: evalúa expresiones matemáticas con ast (sin eval)."""
    import ast
    import math
    import operator

    expr = (expr or "").strip().replace("^", "**").replace("×", "*").replace("÷", "/")
    if not expr:
        return "Expresión vacía."

    FUNCS = {
        "sqrt": math.sqrt, "sin": math.sin, "sen": math.sin, "cos": math.cos,
        "tan": math.tan, "tg": math.tan,
        "asin": math.asin, "acos": math.acos, "atan": math.atan,
        "log": math.log, "log10": math.log10, "ln": math.log, "exp": math.exp,
        "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
        "factorial": math.factorial, "radians": math.radians, "degrees": math.degrees,
        "min": min, "max": max,
    }
    CONST = {"pi": math.pi, "e": math.e, "tau": math.tau}
    OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow,
        ast.USub: operator.neg, ast.UAdd: operator.pos,
    }

    def evaluar(n):
        if isinstance(n, ast.Constant):
            if isinstance(n.value, (int, float)):
                return n.value
            raise ValueError("constante no válida")
        if isinstance(n, ast.Name):
            if n.id in CONST:
                return CONST[n.id]
            raise ValueError(f"nombre desconocido: {n.id}")
        if isinstance(n, ast.BinOp):
            return OPS[type(n.op)](evaluar(n.left), evaluar(n.right))
        if isinstance(n, ast.UnaryOp):
            return OPS[type(n.op)](evaluar(n.operand))
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name) and n.func.id in FUNCS:
                return FUNCS[n.func.id](*[evaluar(a) for a in n.args])
            raise ValueError("función no permitida")
        raise ValueError("expresión no permitida")

    try:
        arbol = ast.parse(expr, mode="eval")
        resultado = evaluar(arbol.body)
        if isinstance(resultado, float):
            resultado = round(resultado, 10)
        return f"Resultado: {resultado}"
    except Exception as e:
        return f"No pude calcular: {e}"


def _crear_recordatorio(arg):
    from . import recordatorios
    if "|" not in arg:
        return ("Formato: texto | cuándo — ejemplos: "
                "'revisar el correo | mañana a las 9', "
                "'llamar a Ana | en 30 minutos', "
                "'cumple de Luis | el 5 de septiembre a las 14:00'.")
    texto, cuando = arg.rsplit("|", 1)
    _rid, msg = recordatorios.crear(texto, cuando)
    return msg


def _clima(lugar):
    import urllib.parse

    import httpx

    lugar = (lugar or "").strip()
    if not lugar:
        return "Dime qué ciudad o lugar quieres consultar."
    url = f"https://wttr.in/{urllib.parse.quote(lugar)}?format=j1&lang=es"
    try:
        r = httpx.get(url, timeout=20)
        r.raise_for_status()
        d = r.json()
        cur = d.get("current_condition", [{}])[0]
        area = d.get("nearest_area", [{}])[0]
        ciudad = area.get("areaName", [{}])[0].get("value", lugar)
        temp = cur.get("temp_C", "?")
        desc = (cur.get("lang_es", [{}])[0].get("value")
                or cur.get("weatherDesc", [{}])[0].get("value") or "?")
        hum = cur.get("humidity", "?")
        viento = cur.get("windspeedKmph", "?")
        hoy = d.get("weather", [{}])[0]
        tmax, tmin = hoy.get("maxtempC", "?"), hoy.get("mintempC", "?")
        return (f"🌤️ Clima en {ciudad}: {desc}, {temp}°C "
                f"(máx {tmax}° / mín {tmin}°), humedad {hum}%, viento {viento} km/h.")
    except Exception as e:
        return f"No pude obtener el clima (¿sin internet?). Detalle: {e}"

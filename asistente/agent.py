"""
El agente: junta el prompt del sistema, la memoria y las herramientas,
y decide si una petición necesita ejecutar una herramienta.

Flujo de cada mensaje del usuario:
  1. Se prepara el prompt del sistema (con herramientas + memoria).
  2. Se envía la conversación al modelo elegido.
  3. Si el modelo pide una herramienta automática (@@TOOL:...), se ejecuta,
     se añade el resultado como mensaje "tool" y se vuelve a llamar.
  4. Si el modelo pide una acción sobre el PC (@@PC:...), NO se ejecuta:
     se devuelve un plan {accion, datos} para que el usuario la apruebe
     desde la interfaz. Al aprobar, el frontend envía el resultado como
     mensaje "tool" y el agente continúa (parámetro tool_result).
  5. La respuesta final es lo que ve el usuario.
"""

import datetime
import re

from . import config, pc, providers, tools

SYSTEM_PROMPT = """Eres MiClaw, un asistente personal que corre en el ordenador de su dueño.
Respondes en el idioma del usuario (normalmente español), de forma clara y útil.

HOY ES: {hoy} (usa esta fecha si necesitas saber qué día es).

TIENES HERRAMIENTAS. Si la petición encaja con alguna, responde SOLO con
la línea exacta (nada más, sin comillas ni explicaciones):

{formato}

Si no encaja con ninguna herramienta, responde normalmente.

REGLAS DE USO:
- "web": Úsala para información actual o desconocida (noticias, precios,
  datos que puedan haber cambiado). No inventes datos que puedas consultar.
- "nota": Úsala SOLO para datos personales importantes que el usuario quiera
  recordar a futuro (nombres, fechas, preferencias, ideas).
- "ver"/"escribir"/"terminal": acciones sobre el PC del usuario. El usuario
  DEBE aprobar cada una desde la interfaz; cuando la apruebe, verás el
  resultado como un mensaje "tool" y podrás continuar. Pide confirmación
  escribiendo la acción propuesta de forma clara.
- "apuntes": úsala cuando el usuario pregunte qué recuerdas o qué apuntes tienes.

MEMORIA (lo que ya sabes de tu dueño):
{memoria}

Si no hay memoria, no pasa nada: simplemente no conoces datos previos.
Nunca inventes recuerdos."""


def _formato_herramientas():
    return "\n\n".join(t["formato"] for t in tools.TOOLS)


def _build_system_prompt():
    from . import memory
    incluir = config.load_config().get("memoria_incluida", True)
    contenido = memory.read_memory() if incluir else ""
    if not contenido:
        contenido = "(vacía)"
    return SYSTEM_PROMPT.format(
        hoy=datetime.date.today().isoformat(),
        formato=_formato_herramientas(),
        memoria=contenido,
    )


def _extraer_tool(texto):
    """Devuelve (tipo, id, argumento). tipo: 'tool' (auto) | 'pc' (permiso)."""
    m = re.match(r"@@TOOL:([a-z]+)@@\s*\n?(.*)", texto, re.DOTALL)
    if m:
        return "tool", m.group(1), m.group(2).strip()

    accion, datos = pc.parsear(texto)
    if accion:
        return "pc", accion, datos

    return None, None, None


def responder(history, provider=None, model=None, tool_result=None, max_tool_rounds=3):
    """
    Devuelve un dict:
      {"tipo": "respuesta", "texto": ...}  → respuesta final
      {"tipo": "permiso", "accion": ..., "datos": ..., "texto": ...}  → pide aprobación
    Si `tool_result` no es None, se inyecta como mensaje "tool" antes del bucle
    (es el resultado de una acción de PC que el usuario ya aprobó).
    """
    provider = provider or config.get_provider()
    model = model or config.get_model()

    messages = [{"role": "system", "content": _build_system_prompt()}] + list(history)
    if tool_result is not None:
        messages.append({"role": "tool", "content": str(tool_result)})

    for _ in range(max_tool_rounds + 1):
        texto = providers.chat(provider, model, messages)
        tipo, tid, arg = _extraer_tool(texto)

        if tipo is None:
            return {"tipo": "respuesta", "texto": texto.strip()}

        if tipo == "pc":
            return {
                "tipo": "permiso",
                "accion": tid,
                "datos": arg,
                "texto": texto.strip(),
            }

        # herramienta automática: se ejecuta y se sigue
        resultado = tools.ejecutar(tid, arg)
        messages.append({"role": "assistant", "content": texto})
        messages.append({
            "role": "tool",
            "content": f"Resultado de la herramienta {tid}:\n{resultado}",
        })

    return {"tipo": "respuesta", "texto": "He agotado los intentos con las herramientas. Prueba a reformular la petición."}

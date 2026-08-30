"""
El agente: junta el prompt del sistema, la memoria y las herramientas,
y decide si una petición necesita ejecutar una herramienta.

Flujo de cada mensaje del usuario:
  1. Se prepara el prompt del sistema (con herramientas + memoria).
  2. Se envía la conversación al modelo elegido.
  3. Si el modelo pide una herramienta (@@TOOL:...), se ejecuta,
     se añade el resultado como mensaje "tool" y se vuelve a llamar.
  4. La respuesta final es lo que ve el usuario.
"""

import re

from . import config, providers, tools

SYSTEM_PROMPT = """Eres MiClaw, un asistente personal que corre en el ordenador de su dueño.
Respondes en el idioma del usuario (normalmente español), de forma clara y útil.

TIENES HERRAMIENTAS. Si la petición encaja con alguna, responde SOLO con
la línea exacta (nada más, sin comillas ni explicaciones):

{formato}

Si no encaja con ninguna herramienta, responde normalmente.

REGLAS DE USO:
- "web": Úsala para información actual o desconocida (noticias, precios,
  datos que puedan haber cambiado). No inventes datos que puedas consultar.
- "nota": Úsala SOLO para datos personales importantes que el usuario quiera
  recordar a futuro (nombres, fechas, preferencias, ideas).

MEMORIA (lo que ya sabes de tu dueño):
{memoria}

Si no hay memoria, no pasa nada: simplemente no conoces datos previos.
Nunca inventes recuerdos."""


TOOL_BLOCK = """Ejecuta la herramienta y responde al usuario en español usando su resultado.
Resultado de la herramienta {tool_id}:
{resultado}"""


def _formato_herramientas():
    return "\n\n".join(t["formato"] for t in tools.TOOLS)


def _build_system_prompt():
    from . import memory
    incluir = config.load_config().get("memoria_incluida", True)
    contenido = memory.read_memory() if incluir else ""
    if not contenido:
        contenido = "(vacía)"
    return SYSTEM_PROMPT.format(
        formato=_formato_herramientas(),
        memoria=contenido,
    )


def _extraer_tool(texto):
    m = re.match(r"@@TOOL:([a-z]+)@@\s*\n?(.*)", texto, re.DOTALL)
    if m:
        return m.group(1), m.group(2).strip()
    return None, None


def responder(history, provider=None, model=None, max_tool_rounds=3):
    """Devuelve la respuesta del asistente para la conversación `history`."""
    provider = provider or config.get_provider()
    model = model or config.get_model()

    messages = [{"role": "system", "content": _build_system_prompt()}] + list(history)

    for _ in range(max_tool_rounds + 1):
        texto = providers.chat(provider, model, messages)
        tool_id, argumento = _extraer_tool(texto)
        if tool_id is None:
            return texto.strip()

        resultado = tools.ejecutar(tool_id, argumento)
        messages.append({"role": "assistant", "content": texto})
        messages.append({
            "role": "tool",
            "content": TOOL_BLOCK.format(tool_id=tool_id, resultado=resultado),
        })

    return "He agotado los intentos con las herramientas. Prueba a reformular la petición."

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
import time

from . import config, pc, providers, tools

# ---------------------------------------------------------------------------
# Modos de trabajo (personas). Se eligen en Ajustes → Modo.
# ---------------------------------------------------------------------------
MODOS = {
    "general": (
        "Eres MiClaw, un asistente personal versátil. Responde de forma clara, "
        "cercana y útil. Si te piden código, lo escribes bien explicado."
    ),
    "programador": (
        "Eres MiClaw en MODO PROGRAMADOR: un ingeniero de software senior. "
        "Escribes código limpio y moderno, detectas bugs, explicas errores con "
        "su causa raíz, propones la solución correcta y puedes crear proyectos "
        "completos desde cero. Antes de escribir código, piensa la estructura; "
        "usa las herramientas de archivos (ver/listar/buscar) para entender el "
        "código existente y las de terminal para ejecutar y comprobar."
    ),
    "investigador": (
        "Eres MiClaw en MODO INVESTIGADOR: analista riguroso. Buscas fuentes, "
        "contrastas datos, citas lo que encuentras y distingues claramente entre "
        "hechos verificados e hipótesis. No inventas información: si no la sabes, "
        "usa la búsqueda web."
    ),
    "escritor": (
        "Eres MiClaw en MODO ESCRITOR: redactor creativo y editor. Escribes con "
        "estilo, corriges gramática y ortografía, adaptas el tono al público y "
        "estructuras textos largos (informes, artículos, correos)."
    ),
}

SYSTEM_PROMPT = """{persona}

Corres en el ordenador de tu dueño. Respondes en el idioma del usuario
(normalmente español).

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
- "calc": Úsala para operaciones matemáticas exactas. Escribe la expresión.
- "recordatorio": Úsala cuando el usuario pida que le recuerdes algo en un
  momento concreto. Formato: @@TOOL:recordatorio@@\\n{{qué recordar}} | {{cuándo}}
  (ej: "mañana a las 9", "en 30 minutos", "el 5 de septiembre a las 14:30").
- "tarea": Úsala cuando el usuario pida programar una acción automática
  ("programa/agenda una tarea..."). Formato: @@TOOL:tarea@@\\n{{qué debe hacer}} | {{cuándo}}
  MiClaw la ejecutará solo a la hora indicada (sin acciones de PC).
- "clima": Úsala para preguntar por el tiempo meteorológico de un lugar.
- "codigo": Úsala para preguntas sobre el código de tus proyectos indexados
  ("¿dónde está...?", "¿qué hace la función X?"). Busca en el índice local
  (no requiere permiso). Si aún no hay índice, indícalo al usuario.
- "depurar": Úsala para ejecutar un script y capturar su error/salida (el
  usuario debe aprobarla). Después podrás corregir el archivo con "escribir"
  y volver a probar con "depurar" hasta que funcione.
- "informe": Úsala para guardar un resumen/informe como archivo Markdown.
  Formato: @@TOOL:informe@@\\n{{título}} | {{contenido en markdown}}
- "captura": Úsala cuando el usuario pida ver su pantalla o capturarla
  ("mira mi pantalla", "captura la pantalla"). Requiere aprobación del usuario
  y un modelo con visión (Gemini, Qwen-VL, etc.).
- "ver"/"escribir"/"terminal"/"listar"/"buscar"/"documento": acciones sobre el
  PC del usuario. El usuario DEBE aprobar cada una desde la interfaz; cuando la
  apruebe, verás el resultado como un mensaje "tool" y podrás continuar. Puedes
  proponer VARIAS acciones seguidas (una por línea @@PC:...@@) para que se
  aprueben en lote. Pide confirmación escribiendo la acción propuesta.
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
    modo = config.get_modo()
    return SYSTEM_PROMPT.format(
        persona=MODOS.get(modo, MODOS["general"]),
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


def responder(history, provider=None, model=None, tool_result=None, max_tool_rounds=5,
              no_pc=False, auto_aprobar=False):
    """
    Devuelve un dict:
      {"tipo": "respuesta", "texto": ...}  → respuesta final
      {"tipo": "permiso", "accion": ..., "datos": ..., "texto": ...}  → pide aprobación
    Si `tool_result` no es None, se inyecta como mensaje "tool" antes del bucle
    (es el resultado de una acción de PC que el usuario ya aprobó).
    Si `no_pc` es True (tareas automáticas), las acciones de PC se saltan
    automáticamente sin pedir permiso.
    Si `auto_aprobar` es True, las acciones de PC se ejecutan directamente
    sin pedir confirmación (activado en Ajustes → Acceso a tu PC).
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
            if no_pc:
                messages.append({"role": "assistant", "content": texto})
                messages.append({
                    "role": "tool",
                    "content": ("Acción de PC no permitida en modo automático. "
                                "No la ejecutes y responde con lo que puedas."),
                })
                continue
            if auto_aprobar:
                lote = pc.parsear_lote(texto)
                acciones = lote if len(lote) > 1 else [{"accion": tid, "datos": arg}]
                for a in acciones:
                    r = pc.ejecutar(a["accion"], a["datos"])
                    if r.startswith("@@IMAGEN@@"):
                        partes = r.split("\n", 2)
                        datauri = partes[1] if len(partes) > 1 else ""
                        nota = partes[2] if len(partes) > 2 else ""
                        messages.append({"role": "assistant", "content": texto})
                        messages.append({
                            "role": "user",
                            "content": "[Captura de pantalla tomada. Analízala y responde.] " + nota,
                            "imagen": datauri,
                        })
                        break
                    messages.append({"role": "assistant", "content": texto})
                    messages.append({
                        "role": "tool",
                        "content": f"Resultado de la herramienta {a['accion']}:\n{r}",
                    })
                continue
            # ¿Varias acciones en un solo mensaje? Se aprueban en lote.
            lote = pc.parsear_lote(texto)
            if len(lote) > 1:
                return {
                    "tipo": "permiso",
                    "accion": "lote",
                    "datos": lote,
                    "texto": texto.strip(),
                }
            return {
                "tipo": "permiso",
                "accion": tid,
                "datos": arg,
                "texto": texto.strip(),
            }

        # herramienta automática: se ejecuta y se sigue
        resultado = tools.ejecutar(tid, arg)
        if resultado.startswith("@@IMAGEN@@"):
            # la herramienta devolvió una imagen (captura de pantalla):
            # se inyecta como mensaje con visión para que el modelo la analice
            partes = resultado.split("\n", 2)
            datauri = partes[1] if len(partes) > 1 else ""
            nota = partes[2] if len(partes) > 2 else ""
            messages.append({"role": "assistant", "content": texto})
            messages.append({
                "role": "user",
                "content": "[Captura de pantalla tomada. Analízala y responde.] " + nota,
                "imagen": datauri,
            })
            continue
        messages.append({"role": "assistant", "content": texto})
        messages.append({
            "role": "tool",
            "content": f"Resultado de la herramienta {tid}:\n{resultado}",
        })

    return {"tipo": "respuesta", "texto": "He agotado los intentos con las herramientas. Prueba a reformular la petición."}


def responder_stream(history, provider=None, model=None, tool_result=None, max_tool_rounds=5,
                     auto_aprobar=False):
    """
    Igual que responder() pero con STREAMING real: va emitiendo eventos:
      {"tipo":"token","texto":...}   → trozo de la respuesta (se muestra en vivo)
      {"tipo":"tool","id":...,"nombre":...}  → se ejecutó una herramienta automática
      {"tipo":"permiso","accion":...,"datos":...,"texto":...} → pide aprobación al usuario
      {"tipo":"error","texto":...}
      {"tipo":"done"}                → respuesta completa
    Si `tool_result` no es None, se inyecta como mensaje "tool" antes del bucle
    (resultado de una acción de PC que el usuario ya aprobó).
    Si `auto_aprobar` es True, las acciones de PC se ejecutan directamente
    sin pedir confirmación.
    """
    provider = provider or config.get_provider()
    model = model or config.get_model()

    messages = [{"role": "system", "content": _build_system_prompt()}] + list(history)
    if tool_result is not None:
        messages.append({"role": "tool", "content": str(tool_result)})

    t0 = time.time()
    for _ in range(max_tool_rounds + 1):
        buffer = []
        try:
            for chunk in providers.stream_chat(provider, model, messages):
                buffer.append(chunk)
                acumulado = "".join(buffer)
                # No reenviamos el texto si parece el inicio de un token de
                # herramienta (así el usuario no ve "@@TOOL:..." por pantalla).
                if not acumulado.lstrip().startswith("@@"):
                    yield {"tipo": "token", "texto": chunk}
        except providers.ProviderError as e:
            yield {"tipo": "error", "texto": str(e)}
            return
        except Exception as e:
            yield {"tipo": "error", "texto": f"Error interno: {e}"}
            return

        texto = "".join(buffer).strip()
        tipo, tid, arg = _extraer_tool(texto)

        if tipo is None:
            yield {
                "tipo": "done",
                "segundos": round(time.time() - t0, 2),
                "tokens": max(1, len(texto) // 4),
            }
            return

        if tipo == "pc":
            if auto_aprobar:
                lote = pc.parsear_lote(texto)
                acciones = lote if len(lote) > 1 else [{"accion": tid, "datos": arg}]
                for a in acciones:
                    nombre = next((t["nombre"] for t in tools.TOOLS if t["id"] == a["accion"]), a["accion"])
                    yield {"tipo": "tool", "id": a["accion"], "nombre": nombre}
                    r = pc.ejecutar(a["accion"], a["datos"])
                    if r.startswith("@@IMAGEN@@"):
                        partes = r.split("\n", 2)
                        datauri = partes[1] if len(partes) > 1 else ""
                        nota = partes[2] if len(partes) > 2 else ""
                        messages.append({"role": "assistant", "content": texto})
                        messages.append({
                            "role": "user",
                            "content": "[Captura de pantalla tomada. Analízala y responde.] " + nota,
                            "imagen": datauri,
                        })
                        break
                    messages.append({"role": "assistant", "content": texto})
                    messages.append({
                        "role": "tool",
                        "content": f"Resultado de la herramienta {a['accion']}:\n{r}",
                    })
                continue
            lote = pc.parsear_lote(texto)
            if len(lote) > 1:
                yield {"tipo": "permiso", "accion": "lote", "datos": lote, "texto": texto}
            else:
                yield {"tipo": "permiso", "accion": tid, "datos": arg, "texto": texto}
            return

        # herramienta automática: se ejecuta y se continúa en otra ronda
        nombre = next((t["nombre"] for t in tools.TOOLS if t["id"] == tid), tid)
        yield {"tipo": "tool", "id": tid, "nombre": nombre}
        resultado = tools.ejecutar(tid, arg)
        if resultado.startswith("@@IMAGEN@@"):
            partes = resultado.split("\n", 2)
            datauri = partes[1] if len(partes) > 1 else ""
            nota = partes[2] if len(partes) > 2 else ""
            messages.append({"role": "assistant", "content": texto})
            messages.append({
                "role": "user",
                "content": "[Captura de pantalla tomada. Analízala y responde.] " + nota,
                "imagen": datauri,
            })
            continue
        messages.append({"role": "assistant", "content": texto})
        messages.append({
            "role": "tool",
            "content": f"Resultado de la herramienta {tid}:\n{resultado}",
        })

    yield {"tipo": "error", "texto": "Demasiadas herramientas seguidas. Reformula la petición."}

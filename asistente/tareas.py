"""
Tareas automáticas de MiClaw.

El usuario (o el propio asistente, vía herramienta) programa una acción:
  {prompt} | {cuándo}
Ej: "busca las noticias de tecnología | mañana a las 9"

Un hilo en segundo plano del servidor ejecuta la tarea cuando llega la hora
(usando el proveedor configurado, con sus herramientas). En las tareas
automáticas las acciones sobre el PC están desactivadas por seguridad.

Se guardan en data/tareas.json.
"""

import datetime
import json
import os
import uuid

from . import config

RUTA = os.path.join(config.DATA_DIR, "tareas.json")

ESTADOS = ("pendiente", "ejecutando", "hecho", "error")


def _load():
    try:
        with open(RUTA, "r", encoding="utf-8") as f:
            lista = json.load(f)
        return lista if isinstance(lista, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save(lista):
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)


def listar():
    lista = _load()
    lista.sort(key=lambda t: t.get("cuando", ""))
    return lista


def crear(prompt, cuando):
    from . import recordatorios
    iso = recordatorios.parse_cuando(cuando)
    if iso is None:
        return None, (
            f'No entendí el momento: "{cuando}". Usa formatos como '
            '"mañana a las 9", "en 30 minutos", "el 5 de septiembre a las 14:30".'
        )
    tid = uuid.uuid4().hex[:8]
    lista = _load()
    lista.append({
        "id": tid,
        "prompt": prompt.strip(),
        "cuando": iso,
        "creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "estado": "pendiente",
        "resultado": "",
    })
    _save(lista)
    return tid, f"🤖 Tarea programada para {iso}: {prompt.strip()}"


def borrar(tid):
    lista = _load()
    nueva = [t for t in lista if t.get("id") != tid]
    if len(nueva) == len(lista):
        return False
    _save(nueva)
    return True


def marcar(tid, estado, resultado=None):
    lista = _load()
    for t in lista:
        if t.get("id") == tid:
            if estado in ESTADOS:
                t["estado"] = estado
            if resultado is not None:
                t["resultado"] = resultado
            _save(lista)
            return True
    return False


def pendientes():
    """Tareas en estado 'pendiente' cuya hora ya llegó."""
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return [t for t in listar() if t.get("estado") == "pendiente" and t.get("cuando", "") <= ahora]

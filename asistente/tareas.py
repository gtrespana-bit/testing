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
import re
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


def _parse_repite(cuando):
    """
    Detecta repeticiones: "cada día a las 9", "todos los días a las 8:30",
    "cada lunes a las 10", "cada hora".
    Devuelve (tipo, hh, mm) o None. El día semanal se guarda en el texto.
    """
    t = (cuando or "").lower().strip()
    if "cada hora" in t or "todas las horas" in t:
        return ("horaria", 0, 0)
    m = re.search(r"(?:cada|todos los)\s+d[ií]a(?:s)?\s+(?:a\s+las\s+)?(\d{1,2})(?::(\d{2}))?", t)
    if m:
        return ("diaria", int(m.group(1)), int(m.group(2) or 0))
    dias = ["lunes", "martes", "mi[eé]rcoles", "jueves", "viernes", "s[aá]bado", "domingo"]
    for i, d in enumerate(dias):
        if re.search(d, t):
            m2 = re.search(r"a\s+las\s+(\d{1,2})(?::(\d{2}))?", t)
            if m2:
                return ("semanal", i, int(m2.group(1)), int(m2.group(2) or 0))
    return None


def _siguiente(rep, ahora=None):
    """Calcula la próxima fecha-hora según el tipo de repetición."""
    ahora = ahora or datetime.datetime.now()
    tipo = rep["tipo"]
    if tipo == "horaria":
        nxt = (ahora + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return nxt.strftime("%Y-%m-%d %H:%M")
    hh, mm = rep.get("hh", 9), rep.get("mm", 0)
    nxt = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if tipo == "diaria":
        if nxt <= ahora:
            nxt += datetime.timedelta(days=1)
    elif tipo == "semanal":
        dia = rep.get("dia", 0)
        dias_faltan = (dia - nxt.weekday()) % 7
        nxt += datetime.timedelta(days=dias_faltan)
        if nxt <= ahora:
            nxt += datetime.timedelta(days=7)
    return nxt.strftime("%Y-%m-%d %H:%M")


def crear(prompt, cuando):
    from . import recordatorios
    rep = _parse_repite(cuando)
    if rep:
        if rep[0] == "semanal":
            rep_dict = {"tipo": "semanal", "dia": rep[1], "hh": rep[2], "mm": rep[3]}
        elif rep[0] == "diaria":
            rep_dict = {"tipo": "diaria", "hh": rep[1], "mm": rep[2]}
        else:
            rep_dict = {"tipo": "horaria"}
        iso = _siguiente(rep_dict)
        etiqueta = "cada día" if rep[0] == "diaria" else "cada hora" if rep[0] == "horaria" else "cada semana"
    else:
        rep_dict = None
        iso = recordatorios.parse_cuando(cuando)
        etiqueta = iso
    if iso is None:
        return None, (
            f'No entendí el momento: "{cuando}". Usa formatos como '
            '"mañana a las 9", "en 30 minutos", "el 5 de septiembre a las 14:30" '
            'o "cada día a las 9" / "cada lunes a las 10".'
        )
    tid = uuid.uuid4().hex[:8]
    lista = _load()
    lista.append({
        "id": tid,
        "prompt": prompt.strip(),
        "cuando": iso,
        "repite": rep_dict,
        "creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "estado": "pendiente",
        "resultado": "",
    })
    _save(lista)
    return tid, f"🤖 Tarea programada ({etiqueta}) para {iso}: {prompt.strip()}"


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


def reagendar(tid):
    """Si la tarea es recurrente, calcula la próxima fecha y vuelve a 'pendiente'."""
    rep = None
    for t in listar():
        if t.get("id") == tid:
            rep = t.get("repite")
            break
    if not rep:
        return
    iso = _siguiente(rep)
    lista = _load()
    for t in lista:
        if t.get("id") == tid:
            t["cuando"] = iso
            t["estado"] = "pendiente"
            t["resultado"] = ""
            break
    _save(lista)

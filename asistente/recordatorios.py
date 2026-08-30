"""
Recordatorios de MiClaw.

Se guardan en data/recordatorios.json. El formato del argumento de la
herramienta es:  {texto} | {cuándo}
  - "hoy a las 18:30"
  - "mañana a las 9"
  - "pasado mañana a las 14:00"
  - "el 5 de septiembre a las 14:30"
  - "en 10 minutos" / "en 2 horas" / "en 1 día"
"""

import datetime
import json
import os
import re
import uuid

from . import config

RUTA = os.path.join(config.DATA_DIR, "recordatorios.json")

MESES = {
    nombre: i for i, nombre in enumerate(
        ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
        start=1,
    )
}


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
    lista.sort(key=lambda r: r.get("cuando", ""))
    return lista


def crear(texto, cuando):
    iso = parse_cuando(cuando)
    if iso is None:
        return None, (
            f'No entendí el momento: "{cuando}". Usa formatos como '
            '"mañana a las 9", "en 10 minutos", "el 5 de septiembre a las 14:30".'
        )
    rid = uuid.uuid4().hex[:8]
    lista = _load()
    lista.append({
        "id": rid,
        "texto": texto.strip(),
        "cuando": iso,
        "creado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(lista)
    return rid, f"⏰ Recordatorio creado para {iso}: {texto.strip()}"


def borrar(rid):
    lista = _load()
    nueva = [r for r in lista if r.get("id") != rid]
    if len(nueva) == len(lista):
        return False
    _save(nueva)
    return True


def vencidos():
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return [r for r in listar() if r.get("cuando", "") <= ahora]


# ---------------------------------------------------------------------------
# Parser de fechas en español
# ---------------------------------------------------------------------------
def parse_cuando(t):
    """Devuelve 'YYYY-MM-DD HH:MM' o None si no entiende el momento."""
    t = re.sub(r"\s+", " ", (t or "").lower().strip())
    now = datetime.datetime.now()

    # "en N minutos|horas|días|semanas"
    m = re.search(r"\ben\s+(\d+)\s*(minutos?|min|horas?|hs?|dias?|días?|semanas?|segundos?)\b", t)
    if m:
        n = int(m.group(1))
        u = m.group(2)
        if u.startswith("min"):
            dt = now + datetime.timedelta(minutes=n)
        elif u.startswith(("h",)):
            dt = now + datetime.timedelta(hours=n)
        elif u.startswith(("sem",)):
            dt = now + datetime.timedelta(weeks=n)
        elif u.startswith(("d",)):
            dt = now + datetime.timedelta(days=n)
        else:
            dt = now + datetime.timedelta(seconds=n)
        return dt.strftime("%Y-%m-%d %H:%M")

    base = now.replace(second=0, microsecond=0)
    dia_offset = 0

    if "pasado mañana" in t or "pasado manana" in t:
        dia_offset = 2
    elif "mañana" in t or "manana" in t:
        dia_offset = 1
    elif "hoy" in t:
        dia_offset = 0
    elif "el " in t:
        m = re.search(r"\bel\s+(\d{1,2})(?:\s+de\s+(\w+))?", t)
        if not m:
            return None
        dia = int(m.group(1))
        mes = MESES.get(m.group(2)) if m.group(2) else None
        try:
            if mes:
                base = base.replace(day=dia, month=mes)
                if base.date() < now.date():
                    base = base.replace(year=base.year + 1)
            else:
                base = base.replace(day=dia)
                if base.date() < now.date():
                    mes_sig = base.month % 12 + 1
                    anno_sig = base.year + (1 if base.month == 12 else 0)
                    base = base.replace(day=dia, month=mes_sig, year=anno_sig)
        except ValueError:
            return None

    base = base + datetime.timedelta(days=dia_offset)

    hh = mm = None
    m = re.search(r"a\s+las\s+(\d{1,2})(?::(\d{2}))?", t)
    if m:
        hh, mm = int(m.group(1)) % 24, int(m.group(2) or 0)
    else:
        m = re.search(r"\b(\d{1,2}):(\d{2})\b", t)
        if m:
            hh, mm = int(m.group(1)) % 24, int(m.group(2))

    if hh is None:
        if dia_offset or "el " in t:
            hh, mm = 9, 0
        else:
            return None

    base = base.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if base < now:
        base += datetime.timedelta(days=1)
    return base.strftime("%Y-%m-%d %H:%M")

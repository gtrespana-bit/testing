"""
Conversaciones persistentes de MiClaw.

Cada conversación es un JSON en data/conversaciones/{id}.json.
Todo vive en tu disco: nada se sube a ningún sitio.
"""

import json
import os
import time
import uuid

from . import config

DIR = os.path.join(config.DATA_DIR, "conversaciones")


def _ensure():
    os.makedirs(DIR, exist_ok=True)


def _path(cid):
    return os.path.join(DIR, f"{cid}.json")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def listar():
    """Lista las conversaciones, de la más reciente a la más antigua."""
    _ensure()
    items = []
    for fname in os.listdir(DIR):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(DIR, fname), encoding="utf-8") as f:
                d = json.load(f)
            items.append({
                "id": d.get("id"),
                "titulo": d.get("titulo", "Sin título"),
                "creada": d.get("creada", ""),
                "actualizada": d.get("actualizada", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    items.sort(key=lambda x: x.get("actualizada") or "", reverse=True)
    return items


def crear(titulo="Nueva conversación"):
    _ensure()
    cid = uuid.uuid4().hex[:12]
    d = {"id": cid, "titulo": titulo, "creada": _now(), "actualizada": _now(), "messages": []}
    with open(_path(cid), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    return cid


def obtener(cid):
    try:
        with open(_path(cid), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def guardar(cid, titulo=None, messages=None):
    d = obtener(cid)
    if d is None:
        return False
    if titulo is not None:
        d["titulo"] = titulo
    if messages is not None:
        d["messages"] = messages
    d["actualizada"] = _now()
    with open(_path(cid), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    return True


def borrar(cid):
    try:
        os.remove(_path(cid))
        return True
    except FileNotFoundError:
        return False

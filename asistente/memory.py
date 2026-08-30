"""
Memoria de MiClaw: una "carpeta de apuntes" que el asistente consulta.

Todo se guarda en data/memoria/ como archivos .txt. Cuando el usuario pide
"recuerda X", se escribe un apunte con su fecha. Cada conversación puede
incluir un resumen de memoria para que el modelo sepa lo que sabes de ti.
"""

import json
import os
import time

from . import config

MEMO_DIR = os.path.join(config.DATA_DIR, "memoria")
MEMORY_INDEX = os.path.join(MEMO_DIR, "_indice.json")


def _ensure():
    os.makedirs(MEMO_DIR, exist_ok=True)


def _load_index():
    _ensure()
    try:
        with open(MEMORY_INDEX, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_index(index):
    _ensure()
    with open(MEMORY_INDEX, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def remember(text):
    """Guarda un apunte y devuelve su nombre."""
    _ensure()
    index = _load_index()
    n = len(index) + 1
    name = f"apunte-{n:03d}"
    path = os.path.join(MEMO_DIR, f"{name}.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text.strip())
    index[name] = {"archivo": f"{name}.txt", "fecha": time.strftime("%Y-%m-%d %H:%M")}
    _save_index(index)
    return name


def read_memory():
    """Devuelve todo el contenido de memoria como texto plano (para el prompt)."""
    _ensure()
    chunks = []
    for fname in sorted(os.listdir(MEMO_DIR)):
        if fname.endswith(".txt"):
            path = os.path.join(MEMO_DIR, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    chunks.append(f"[{fname[:-4]}] {f.read().strip()}")
            except OSError:
                continue
    return "\n\n".join(chunks)


def listar_apuntes():
    """Devuelve [{nombre, contenido, fecha}] para mostrarlos en la interfaz."""
    _ensure()
    index = _load_index()
    apuntes = []
    for fname in sorted(os.listdir(MEMO_DIR)):
        if not fname.endswith(".txt"):
            continue
        nombre = fname[:-4]
        try:
            with open(os.path.join(MEMO_DIR, fname), "r", encoding="utf-8") as f:
                contenido = f.read().strip()
        except OSError:
            continue
        apuntes.append({
            "nombre": nombre,
            "contenido": contenido,
            "fecha": index.get(nombre, {}).get("fecha", ""),
        })
    apuntes.sort(key=lambda a: a["fecha"], reverse=True)
    return apuntes


def borrar(nombre):
    """Borra un apunte concreto. Devuelve True si existía."""
    path = os.path.join(MEMO_DIR, f"{nombre}.txt")
    try:
        os.remove(path)
    except FileNotFoundError:
        return False
    index = _load_index()
    index.pop(nombre, None)
    _save_index(index)
    return True


def forget_all():
    """Borra toda la memoria."""
    _ensure()
    for fname in os.listdir(MEMO_DIR):
        try:
            os.remove(os.path.join(MEMO_DIR, fname))
        except OSError:
            pass

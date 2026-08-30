"""
Informes generados por MiClaw (data/informes/*.md).

Cuando el usuario pide «guarda un informe/resumen de esto», MiClaw usa la
herramienta @@TOOL:informe@@ y el resultado se guarda como Markdown en
data/informes/ (dentro de la carpeta de datos de la app: sin permisos extra).
"""

import datetime
import os
import re

from . import config

DIR = os.path.join(config.DATA_DIR, "informes")


def _ensure():
    os.makedirs(DIR, exist_ok=True)


def _slug(titulo):
    s = re.sub(r"[^\w\sáéíóúñü-]", "", titulo.lower())
    s = re.sub(r"\s+", "-", s).strip("-")
    return (s or "informe")[:40]


def guardar(titulo, contenido):
    _ensure()
    fecha = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    nombre = f"{_slug(titulo)}-{fecha}.md"
    with open(os.path.join(DIR, nombre), "w", encoding="utf-8") as f:
        f.write(f"# {titulo.strip()}\n\n{contenido.strip()}\n")
    return nombre


def listar():
    _ensure()
    items = []
    for fname in sorted(os.listdir(DIR), reverse=True):
        if not fname.endswith(".md"):
            continue
        ruta = os.path.join(DIR, fname)
        try:
            tam = os.path.getsize(ruta)
            mod = datetime.datetime.fromtimestamp(os.path.getmtime(ruta)).strftime("%Y-%m-%d %H:%M")
            items.append({"nombre": fname, "tamano": tam, "fecha": mod})
        except OSError:
            continue
    return items


def leer(nombre):
    ruta = os.path.join(DIR, nombre)
    if not os.path.isfile(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def borrar(nombre):
    ruta = os.path.join(DIR, nombre)
    try:
        os.remove(ruta)
        return True
    except FileNotFoundError:
        return False

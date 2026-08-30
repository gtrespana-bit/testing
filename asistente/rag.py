"""
RAG de código: índice de búsqueda local sobre tus proyectos.

MiClaw indexa una carpeta (por defecto la del proyecto) y puede responder
preguntas sobre TU código: «¿dónde está la función que valida emails?»,
«¿qué hace esta clase?»… Todo es local: sin APIs, sin vectores, sin internet.
"""

import json
import os
import re
import time
from pathlib import Path

from . import config

INDEX_PATH = os.path.join(config.DATA_DIR, "rag_index.json")
EXTENSIONES = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".scss",
               ".md", ".json", ".csv", ".yaml", ".yml", ".toml", ".ini", ".sh",
               ".bat", ".c", ".cpp", ".h", ".java", ".go", ".rs", ".rb", ".php",
               ".sql", ".vue", ".svelte", ".txt", ".cfg", ".conf", ".properties"}
EXCLUIR_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist",
                "build", ".next", ".nuxt", ".cache", ".tox", ".mypy_cache",
                ".pytest_cache", ".ruff_cache", "coverage", "target", "out",
                ".idea", ".vscode", "data"}


def get_ruta():
    return config.load_config().get("rag_ruta", "") or config.BASE_DIR


def set_ruta(ruta):
    cfg = config.load_config()
    cfg["rag_ruta"] = ruta.strip()
    config.save_config(cfg)


def _normalizar(t):
    t = t.lower()
    for a, b in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
                 ("ü", "u"), ("ñ", "n")]:
        t = t.replace(a, b)
    return t


def indexar(ruta=None):
    """Escanea la carpeta y construye el índice. Devuelve estadísticas."""
    ruta = ruta or get_ruta()
    base = Path(ruta)
    if not base.is_dir():
        return {"ok": False, "error": f"No encuentro la carpeta: {ruta}"}
    trozos = []
    archivos = 0
    t0 = time.time()
    for path in base.rglob("*"):
        try:
            if path.is_dir():
                continue
            if path.name in EXCLUIR_DIRS or any(p in EXCLUIR_DIRS for p in path.parts):
                continue
            if path.suffix.lower() not in EXTENSIONES:
                continue
            if path.stat().st_size > 300_000:
                continue
            rel = str(path.relative_to(base))
            if rel.startswith(".") or "/." in rel:
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                texto = f.read()
            lineas = texto.splitlines()
            paso, solape = 40, 5
            for i in range(0, max(1, len(lineas)), paso - solape):
                trozos.append({
                    "archivo": rel,
                    "inicio": i + 1,
                    "texto": "\n".join(lineas[i:i + paso]),
                })
            archivos += 1
        except OSError:
            continue
    data = {
        "ruta": str(base),
        "archivos": archivos,
        "trozos": len(trozos),
        "actualizado": time.strftime("%Y-%m-%d %H:%M"),
        "chunks": trozos,
    }
    os.makedirs(config.DATA_DIR, exist_ok=True)
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return {"ok": True, "archivos": archivos, "trozos": len(trozos),
            "segundos": round(time.time() - t0, 1)}


def estado():
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        return {"indexado": True, "ruta": d.get("ruta", ""),
                "archivos": d.get("archivos", 0), "trozos": d.get("trozos", 0),
                "actualizado": d.get("actualizado", "")}
    except (FileNotFoundError, json.JSONDecodeError):
        return {"indexado": False, "ruta": get_ruta(), "archivos": 0,
                "trozos": 0, "actualizado": ""}


def _cargar():
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _peso(chunk, tokens):
    t = _normalizar(chunk["texto"])
    p = sum(t.count(tok) for tok in tokens)
    # bonus si el trozo contiene una definición
    if re.search(r"\b(def|function|class|const|let|fun|public|private|return)\b",
                 chunk["texto"], re.IGNORECASE):
        p += 2
    return p


def buscar(query, n=6):
    d = _cargar()
    if not d or not d.get("chunks"):
        return ("Aún no hay índice. Configura la carpeta en Ajustes → "
                "Base de conocimiento y pulsa «Indexar».")
    tokens = [t for t in re.findall(r"[a-z0-9_ñ]+", _normalizar(query)) if len(t) >= 3]
    if not tokens:
        return "Consulta demasiado corta. Pregunta por una función, clase o concepto."
    chunks = d["chunks"]
    con_peso = [(c, _peso(c, tokens)) for c in chunks]
    con_peso = [x for x in con_peso if x[1] > 0]
    con_peso.sort(key=lambda x: x[1], reverse=True)
    if not con_peso:
        return f"No encontré nada relacionado con «{query}» en el índice."
    lineas = [f"Resultados en {d.get('ruta', '')}:"]
    for c, p in con_peso[:n]:
        preview = "\n".join(c["texto"].splitlines()[:8])
        lineas.append(f"\n📄 {c['archivo']}:{c['inicio']} (relevancia {p})\n```\n{preview}\n```")
    return "\n".join(lineas)[:6000]

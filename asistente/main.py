"""
MiClaw — servidor local.

Arranca con:  python -m asistente.main   (desde la raíz del proyecto)

Todo corre en tu ordenador: el servidor es local y las claves nunca se suben.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Permitir ejecutar "python -m asistente.main" desde la raíz del repo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import agent, config, pc, providers  # noqa: E402
from .memory import forget_all, read_memory  # noqa: E402

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app = FastAPI(title="MiClaw", version="0.2.0")


# ---------------------------------------------------------------- modelos
class ChatBody(BaseModel):
    messages: list
    provider: str | None = None
    model: str | None = None
    tool_result: str | None = None


class KeyBody(BaseModel):
    provider: str
    key: str


class ModelBody(BaseModel):
    provider: str
    model: str


class PcBody(BaseModel):
    accion: str
    datos: str | dict | None = None


class CustomBody(BaseModel):
    base_url: str
    modelos: list[str] = []


class PcConfigBody(BaseModel):
    carpeta_extra: str = ""


# ---------------------------------------------------------------- API
@app.get("/api/estado")
def estado():
    cfg = config.load_config()
    proveedores = {}
    for pid, info in providers.PROVIDERS.items():
        proveedores[pid] = {
            "nombre": info["nombre"],
            "info": info["info"],
            "enlace": info["enlace"],
            "tipo": info["tipo"],
            "modelos": providers.list_models(pid),
        }
    return {
        "proveedor": cfg.get("proveedor"),
        "modelo": cfg.get("modelo"),
        "claves": {p: bool(k) for p, k in cfg.get("claves", {}).items()},
        "proveedores": proveedores,
        "ollama_activo": bool(providers.list_ollama_models()),
        "custom": config.get_custom(),
        "pc": {"carpeta_extra": (cfg.get("pc") or {}).get("carpeta_extra", "")},
    }


@app.post("/api/clave")
def guardar_clave(body: KeyBody):
    config.set_api_key(body.provider, body.key.strip())
    return {"ok": True}


@app.post("/api/modelo")
def elegir_modelo(body: ModelBody):
    config.set_model(body.provider, body.model)
    return {"ok": True}


@app.post("/api/chat")
def chat(body: ChatBody):
    try:
        resultado = agent.responder(
            body.messages, body.provider, body.model, tool_result=body.tool_result
        )
        return resultado
    except providers.ProviderError as e:
        return {"tipo": "error", "texto": str(e)}
    except Exception as e:
        return {"tipo": "error", "texto": f"Error interno: {e}"}


@app.post("/api/pc/ejecutar")
def pc_ejecutar(body: PcBody):
    """Ejecuta una acción de PC YA aprobada por el usuario."""
    try:
        if body.accion == "ver" and isinstance(body.datos, str):
            resultado = pc.ver_archivo(body.datos)
        elif body.accion == "escribir" and isinstance(body.datos, dict):
            resultado = pc.escribir_archivo(body.datos.get("ruta", ""), body.datos.get("contenido", ""))
        elif body.accion == "terminal" and isinstance(body.datos, str):
            resultado = pc.ejecutar_comando(body.datos)
        elif body.accion == "apuntes":
            resultado = read_memory() or "(sin apuntes)"
        else:
            resultado = "Acción no válida."
        return {"resultado": resultado}
    except Exception as e:
        return {"resultado": f"Error ejecutando la acción: {e}"}


@app.post("/api/custom")
def guardar_custom(body: CustomBody):
    config.set_custom(body.base_url, body.modelos)
    return {"ok": True}


@app.post("/api/pc/config")
def guardar_pc_config(body: PcConfigBody):
    cfg = config.load_config()
    cfg["pc"] = {"carpeta_extra": body.carpeta_extra.strip()}
    config.save_config(cfg)
    return {"ok": True}


@app.get("/api/memoria")
def memoria():
    return {"contenido": read_memory()}


@app.delete("/api/memoria")
def borrar_memoria():
    forget_all()
    return {"ok": True}


# ---------------------------------------------------------------- frontend
@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    print("MiClaw arrancando en http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

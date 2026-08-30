"""
MiClaw — servidor local.

Arranca con:  uvicorn asistente.main:app --host 0.0.0.0 --port 8000
o más fácil:  python asistente/main.py   (desde la raíz del proyecto)

Todo corre en tu ordenador: el servidor es local y las claves nunca se suben.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Permitir ejecutar "python asistente/main.py" desde la raíz del repo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import agent, config, providers  # noqa: E402
from .memory import forget_all, read_memory  # noqa: E402

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app = FastAPI(title="MiClaw", version="0.1.0")


# ---------------------------------------------------------------- modelos
class ChatBody(BaseModel):
    messages: list
    provider: str | None = None
    model: str | None = None


class KeyBody(BaseModel):
    provider: str
    key: str


class ModelBody(BaseModel):
    provider: str
    model: str


# ---------------------------------------------------------------- API
@app.get("/api/estado")
def estado():
    cfg = config.load_config()
    return {
        "proveedor": cfg.get("proveedor"),
        "modelo": cfg.get("modelo"),
        "claves": {p: bool(k) for p, k in cfg.get("claves", {}).items()},
        "proveedores": {
            pid: {
                "nombre": {
                    "ollama": "Ollama (local)",
                    "gemini": "Google Gemini",
                    "groq": "Groq",
                    "openrouter": "OpenRouter",
                }.get(pid, pid),
                "info": providers.PROVIDER_INFO.get(pid, ""),
                "modelos": providers.list_models(pid),
            }
            for pid in ("ollama", "gemini", "groq", "openrouter")
        },
        "ollama_activo": bool(providers.list_ollama_models()),
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
        respuesta = agent.responder(body.messages, body.provider, body.model)
        return {"respuesta": respuesta}
    except providers.ProviderError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Error interno: {e}"}


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

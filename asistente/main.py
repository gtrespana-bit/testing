"""
MiClaw — servidor local.

Arranca con:  python -m asistente.main   (desde la raíz del proyecto)

Todo corre en tu ordenador: el servidor es local y las claves nunca se suben.
"""

import json
import os
import sys
import threading
import time

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Permitir ejecutar "python -m asistente.main" desde la raíz del repo
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from . import agent, config, conversaciones, pc, providers, recordatorios, tareas  # noqa: E402
from .memory import borrar as memory_borrar  # noqa: E402
from .memory import forget_all, listar_apuntes, read_memory  # noqa: E402

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

app = FastAPI(title="MiClaw", version="1.2.0")


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
    datos: str | dict | list | None = None


class CustomBody(BaseModel):
    base_url: str
    modelos: list[str] = []


class PcConfigBody(BaseModel):
    carpeta_extra: str = ""


class ConfigBody(BaseModel):
    memoria_incluida: bool | None = None
    modo: str | None = None


class ProbarBody(BaseModel):
    provider: str | None = None
    model: str | None = None


class ConvCrearBody(BaseModel):
    titulo: str = "Nueva conversación"


class ConvGuardarBody(BaseModel):
    titulo: str | None = None
    messages: list | None = None


class TareaBody(BaseModel):
    prompt: str
    cuando: str


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
        "version": app.version,
        "proveedor": cfg.get("proveedor"),
        "modelo": cfg.get("modelo"),
        "claves": {p: bool(k) for p, k in cfg.get("claves", {}).items()},
        "proveedores": proveedores,
        "ollama_activo": bool(providers.list_ollama_models()),
        "custom": config.get_custom(),
        "pc": {"carpeta_extra": (cfg.get("pc") or {}).get("carpeta_extra", "")},
        "memoria_incluida": cfg.get("memoria_incluida", True),
        "modo": cfg.get("modo", "general"),
        "modos": {
            "general": "General — asistente versátil",
            "programador": "💻 Programador — ingeniero senior (código, bugs, proyectos)",
            "investigador": "🔬 Investigador — fuentes y datos rigurosos",
            "escritor": "✍️ Escritor — redacción y edición",
        },
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
    """Streaming real (NDJSON): cada línea es un evento {tipo, ...}."""

    def gen():
        try:
            for ev in agent.responder_stream(
                body.messages, body.provider, body.model, tool_result=body.tool_result
            ):
                yield json.dumps(ev, ensure_ascii=False) + "\n"
        except providers.ProviderError as e:
            yield json.dumps({"tipo": "error", "texto": str(e)}, ensure_ascii=False) + "\n"
        except Exception as e:
            yield json.dumps({"tipo": "error", "texto": f"Error interno: {e}"}, ensure_ascii=False) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


@app.post("/api/probar")
def probar_conexion(body: ProbarBody):
    """Hace una llamada mínima al proveedor para verificar que la clave funciona."""
    provider = body.provider or config.get_provider()
    model = body.model or config.get_model()
    try:
        respuesta = providers.chat(
            provider, model,
            [{"role": "user", "content": "Responde solo: OK"}],
            max_tokens=10, timeout=45,
        )
        return {"ok": True, "respuesta": (respuesta or "").strip()[:80]}
    except providers.ProviderError as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": f"Error inesperado: {e}"}


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
        elif body.accion == "listar" and isinstance(body.datos, str):
            resultado = pc.listar_carpeta(body.datos)
        elif body.accion == "buscar" and isinstance(body.datos, dict):
            resultado = pc.buscar_en(body.datos.get("ruta", ""), body.datos.get("texto", ""))
        elif body.accion == "documento" and isinstance(body.datos, str):
            resultado = pc.leer_documento(body.datos)
        elif body.accion == "lote" and isinstance(body.datos, list):
            partes = []
            for act in body.datos:
                r = pc.ejecutar(act.get("accion"), act.get("datos"))
                partes.append(f"→ {act.get('accion')}: {r}")
            resultado = "\n\n".join(partes)
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


@app.post("/api/config")
def guardar_config(body: ConfigBody):
    cfg = config.load_config()
    if body.memoria_incluida is not None:
        cfg["memoria_incluida"] = body.memoria_incluida
    if body.modo is not None:
        cfg["modo"] = body.modo
    config.save_config(cfg)
    return {"ok": True}


# ---------------------------------------------------------------- conversaciones
@app.get("/api/conversaciones")
def conversaciones_listar():
    return {"conversaciones": conversaciones.listar()}


@app.post("/api/conversaciones")
def conversaciones_crear(body: ConvCrearBody):
    cid = conversaciones.crear(body.titulo)
    return {"id": cid}


@app.get("/api/conversaciones/{cid}")
def conversaciones_obtener(cid: str):
    d = conversaciones.obtener(cid)
    if d is None:
        return {"error": "no existe"}
    return d


@app.put("/api/conversaciones/{cid}")
def conversaciones_guardar(cid: str, body: ConvGuardarBody):
    ok = conversaciones.guardar(cid, titulo=body.titulo, messages=body.messages)
    return {"ok": ok}


@app.delete("/api/conversaciones/{cid}")
def conversaciones_borrar(cid: str):
    return {"ok": conversaciones.borrar(cid)}


# ---------------------------------------------------------------- recordatorios
@app.get("/api/recordatorios")
def recordatorios_listar():
    return {"recordatorios": recordatorios.listar()}


@app.get("/api/recordatorios/vencidos")
def recordatorios_vencidos():
    return {"vencidos": recordatorios.vencidos()}


@app.delete("/api/recordatorios/{rid}")
def recordatorios_borrar(rid: str):
    return {"ok": recordatorios.borrar(rid)}


# ---------------------------------------------------------------- tareas automáticas
@app.get("/api/tareas")
def tareas_listar():
    return {"tareas": tareas.listar()}


@app.post("/api/tareas")
def tareas_crear(body: TareaBody):
    tid, msg = tareas.crear(body.prompt, body.cuando)
    return {"id": tid, "msg": msg, "ok": tid is not None}


@app.delete("/api/tareas/{tid}")
def tareas_borrar(tid: str):
    return {"ok": tareas.borrar(tid)}


def _bucle_tareas():
    """Ejecuta las tareas programadas cuando llega su hora (hilo en segundo plano)."""
    while True:
        time.sleep(10)
        try:
            for t in tareas.pendientes():
                tareas.marcar(t["id"], "ejecutando")
                try:
                    res = agent.responder(
                        [{"role": "user", "content": t["prompt"]}],
                        no_pc=True,
                    )
                    if res.get("tipo") == "respuesta":
                        tareas.marcar(t["id"], "hecho", resultado=res.get("texto", ""))
                    else:
                        tareas.marcar(t["id"], "hecho",
                                      resultado="(requería aprobación manual; se omitió en modo automático)")
                except providers.ProviderError as e:
                    tareas.marcar(t["id"], "error", resultado=str(e))
                except Exception as e:
                    tareas.marcar(t["id"], "error", resultado=f"Error interno: {e}")
                if t.get("repite"):
                    tareas.reagendar(t["id"])
        except Exception:
            pass


threading.Thread(target=_bucle_tareas, daemon=True).start()


# ---------------------------------------------------------------- memoria
@app.get("/api/memoria")
def memoria():
    return {"contenido": read_memory(), "apuntes": listar_apuntes()}


@app.delete("/api/memoria/{nombre}")
def memoria_borrar_apunte(nombre: str):
    return {"ok": memory_borrar(nombre)}


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

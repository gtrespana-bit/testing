"""
Proveedores de IA soportados por MiClaw.

Todos son GRATIS:
  - "ollama"      → modelos 100% locales (instala Ollama). Sin internet, sin límites.
  - "gemini"      → Google AI Studio. Plan gratuito: ~15 peticiones/min y ~1500/día.
  - "groq"        → muy rápido, gratis. ~30 peticiones/min (puede variar).
  - "openrouter"  → modelos ":free" de muchas familias, sin tarjeta. ~50 peticiones/día
                    (límites de 2026, sujetos a cambios; consulta su web).

Las claves se guardan en data/config.json y solo se usan para llamar a la API.
"""

import json

import httpx

from . import config

TIMEOUT = 120.0

# ---------------------------------------------------------------------------
# Modelos gratuitos conocidos (2026). Puedes usar cualquier otro que exista:
# solo escríbelo en el selector o en ajustes.
# ---------------------------------------------------------------------------
FREE_MODELS = {
    "ollama": [],
    "gemini": [
        {"id": "gemini-2.5-flash", "nombre": "Gemini 2.5 Flash (rápido)"},
        {"id": "gemini-2.5-flash-lite", "nombre": "Gemini 2.5 Flash-Lite (más barato/ligero)"},
        {"id": "gemma-3-27b-it", "nombre": "Gemma 3 27B (abierto)"},
    ],
    "groq": [
        {"id": "llama-3.3-70b-versatile", "nombre": "Llama 3.3 70B"},
        {"id": "llama-3.1-8b-instant", "nombre": "Llama 3.1 8B (muy rápido)"},
        {"id": "openai/gpt-oss-120b", "nombre": "GPT-OSS 120B"},
        {"id": "moonshotai/kimi-k2-instruct", "nombre": "Kimi K2"},
    ],
    "openrouter": [
        {"id": "meta-llama/llama-3.3-70b-instruct:free", "nombre": "Llama 3.3 70B :free"},
        {"id": "deepseek/deepseek-chat-v3-0324:free", "nombre": "DeepSeek V3 :free"},
        {"id": "qwen/qwen3-32b:free", "nombre": "Qwen3 32B :free"},
        {"id": "google/gemma-3-27b-it:free", "nombre": "Gemma 3 27B :free"},
    ],
}

PROVIDER_INFO = {
    "ollama": "Modelos locales. Instala Ollama (ollama.com), luego 'ollama pull llama3.2'.",
    "gemini": "Clave gratis en aistudio.google.com/apikey (sin tarjeta).",
    "groq": "Clave gratis en console.groq.com/keys (sin tarjeta).",
    "openrouter": "Clave gratis en openrouter.ai/keys (sin tarjeta). Modelos ':free'.",
}


class ProviderError(Exception):
    """Error legible de un proveedor (clave mala, límite, sin internet...)."""


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------
def _ollama_list_models():
    try:
        r = httpx.get(f"{config.OLLAMA_URL}/api/tags", timeout=5)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def ollama_chat(model, messages):
    payload = {"model": model, "messages": messages, "stream": False}
    with httpx.Client(timeout=TIMEOUT) as client:
        try:
            r = client.post(f"{config.OLLAMA_URL}/api/chat", json=payload)
        except httpx.ConnectError:
            raise ProviderError(
                "No encuentro Ollama en el puerto 11434. "
                "Instálalo en ollama.com y ejecuta: ollama pull " + model
            )
        except httpx.TimeoutException:
            raise ProviderError("Ollama no responde. ¿Está abierto? Prueba: ollama serve")
        r.raise_for_status()
        return r.json()["message"]["content"]


# ---------------------------------------------------------------------------
# OpenAI-compatible (Groq y OpenRouter)
# ---------------------------------------------------------------------------
def openai_compatible_chat(provider, base_url, model, messages, api_key):
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "messages": messages}
    with httpx.Client(timeout=TIMEOUT) as client:
        try:
            r = client.post(base_url, json=payload, headers=headers)
        except httpx.ConnectError:
            raise ProviderError(f"No hay conexión con {provider}. ¿Tienes internet?")
        except httpx.TimeoutException:
            raise ProviderError(f"{provider} tardó demasiado en responder.")
        except httpx.HTTPError as e:
            raise ProviderError(f"Error de red con {provider}: {e}")

    if r.status_code == 401 or r.status_code == 403:
        raise ProviderError(
            f"{provider} rechazó la clave (401/403). "
            f"Revísala en el panel de claves o genera una nueva."
        )
    if r.status_code == 402:
        raise ProviderError(
            f"{provider}: saldo/plan requerido. Usa un modelo ':free' o prueba Gemini/Groq."
        )
    if r.status_code == 429:
        raise ProviderError(
            f"{provider}: límite de peticiones alcanzado. Espera un minuto y vuelve a intentar."
        )
    if r.status_code >= 400:
        raise ProviderError(f"{provider} respondió con error {r.status_code}: {r.text[:300]}")

    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise ProviderError(f"Respuesta inesperada de {provider}: {str(data)[:300]}")


# ---------------------------------------------------------------------------
# Gemini (Google AI Studio)
# ---------------------------------------------------------------------------
def gemini_chat(model, messages, api_key):
    # Convertimos los mensajes del chat al formato de Gemini
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    contents = [
        {"role": "user" if m["role"] in ("user", "tool") else "model",
         "parts": [{"text": m["content"]}]}
        for m in rest
    ]
    payload = {"contents": contents}
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
           f":generateContent?key={api_key}")
    with httpx.Client(timeout=TIMEOUT) as client:
        try:
            r = client.post(url, json=payload)
        except httpx.ConnectError:
            raise ProviderError("No hay conexión con Google. ¿Tienes internet?")
        except httpx.TimeoutException:
            raise ProviderError("Gemini tardó demasiado en responder.")
        except httpx.HTTPError as e:
            raise ProviderError(f"Error de red con Gemini: {e}")

    if r.status_code in (400, 403):
        raise ProviderError(f"Gemini rechazó la petición ({r.status_code}). ¿Es válida la clave o el modelo?")
    if r.status_code == 429:
        raise ProviderError("Gemini: límite de peticiones alcanzado. Espera un poco y reintenta.")
    if r.status_code == 404:
        raise ProviderError(f"Gemini: el modelo '{model}' no existe o no está en el plan gratis.")
    if r.status_code >= 400:
        raise ProviderError(f"Gemini respondió con error {r.status_code}: {r.text[:300]}")

    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        bloqueo = data.get("promptFeedback", {}).get("blockReason")
        if bloqueo:
            raise ProviderError(f"Gemini bloqueó la petición (motivo: {bloqueo}).")
        raise ProviderError(f"Respuesta inesperada de Gemini: {str(data)[:300]}")


# ---------------------------------------------------------------------------
# Despacho principal
# ---------------------------------------------------------------------------
def chat(provider, model, messages):
    """Envía la conversación al proveedor elegido y devuelve el texto de respuesta."""
    if provider == "ollama":
        return ollama_chat(model, messages)
    if provider == "gemini":
        key = config.get_api_key("gemini")
        if not key:
            raise ProviderError("Falta la clave de Gemini. Añádela en Ajustes → Claves.")
        return gemini_chat(model, messages, key)
    if provider == "groq":
        key = config.get_api_key("groq")
        if not key:
            raise ProviderError("Falta la clave de Groq. Añádela en Ajustes → Claves.")
        return openai_compatible_chat(
            "Groq", "https://api.groq.com/openai/v1/chat/completions", model, messages, key
        )
    if provider == "openrouter":
        key = config.get_api_key("openrouter")
        if not key:
            raise ProviderError("Falta la clave de OpenRouter. Añádela en Ajustes → Claves.")
        return openai_compatible_chat(
            "OpenRouter", "https://openrouter.ai/api/v1/chat/completions", model, messages, key
        )
    raise ProviderError(f"Proveedor desconocido: {provider}")


def list_ollama_models():
    """Modelos locales instalados (si Ollama está corriendo)."""
    names = _ollama_list_models()
    return [{"id": n, "nombre": n} for n in names if "embed" not in n and ":" not in n.split(":")[0]]


def list_models(provider):
    if provider == "ollama":
        return list_ollama_models()
    return FREE_MODELS.get(provider, [])

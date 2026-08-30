"""
Proveedores de IA soportados por MiClaw.

Todos son GRATIS (2026, sujeto a cambios — el panel de ajustes permite
cambiar de proveedor en un clic y el proveedor personalizado acepta
cualquier API compatible con OpenAI):

  - "ollama"     → modelos 100% locales. Sin internet, sin límites.
  - "gemini"     → Google AI Studio. Plan gratis: ~15 peticiones/min, ~1.500/día.
  - "groq"       → muy rápido, gratis. ~30 peticiones/min.
  - "openrouter" → modelos ":free" de muchas familias, sin tarjeta.
  - "alibaba"    → Qwen oficial (DashScope). Prueba gratis de ~1M tokens
                   al activar Model Studio (90 días, región Singapur).
                   Incluye Qwen 3.8-Max, Qwen3-Plus, Qwen3-Coder, QwQ...
  - "mistral"    → plan Experiment gratis (~1.000M tokens/mes), verificación por teléfono.
  - "cerebras"   → plan gratis: ~1M tokens/día, sin tarjeta.
  - "zai"        → Zhipu GLM: GLM-4.5-Flash gratis de verdad (0 €/token).
  - "github"     → GitHub Models: GPT-4.1-mini, o3-mini, Llama 4, DeepSeek-R1
                   gratis con tu cuenta de GitHub.
  - "sambanova"  → plan free (sin tarjeta): Llama y Qwen.
  - "custom"     → CUALQUIER API compatible con OpenAI: tú pones la URL base
                   y los modelos (vLLM, LM Studio, otros agregadores...).

Las claves se guardan en data/config.json y solo se usan para llamar a la API.
"""

import json

import httpx

from . import config

TIMEOUT = 120.0
OLLAMA_URL = config.OLLAMA_URL

# ---------------------------------------------------------------------------
# Registro de proveedores
# ---------------------------------------------------------------------------
PROVIDERS = {
    "ollama": {
        "nombre": "Ollama (100% local)",
        "info": ("Modelos locales en tu PC: sin internet y sin límites. "
                 "Instala Ollama (ollama.com) y ejecuta: ollama pull llama3.2"),
        "enlace": "https://ollama.com",
        "tipo": "local",
        "modelos": [],
    },
    "gemini": {
        "nombre": "Google Gemini",
        "info": ("Plan gratis: ~15 peticiones/min y ~1.500/día. "
                 "Clave gratis en AI Studio (sin tarjeta)."),
        "enlace": "https://aistudio.google.com/apikey",
        "tipo": "clave",
        "modelos": [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemma-3-27b-it",
        ],
    },
    "groq": {
        "nombre": "Groq (ultrarrápido)",
        "info": ("Plan gratis: ~30 peticiones/min. Modelos Llama, GPT-OSS, "
                 "Kimi, Qwen... sin tarjeta."),
        "enlace": "https://console.groq.com/keys",
        "tipo": "clave",
        "modelos": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
            "moonshotai/kimi-k2-instruct",
        ],
    },
    "openrouter": {
        "nombre": "OpenRouter",
        "info": ("Todas las familias en un solo sitio. Modelos ':free' sin "
                 "tarjeta (~50 peticiones/día)."),
        "enlace": "https://openrouter.ai/keys",
        "tipo": "clave",
        "modelos": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "qwen/qwen3-32b:free",
            "google/gemma-3-27b-it:free",
        ],
    },
    "alibaba": {
        "nombre": "Alibaba Qwen (DashScope)",
        "info": ("Qwen oficial: Qwen 3.8-Max, Qwen3-Plus, Coder, QwQ, VL... "
                 "Prueba gratis de ~1M tokens al activar Model Studio "
                 "(90 días, región Singapur). Sin tarjeta."),
        "enlace": "https://bailian.console.alibabacloud.com",
        "tipo": "clave",
        "modelos": [
            "qwen3.8-max",
            "qwen3-max",
            "qwen3-plus",
            "qwen3-coder-plus",
            "qwq-plus",
            "qwen3-vl-plus",
        ],
    },
    "mistral": {
        "nombre": "Mistral",
        "info": ("Plan Experiment gratis (~1.000M tokens/mes): Mistral Large, "
                 "Small, Codestral... Verificación por teléfono, sin tarjeta."),
        "enlace": "https://console.mistral.ai/api-keys",
        "tipo": "clave",
        "modelos": [
            "mistral-large-latest",
            "mistral-small-latest",
            "open-mistral-nemo",
            "codestral-latest",
        ],
    },
    "cerebras": {
        "nombre": "Cerebras (ultrarrápido)",
        "info": ("Plan gratis: ~1M tokens/día (Llama, Qwen3, GPT-OSS). "
                 "Sin tarjeta, sin lista de espera."),
        "enlace": "https://cloud.cerebras.ai",
        "tipo": "clave",
        "modelos": [
            "llama-3.3-70b",
            "llama-3.1-8b-instant",
            "qwen3-32b",
            "gpt-oss-120b",
        ],
    },
    "zai": {
        "nombre": "Z.ai (GLM)",
        "info": ("Zhipu GLM. GLM-4.5-Flash y GLM-4.7-Flash son gratis de "
                 "verdad (0 €/token). Sin tarjeta."),
        "enlace": "https://z.ai/console",
        "tipo": "clave",
        "modelos": [
            "glm-4.5-flash",
            "glm-4.7-flash",
            "glm-4.6v-flash",
            "glm-4.5-air",
        ],
    },
    "github": {
        "nombre": "GitHub Models",
        "info": ("Gratis con tu cuenta de GitHub: GPT-4.1-mini, o3-mini, "
                 "Llama 4, DeepSeek-R1... ~15 peticiones/min."),
        "enlace": "https://github.com/marketplace/models",
        "tipo": "clave",
        "modelos": [
            "openai/gpt-4.1-mini",
            "openai/gpt-4o-mini",
            "openai/o3-mini",
            "meta/llama-3.3-70b-instruct",
            "meta/llama-4-scout-17b-16e-instruct",
            "deepseek-ai/DeepSeek-R1",
            "microsoft/phi-4",
        ],
    },
    "sambanova": {
        "nombre": "SambaNova",
        "info": ("Plan free sin tarjeta: Llama y Qwen en sus chips. "
                 "Límites: consulta su web."),
        "enlace": "https://cloud.sambanova.ai",
        "tipo": "clave",
        "modelos": [
            "Meta-Llama-3.3-70B-Instruct",
            "Qwen2.5-72B-Instruct",
            "Meta-Llama-3.1-8B-Instruct",
        ],
    },
    "custom": {
        "nombre": "Personalizado (OpenAI-compatible)",
        "info": ("Cualquier API compatible con OpenAI: pega su URL base, "
                 "los modelos y tu clave (vLLM, LM Studio, otros...)."),
        "enlace": "",
        "tipo": "clave",
        "modelos": [],
    },
}

# URL base de cada proveedor OpenAI-compatible (sin /chat/completions)
OPENAI_BASE = {
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "alibaba": "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "mistral": "https://api.mistral.ai/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "zai": "https://api.z.ai/api/paas/v4",
    "github": "https://models.inference.ai.azure.com",
    "sambanova": "https://api.sambanova.ai/v1",
}


class ProviderError(Exception):
    """Error legible de un proveedor (clave mala, límite, sin internet...)."""


# ---------------------------------------------------------------------------
# Ayudas para mensajes con IMÁGENES (visión)
# Formato de mensaje de MiClaw:
#   {"role": "user", "content": "texto", "imagen": "data:image/png;base64,XXXX"}
# ---------------------------------------------------------------------------
def _split_data_uri(data_uri):
    """Devuelve (mime, base64) de una data URI, o (None, None)."""
    try:
        meta, b64 = data_uri.split(",", 1)
        mime = meta.split(";")[0].split(":", 1)[1]
        return mime, b64
    except Exception:
        return None, None


def _parse_json(data):
    """Parsea un fragmento SSE sin depender de que 'json' esté en el ámbito global.

    Se usa en los streamers para que el fallo clásico
    `Error interno: name 'json' is not defined` sea imposible.
    """
    try:
        _json = json
    except NameError:
        import json as _json

    try:
        return _json.loads(data)
    except (_json.JSONDecodeError, ValueError, TypeError):
        return None


def _build_openai_messages(messages):
    """Convierte mensajes de MiClaw al formato OpenAI (con imágenes)."""
    out = []
    for m in messages:
        rol = m["role"] if m["role"] != "tool" else "user"
        if m.get("imagen"):
            contenido = [{"type": "text", "text": m["content"] or "Describe esta imagen."}]
            contenido.append({"type": "image_url", "image_url": {"url": m["imagen"]}})
            out.append({"role": rol, "content": contenido})
        else:
            out.append({"role": rol, "content": m["content"]})
    return out


def _build_gemini_contents(messages):
    """Convierte mensajes de MiClaw al formato de Gemini (con imágenes)."""
    contents = []
    for m in messages:
        if m["role"] == "system":
            continue
        parts = []
        if m.get("imagen"):
            mime, b64 = _split_data_uri(m["imagen"])
            if mime and b64:
                parts.append({"inlineData": {"mimeType": mime, "data": b64}})
        parts.append({"text": m["content"] or "Describe esta imagen."})
        contents.append({
            "role": "user" if m["role"] in ("user", "tool") else "model",
            "parts": parts,
        })
    return contents


def _build_ollama_messages(messages):
    """Convierte mensajes de MiClaw al formato de Ollama (con imágenes)."""
    out = []
    for m in messages:
        msg = {"role": m["role"], "content": m["content"]}
        if m.get("imagen"):
            _mime, b64 = _split_data_uri(m["imagen"])
            if b64:
                msg["images"] = [b64]
        out.append(msg)
    return out


# ---------------------------------------------------------------------------
# Ollama (local)
# ---------------------------------------------------------------------------
def _ollama_list_models():
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []


def ollama_chat(model, messages, max_tokens=None, timeout=TIMEOUT):
    payload = {"model": model, "messages": _build_ollama_messages(messages), "stream": False}
    if max_tokens:
        payload["options"] = {"num_predict": max_tokens}
    with httpx.Client(timeout=timeout) as client:
        try:
            r = client.post(f"{OLLAMA_URL}/api/chat", json=payload)
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
# OpenAI-compatible (Groq, OpenRouter, Alibaba, Mistral, Cerebras, Z.ai,
# GitHub Models, SambaNova y el proveedor personalizado)
# ---------------------------------------------------------------------------
def _extra_body(provider):
    """Parámetros extra del proveedor. Para Alibaba/Qwen, si el modo
    razonamiento está desactivado, pedimos enable_thinking=False (responde
    mucho más rápido al no generar la cadena de pensamiento oculta)."""
    if provider == "alibaba" and not config.get_razonamiento():
        return {"enable_thinking": False}
    return None


def openai_compatible_chat(provider, base_url, model, messages, api_key,
                           max_tokens=None, timeout=TIMEOUT, extra_body=None):
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "messages": _build_openai_messages(messages)}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    if extra_body:
        payload["extra_body"] = extra_body
    url = base_url.rstrip("/") + "/chat/completions"
    with httpx.Client(timeout=timeout) as client:
        try:
            r = client.post(url, json=payload, headers=headers)
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
            f"{provider}: saldo/plan requerido (402). Usa un modelo gratuito "
            f"o prueba otro proveedor del panel."
        )
    if r.status_code == 429:
        raise ProviderError(
            f"{provider}: límite de peticiones alcanzado (429). "
            f"Espera un minuto y vuelve a intentar, o cambia de proveedor."
        )
    if r.status_code == 404:
        raise ProviderError(
            f"{provider}: el modelo '{model}' no existe o no está disponible "
            f"gratis. Revisa el nombre en Ajustes."
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
def gemini_chat(model, messages, api_key, max_tokens=None, timeout=TIMEOUT):
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    contents = _build_gemini_contents(messages)
    payload = {"contents": contents}
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
    if max_tokens:
        payload["generationConfig"] = {"maxOutputTokens": max_tokens}

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
           f":generateContent?key={api_key}")
    with httpx.Client(timeout=timeout) as client:
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
def chat(provider, model, messages, max_tokens=None, timeout=TIMEOUT):
    """Envía la conversación al proveedor elegido y devuelve el texto de respuesta."""
    if provider == "ollama":
        return ollama_chat(model, messages, max_tokens, timeout)

    if provider == "gemini":
        key = config.get_api_key("gemini")
        if not key:
            raise ProviderError("Falta la clave de Gemini. Añádela en Ajustes → Claves.")
        return gemini_chat(model, messages, key, max_tokens, timeout)

    if provider == "custom":
        c = config.get_custom()
        if not c["base_url"]:
            raise ProviderError("Configura la URL base del proveedor personalizado en Ajustes.")
        key = config.get_api_key("custom")
        if not key:
            raise ProviderError("Falta la clave del proveedor personalizado. Añádela en Ajustes.")
        return openai_compatible_chat("personalizado", c["base_url"], model, messages, key,
                                      max_tokens, timeout)

    if provider in OPENAI_BASE:
        key = config.get_api_key(provider)
        if not key:
            raise ProviderError(
                f"Falta la clave de {PROVIDERS.get(provider, {}).get('nombre', provider)}. "
                f"Añádela en Ajustes → Claves."
            )
        return openai_compatible_chat(
            PROVIDERS.get(provider, {}).get("nombre", provider),
            OPENAI_BASE[provider], model, messages, key, max_tokens, timeout,
            extra_body=_extra_body(provider),
        )

    raise ProviderError(f"Proveedor desconocido: {provider}")


def stream_openai_compatible(provider, base_url, model, messages, api_key,
                             max_tokens=None, timeout=TIMEOUT, extra_body=None):
    """Versión en streaming (SSE) de las APIs compatibles con OpenAI.

    Cada trozo es un dict {"texto": ..., "razon": ...}: "razon" recoge la
    cadena de pensamiento del modelo (reasoning) cuando el proveedor la
    envía en un campo aparte (DeepSeek, Qwen, o-series…)."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": model, "messages": _build_openai_messages(messages), "stream": True}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    if extra_body:
        payload["extra_body"] = extra_body
    url = base_url.rstrip("/") + "/chat/completions"
    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", url, json=payload, headers=headers) as r:
                if r.status_code in (401, 403):
                    raise ProviderError(f"{provider} rechazó la clave (401/403). Revísala en el panel de claves.")
                if r.status_code == 429:
                    raise ProviderError(f"{provider}: límite de peticiones alcanzado (429). Espera un minuto.")
                if r.status_code == 402:
                    raise ProviderError(f"{provider}: saldo/plan requerido (402). Usa un modelo gratuito.")
                if r.status_code == 404:
                    raise ProviderError(f"{provider}: el modelo '{model}' no existe o no está gratis.")
                if r.status_code >= 400:
                    cuerpo = r.read().decode(errors="replace")[:300]
                    raise ProviderError(f"{provider} respondió con error {r.status_code}: {cuerpo}")
                for line in r.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    obj = _parse_json(data)
                    if not isinstance(obj, dict):
                        continue
                    delta = (obj.get("choices") or [{}])[0].get("delta", {})
                    contenido = delta.get("content")
                    razon = delta.get("reasoning_content") or delta.get("reasoning") or ""
                    if contenido or razon:
                        yield {"texto": contenido or "", "razon": razon or ""}
    except httpx.ConnectError:
        raise ProviderError(f"No hay conexión con {provider}. ¿Tienes internet?")
    except httpx.TimeoutException:
        raise ProviderError(f"{provider} tardó demasiado en responder.")
    except httpx.HTTPError as e:
        raise ProviderError(f"Error de red con {provider}: {e}")


def stream_gemini(model, messages, api_key, max_tokens=None, timeout=TIMEOUT):
    """Versión en streaming de Gemini (SSE con streamGenerateContent)."""
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    contents = _build_gemini_contents(messages)
    payload = {"contents": contents}
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
    if max_tokens:
        payload["generationConfig"] = {"maxOutputTokens": max_tokens}

    url = (f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
           f":streamGenerateContent?alt=sse&key={api_key}")
    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", url, json=payload) as r:
                if r.status_code in (400, 403):
                    raise ProviderError(f"Gemini rechazó la petición ({r.status_code}). ¿Es válida la clave o el modelo?")
                if r.status_code == 429:
                    raise ProviderError("Gemini: límite de peticiones alcanzado. Espera un poco y reintenta.")
                if r.status_code == 404:
                    raise ProviderError(f"Gemini: el modelo '{model}' no existe o no está en el plan gratis.")
                if r.status_code >= 400:
                    cuerpo = r.read().decode(errors="replace")[:300]
                    raise ProviderError(f"Gemini respondió con error {r.status_code}: {cuerpo}")
                for line in r.iter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data:
                        continue
                    obj = _parse_json(data)
                    if not isinstance(obj, dict):
                        continue
                    try:
                        parts = obj["candidates"][0]["content"]["parts"]
                    except (KeyError, IndexError, TypeError):
                        continue
                    contenido = ""
                    razon = ""
                    for parte in parts:
                        txt = parte.get("text", "") or ""
                        if parte.get("thought"):
                            razon += txt
                        else:
                            contenido += txt
                    if contenido or razon:
                        yield {"texto": contenido, "razon": razon}
    except httpx.ConnectError:
        raise ProviderError("No hay conexión con Google. ¿Tienes internet?")
    except httpx.TimeoutException:
        raise ProviderError("Gemini tardó demasiado en responder.")
    except httpx.HTTPError as e:
        raise ProviderError(f"Error de red con Gemini: {e}")


def stream_ollama(model, messages, max_tokens=None, timeout=TIMEOUT):
    """Versión en streaming de Ollama (NDJSON)."""
    payload = {"model": model, "messages": _build_ollama_messages(messages), "stream": True}
    if max_tokens:
        payload["options"] = {"num_predict": max_tokens}
    try:
        with httpx.Client(timeout=timeout) as client:
            with client.stream("POST", f"{OLLAMA_URL}/api/chat", json=payload) as r:
                if r.status_code >= 400:
                    raise ProviderError(f"Ollama respondió con error {r.status_code}")
                for line in r.iter_lines():
                    if not line:
                        continue
                    obj = _parse_json(line)
                    if not isinstance(obj, dict):
                        continue
                    msg = obj.get("message") or {}
                    contenido = msg.get("content")
                    razon = msg.get("thinking") or ""
                    if contenido or razon:
                        yield {"texto": contenido or "", "razon": razon or ""}
                    if obj.get("done"):
                        break
    except httpx.ConnectError:
        raise ProviderError(
            "No encuentro Ollama en el puerto 11434. "
            "Instálalo en ollama.com y ejecuta: ollama pull " + model
        )
    except httpx.TimeoutException:
        raise ProviderError("Ollama no responde. ¿Está abierto? Prueba: ollama serve")


def stream_chat(provider, model, messages, max_tokens=None, timeout=TIMEOUT):
    """Generador: igual que chat() pero devuelve trozos en vivo.

    Cada trozo es un dict {"texto": ..., "razon": ...} (razon = pensamiento
    del modelo, vacío si el proveedor no lo envía)."""
    if provider == "ollama":
        return stream_ollama(model, messages, max_tokens, timeout)

    if provider == "gemini":
        key = config.get_api_key("gemini")
        if not key:
            raise ProviderError("Falta la clave de Gemini. Añádela en Ajustes → Claves.")
        return stream_gemini(model, messages, key, max_tokens, timeout)

    if provider == "custom":
        c = config.get_custom()
        if not c["base_url"]:
            raise ProviderError("Configura la URL base del proveedor personalizado en Ajustes.")
        key = config.get_api_key("custom")
        if not key:
            raise ProviderError("Falta la clave del proveedor personalizado. Añádela en Ajustes.")
        return stream_openai_compatible("personalizado", c["base_url"], model, messages, key,
                                        max_tokens, timeout)

    if provider in OPENAI_BASE:
        key = config.get_api_key(provider)
        if not key:
            raise ProviderError(
                f"Falta la clave de {PROVIDERS.get(provider, {}).get('nombre', provider)}. "
                f"Añádela en Ajustes → Claves."
            )
        return stream_openai_compatible(
            PROVIDERS.get(provider, {}).get("nombre", provider),
            OPENAI_BASE[provider], model, messages, key, max_tokens, timeout,
            extra_body=_extra_body(provider),
        )

    raise ProviderError(f"Proveedor desconocido: {provider}")


def list_ollama_models():
    """Modelos locales instalados (si Ollama está corriendo)."""
    names = _ollama_list_models()
    return [{"id": n, "nombre": n} for n in names if "embed" not in n and ":" not in n.split(":")[0]]


def list_models(provider):
    if provider == "ollama":
        return list_ollama_models()
    if provider == "custom":
        return [{"id": m, "nombre": m} for m in config.get_custom()["modelos"]]
    return [{"id": m, "nombre": m} for m in PROVIDERS.get(provider, {}).get("modelos", [])]

"""
Configuración de MiClaw.

Toda la configuración (claves API, modelo elegido) se guarda en
data/config.json, en TU ordenador. Nunca sale de ahí.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

DEFAULT_CONFIG = {
    "proveedor": "gemini",      # proveedor activo
    "modelo": "gemini-2.5-flash",  # modelo activo
    "claves": {},               # {proveedor: api_key}
}

# Los modelos locales los sirve Ollama (http://localhost:11434).
OLLAMA_URL = "http://localhost:11434"


def _sanitize(value):
    """Devuelve el valor si parece una clave/string razonable."""
    if isinstance(value, str) and len(value) < 500:
        return value
    return ""


def load_config():
    config = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            config.update(saved)
    except FileNotFoundError:
        pass
    except (json.JSONDecodeError, OSError):
        pass
    return config


def save_config(config):
    os.makedirs(DATA_DIR, exist_ok=True)
    # Los archivos con claves se crean legibles solo por el usuario
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_api_key(proveedor):
    config = load_config()
    return config.get("claves", {}).get(proveedor, "")


def set_api_key(proveedor, key):
    config = load_config()
    config.setdefault("claves", {})[proveedor] = _sanitize(key)
    save_config(config)


def get_provider():
    return load_config().get("proveedor", DEFAULT_CONFIG["proveedor"])


def get_model():
    return load_config().get("modelo", DEFAULT_CONFIG["modelo"])


def set_model(proveedor, modelo):
    config = load_config()
    config["proveedor"] = proveedor
    config["modelo"] = modelo
    save_config(config)


def get_custom():
    """Configuración del proveedor personalizado (URL base + modelos)."""
    cfg = load_config()
    c = cfg.get("custom") or {}
    return {
        "base_url": c.get("base_url", ""),
        "modelos": c.get("modelos", []),
    }


def set_custom(base_url, modelos):
    cfg = load_config()
    cfg["custom"] = {
        "base_url": base_url.strip(),
        "modelos": [m.strip() for m in modelos if m.strip()],
    }
    save_config(cfg)

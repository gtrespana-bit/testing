# 🦞 MiClaw — tu asistente personal de IA, 100% gratis y en tu PC

Un asistente estilo **OpenClaw** pero tuyo: corre en tu ordenador, usa modelos de
IA **gratuitos** (locales o en la nube con plan free) y toda tu información
(conversaciones, claves, memoria) se queda en tu disco.

## ¿Qué hace ya?

- 💬 **Chat** con varios proveedores de IA, todos gratis:
  - **Ollama** — modelos 100% locales (sin internet, ilimitado). Requiere instalar Ollama.
  - **Google Gemini** — plan gratis: ~15 peticiones/min, ~1.500/día.
  - **Groq** — muy rápido, gratis (límites de ~30 peticiones/min).
  - **OpenRouter** — modelos `:free` de muchas familias, sin tarjeta (~50 peticiones/día).
- 🔍 **Buscar en internet**: pídele «busca en internet…» y usa DuckDuckGo (sin clave).
- 🧠 **Memoria**: pídele «recuerda que…» y lo guarda en `data/memoria/`; lo consulta en cada conversación.
- ⚙️ **Panel de ajustes**: cambia de proveedor/modelo y guarda tus claves (solo en tu PC).

## Requisitos

- Python 3.10+ (cualquier sistema: Windows, Linux, macOS)
- Opcional: [Ollama](https://ollama.com) para modelos locales

## Instalación

**Linux / macOS** (un comando):

```bash
scripts/instalar.sh
```

**Windows** (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Arrancar

```bash
scripts/arrancar.sh
# o manualmente:
# python asistente/main.py
```

Abre **http://localhost:8000** en tu navegador.

## Primeros pasos

1. Ve a **Ajustes** y elige un proveedor:
   - **Gemini**: clave gratis en https://aistudio.google.com/apikey (sin tarjeta).
   - **Groq**: clave gratis en https://console.groq.com/keys.
   - **OpenRouter**: clave gratis en https://openrouter.ai/keys; usa modelos `:free`.
   - **Ollama** (local): instálalo, luego `ollama pull llama3.2` y elígelo en Ajustes.
2. Escribe en el chat. Prueba:
   - «busca en internet las noticias de hoy»
   - «recuerda que mi cumpleaños es el 3 de mayo»
   - «¿Qué es OpenClaw?»

## Estructura

```
asistente/
  main.py        → servidor web local (FastAPI)
  agent.py       → orquesta conversación + herramientas
  providers.py   → Gemini, Groq, OpenRouter, Ollama
  tools.py       → búsqueda web y notas
  memory.py      → memoria persistente (data/memoria/)
  static/        → interfaz web (chat + ajustes + memoria)
data/            → tus datos locales (no se sube a git)
scripts/         → instalar.sh y arrancar.sh
```

## Notas honestas

- Los planes gratis cambian de límites con el tiempo; si un proveedor da error,
  revisa su web oficial o cambia a otro (el panel lo hace fácil).
- Tu privacidad depende de dónde corra el modelo: Ollama es 100% local;
  Gemini/Groq/OpenRouter envían tu mensaje a sus servidores (plan gratis).
- Las claves se guardan en `data/config.json` con permisos restringidos.

## Ideas para el futuro (fáciles de añadir)

- Conversaciones guardadas por sesión (ahora al pulsar «Nueva» se pierden).
- Más herramientas: calculadora, recordatorios, archivos, voz.
- Modo agente con más pasos (el modelo decide varias herramientas seguidas).

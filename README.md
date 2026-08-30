# 🦞 MiClaw — tu asistente personal de IA, 100% gratis y en tu PC

Un asistente estilo **OpenClaw** pero tuyo: corre en tu ordenador, usa modelos de
IA **gratuitos** (locales o en la nube con plan free) y toda tu información
(conversaciones, claves, memoria) se queda en tu disco.

## ¿Qué hace?

- 💬 **Chat** con muchos proveedores de IA, todos gratuitos (sin tarjeta):
  - **Ollama** — modelos 100% locales (sin internet, ilimitado). Instala Ollama.
  - **Google Gemini** — plan gratis: ~15 peticiones/min, ~1.500/día.
  - **Groq** — ultrarrápido, gratis (~30 peticiones/min).
  - **OpenRouter** — modelos `:free` de todas las familias (~50 peticiones/día).
  - **Alibaba Qwen** — Qwen **3.8-Max**, Qwen3-Plus, Qwen3-Coder, QwQ… Prueba
    gratis de **~1M tokens** al activar Model Studio (90 días, región Singapur).
  - **Mistral** — plan Experiment: ~1.000M tokens/mes (verificación por teléfono).
  - **Cerebras** — ~1M tokens/día gratis, sin tarjeta.
  - **Z.ai (GLM)** — GLM-4.5-Flash gratis de verdad (0 €/token).
  - **GitHub Models** — GPT-4.1-mini, o3-mini, Llama 4, DeepSeek-R1 gratis con tu cuenta de GitHub.
  - **SambaNova** — plan free (sin tarjeta): Llama y Qwen.
  - **Personalizado** — *cualquier* API compatible con OpenAI (LM Studio,
    vLLM, otros agregadores…): pones la URL base, los modelos y tu clave.
- 🔍 **Buscar en internet**: «busca en internet…» usa DuckDuckGo (sin clave).
- 🧠 **Memoria**: «recuerda que…» guarda apuntes en `data/memoria/` y los consulta.
- 🖥️ **Acceso a tu PC** (con confirmación):
  - 👀 **Leer archivos** — «mira qué hay en mi archivo notas.txt»
  - ✍️ **Escribir archivos** — «crea un archivo lista.txt con la compra»
  - 💻 **Ejecutar comandos** — «¿cuánto espacio libre hay en el disco?»
  - ⚠️ **Nada se ejecuta sin tu aprobación**: cada acción aparece en el chat
    con un botón Aprobar/Rechazar. Además, por defecto solo puede tocar tu
    carpeta de usuario y la del proyecto (añade carpetas extra en Ajustes → PC).

## Requisitos

- Python 3.10+ (Windows, Linux o macOS)
- Opcional: [Ollama](https://ollama.com) para modelos locales

## Instalación

**Linux / macOS**:

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
# python -m asistente.main
```

Abre **http://localhost:8000** en tu navegador.

## Primeros pasos

1. Ve a **Ajustes** y elige un proveedor:
   - **Alibaba Qwen**: crea cuenta en bailian.console.alibabacloud.com (región
     Singapur), activa Model Studio y genera una API key → prueba gratis ~1M tokens.
   - **Gemini**: https://aistudio.google.com/apikey · **Groq**: https://console.groq.com/keys
   - **Mistral**: https://console.mistral.ai · **Cerebras**: https://cloud.cerebras.ai
   - **Z.ai**: https://z.ai/console · **GitHub Models**: https://github.com/marketplace/models
   - **OpenRouter**: https://openrouter.ai/keys (modelos `:free`)
   - **Ollama** (local): instálalo, `ollama pull llama3.2` y elígelo.
2. Escribe en el chat. Prueba:
   - «busca en internet las noticias de hoy»
   - «recuerda que mi cumpleaños es el 3 de mayo»
   - «lee el archivo README.md y resúmelo»
   - «crea un script que me liste los archivos grandes de mi carpeta»

## Estructura

```
asistente/
  main.py        → servidor web local (FastAPI)
  agent.py       → orquesta conversación + herramientas (+ permisos)
  providers.py   → registro de 11 proveedores gratuitos
  pc.py          → acceso a archivos y terminal (con sandbox y permisos)
  tools.py       → búsqueda web, notas y herramientas de PC
  memory.py      → memoria persistente (data/memoria/)
  static/        → interfaz web (chat + ajustes + memoria)
data/            → tus datos locales (no se sube a git)
scripts/         → instalar.sh y arrancar.sh
```

## Notas honestas

- Los planes gratis cambian de límites con el tiempo; si un proveedor da error,
  revisa su web oficial o cambia a otro en el panel. Es la naturaleza de «gratis»:
  nada es eterno.
- Tu privacidad depende de dónde corra el modelo: Ollama es 100% local;
  los demás envían tu mensaje a sus servidores (plan gratis).
- Las claves se guardan en `data/config.json` con permisos restringidos.
- **Seguridad del acceso al PC**: el terminal puede ejecutar lo que le pidas.
  MiClaw siempre pide confirmación y limita las rutas, pero *tú* decides qué
  apruebas. Trátalo como a un asistente con acceso a tu teclado.
- **¿arena.ai?** Los modelos que se prueban en arena.ai (Llama, Qwen, GLM,
  DeepSeek…) son los mismos que ya puedes usar gratis por sus vías oficiales
  desde MiClaw. Arena no ofrece API pública, así que no la integramos por
  scraping: es frágil y va contra sus términos.

## Ideas para el futuro (fáciles de añadir)

- Conversaciones guardadas por sesión.
- Más herramientas: calculadora, recordatorios, voz, imágenes.
- Modo agente con varios pasos autónomos (con límites de seguridad).

# 🦞 MiClaw — tu asistente personal de IA, 100% gratis y en tu PC

Un asistente estilo **OpenClaw** pero tuyo: corre en tu ordenador, usa modelos de
IA **gratuitos** (locales o en la nube con plan free) y toda tu información
(conversaciones, claves, memoria) se queda en tu disco.

> **v1.0 — premium**: interfaz rediseñada, conversaciones guardadas, Markdown,
> máquina de escribir, botón «Probar conexión», exportar chats y más.

## ✨ Qué hace

### Chat y proveedores (todo gratis, sin tarjeta)
- **Ollama** — modelos 100% locales (sin internet, ilimitado).
- **Google Gemini** — plan gratis: ~15 peticiones/min, ~1.500/día.
- **Groq** — ultrarrápido (~30 peticiones/min).
- **OpenRouter** — modelos `:free` de todas las familias.
- **Alibaba Qwen** — Qwen **3.8-Max**, Qwen3-Plus, Coder, QwQ… prueba gratis de
  **~1M tokens** (90 días, región Singapur).
- **Mistral** — plan Experiment: ~1.000M tokens/mes (verificación por teléfono).
- **Cerebras** — ~1M tokens/día, sin tarjeta.
- **Z.ai (GLM)** — GLM-4.5-Flash gratis de verdad (0 €/token).
- **GitHub Models** — GPT-4.1-mini, o3-mini, Llama 4, DeepSeek-R1 gratis.
- **SambaNova** — plan free: Llama y Qwen.
- **Personalizado** — *cualquier* API compatible con OpenAI (LM Studio, vLLM…):
  pones la URL base, los modelos y tu clave.

### Herramientas
- 🔍 **Buscar en internet** — «busca en internet…» (DuckDuckGo, sin clave).
- 🧠 **Memoria** — «recuerda que…» guarda apuntes con fecha en `data/memoria/`.
- 🖥️ **Acceso a tu PC** (siempre con tu aprobación):
  - 👀 Leer archivos · ✍️ Escribir archivos · 💻 Ejecutar comandos
  - Cada acción muestra una tarjeta **Aprobar / Rechazar**; por defecto solo
    puede tocar tu carpeta de usuario y la del proyecto (ajustable).

### Experiencia premium
- 💾 **Conversaciones guardadas** — historial lateral con búsqueda, se retoma donde lo dejaste.
- 📝 **Markdown** — respuestas con formato (código con botón «Copiar», tablas, listas…).
- ⌨️ **Máquina de escribir** + indicador de pensamiento animado.
- ⚡ **Botón «Probar conexión»** por proveedor (verifica tu clave en 1 clic).
- ⬇️ **Exportar** cualquier conversación a Markdown.
- ↻ **Regenerar** respuestas · ⧉ copiar mensajes.
- 🎨 Diseño oscuro premium (glassmorphism + gradientes) y atajos (`Ctrl+N`, `Ctrl+,`).

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
# o: python -m asistente.main
```

Abre **http://localhost:8000**.

## Primeros pasos

1. **Ajustes → Proveedor**: elige uno y pega su clave (gratis, sin tarjeta):
   - **Alibaba Qwen**: bailian.console.alibabacloud.com (región Singapur) → activa Model Studio → API key.
   - **Gemini**: aistudio.google.com/apikey · **Groq**: console.groq.com/keys
   - **Mistral**: console.mistral.ai · **Cerebras**: cloud.cerebras.ai
   - **Z.ai**: z.ai/console · **GitHub**: github.com/marketplace/models
   - **OpenRouter**: openrouter.ai/keys (modelos `:free`)
   - **Ollama** (local): `ollama pull llama3.2`
2. Pulsa **⚡ Probar conexión** para confirmar que la clave funciona.
3. Chatea: «busca en internet…», «recuerda que…», «lee el archivo README.md», «crea un script…».

## Estructura

```
asistente/
  main.py            → servidor web local (FastAPI)
  agent.py           → orquesta conversación + herramientas (+ permisos)
  providers.py       → registro de 11 proveedores gratuitos
  pc.py              → acceso a archivos y terminal (sandbox + permisos)
  tools.py           → búsqueda web, notas y herramientas de PC
  memory.py          → memoria persistente (data/memoria/)
  conversaciones.py  → historial persistente (data/conversaciones/)
  static/            → interfaz premium (HTML/CSS/JS)
data/                → tus datos locales (no se sube a git)
scripts/             → instalar.sh y arrancar.sh
```

## Notas honestas

- Los planes gratis cambian con el tiempo: si un proveedor da error, revisa su
  web o cambia a otro en un clic. Es la naturaleza de «gratis».
- Ollama es 100% local; los demás envían tu mensaje a sus servidores (plan gratis).
- Claves en `data/config.json` con permisos restringidos.
- **Seguridad del acceso al PC**: el terminal ejecuta solo lo que *tú* apruebas.
- **¿arena.ai?** No tiene API pública: los modelos que prueba (Llama, Qwen, GLM,
  DeepSeek…) son los mismos que ya usas gratis por sus vías oficiales desde MiClaw.

## Ideas para el futuro

- Voz (texto → habla y dictado), imágenes, más herramientas (recordatorios).
- Modo agente con varios pasos autónomos (con límites de seguridad).
- Streaming real de las respuestas.

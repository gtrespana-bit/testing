# 🦞 MiClaw — tu asistente personal de IA, 100% gratis y en tu PC

Un asistente estilo **OpenClaw** pero tuyo: corre en tu ordenador, usa modelos de
IA **gratuitos** (locales o en la nube con plan free) y toda tu información
(conversaciones, claves, memoria) se queda en tu disco.

> **v1.5**: auto-aprobación opcional (ejecuta comandos y herramientas sin
> confirmar cada uno), modo rápido para Qwen (sin cadena de pensamiento),
> y acceso multi-dispositivo con PIN.
>
> 📘 **Documentación completa para retomar el proyecto (y hacer el PR):**
> [docs/ESTADO-DEL-PROYECTO.md](docs/ESTADO-DEL-PROYECTO.md)

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
- 🧠 **RAG de código** — indexa una carpeta de proyectos (Ajustes → Base de
  conocimiento) y responde sobre TU código: «¿dónde está la función que valida
  emails?», «¿qué hace esta clase?». 100% local.
- 🐞 **Bucle de depuración** — ejecuta un script (.py/.js/.sh/.bat), ve el
  traceback, corrige el archivo y vuelve a probar: «arregla mi script» (cada
  paso con tu aprobación).
- 📊 **Informes** — «guarda un informe de esto» → archivo Markdown en
  data/informes/, visible y consultable en Memoria → Informes.
- 🔍 **Buscar en internet** — «busca en internet…» (DuckDuckGo, sin clave).
- 🧠 **Memoria** — «recuerda que…» guarda apuntes con fecha en `data/memoria/`.
- 🧮 **Calculadora** — «calcula 25*4+10», raíces, trigonometría… (segura, sin eval).
- ⏰ **Recordatorios** — «recuérdame llamar a Ana mañana a las 9» → aviso con
  notificación en el navegador.
- 🌤️ **Clima** — «¿qué tiempo hace en Valencia?» (wttr.in, gratis y sin clave).
- 🖥️ **Acceso a tu PC** (siempre con tu aprobación):
  - 👀 Leer archivos · ✍️ Escribir archivos · 💻 Ejecutar comandos
  - 📁 Listar carpetas · 🔍 Buscar texto en archivos (grep) · 📄 Leer PDF/Word/Excel
  - 📦 **Acciones en lote**: varias acciones propuestas a la vez, apruebas las que quieras
  - Cada acción muestra una tarjeta **Aprobar / Rechazar**; por defecto solo
    puede tocar tu carpeta de usuario y la del proyecto (ajustable).
  - 🚀 **Auto-aprobación opcional** (Ajustes → Acceso a tu PC): si la activas,
    MiClaw ejecuta comandos, escribe archivos y usa herramientas **sin pedir
    confirmación cada vez** — ideal para programar sin interrupciones.
- ⚡ **Modo rápido**: con modelos Qwen (Alibaba) puedes desactivar la cadena de
  pensamiento (Ajustes → Preferencias) para que responda mucho antes.

### Experiencia premium
- 👁️ **Visión** — adjunta imágenes o archivos al chat (📎 o arrastrando):
  MiClaw los ve (Gemini/Qwen-VL/Ollama multimodal) o lee su texto.
- 🖥️ **Captura de pantalla** — «mira mi pantalla»: MiClaw la captura (con tu
  aprobación) y la analiza con un modelo con visión.
- 📊 **Diff visual** — antes de modificar un archivo existente, te muestra los
  cambios en verde/rojo para que apruebes con conocimiento.
- 🔐 **Multi-dispositivo con PIN** — abre MiClaw desde tu móvil en la misma red
  WiFi (`http://IP:8000`, la IP se muestra en Ajustes) y protégelo con un PIN
  opcional (guardado con hash, token de 7 días).
- 🤖 **Tareas autónomas** — programa acciones que MiClaw ejecuta SOLO a la hora
  indicada («programa una tarea para mañana a las 9 que busque las noticias»).
  Resultados visibles en Memoria → Tareas, con notificación.
- ⌘ **Paleta de comandos** — `Ctrl+K`: nueva conversación, cambiar proveedor,
  tema, exportar, probar conexión… desde un solo buscador.
- 📡 **HUD de telemetría** — barra superior con estado del núcleo y, tras cada
  respuesta, tiempo de síntesis y tokens estimados.
- 🧬 **Red neuronal animada** de fondo + pantalla de arranque estilo IA despertando.
- ⚡ **Streaming real** — las respuestas aparecen palabra a palabra, en vivo.
- 🎤 **Voz** — lee respuestas en voz alta (🔊, auto-read, velocidad) y dictado 🎤.
- ☀️🌙 **Modo claro y oscuro** con un clic.
- 💾 **Conversaciones guardadas** con historial lateral y búsqueda.
- 📝 **Markdown** con bloques de código copiables, tablas y listas.
- ⚡ **Botón «Probar conexión»** · ⬇️ exportar · ↻ regenerar · atajos (`Ctrl+N`, `Ctrl+,`, `Ctrl+K`).

## Requisitos

- Python 3.10+ (Windows, Linux o macOS)
- Opcional: [Ollama](https://ollama.com) para modelos locales

## Instalación

**Linux / macOS**:

```bash
scripts/instalar.sh
```

**Windows** (doble clic, sin comandos):

1. Doble clic en **`INSTALAR.bat`** (solo la primera vez).
2. Doble clic en **`ARRANCAR.bat`**. Se abre el navegador en http://localhost:8000.

Si Windows avisa «Windows protegió tu PC», pulsa *Más información* → *Ejecutar de todas formas*.

> Si al instalar veías el error `"cho."` / `"ho" no se reconoce como un comando`:
> era un fallo de los `.bat` (finales de línea Unix). Ya está corregido;
> vuelve a descargar/actualizar el proyecto y haz doble clic en `INSTALAR.bat`.

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
scripts/             → instalar.sh / arrancar.sh (Linux/macOS)
                     → instalar.bat / arrancar.bat (Windows)
INSTALAR.bat         → doble clic en Windows (primera vez)
ARRANCAR.bat         → doble clic en Windows (abre el navegador)
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

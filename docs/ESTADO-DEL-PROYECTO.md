# 📘 MiClaw — Estado del proyecto y guía de retoma

> **LEE ESTE ARCHIVO PRIMERO.** Este documento existe para que cualquier
> persona (o agente de IA) pueda retomar el proyecto en minutos: qué es,
> qué está hecho, cómo funciona, cómo se prueba y cómo se hace el PR.

---

## 1. Resumen ejecutivo

**MiClaw** es un asistente personal de IA estilo OpenClaw, 100% gratuito y
local, que corre en el ordenador del usuario:

- **Web app local** (Python FastAPI + frontend HTML/CSS/JS puro, sin build).
- **11 proveedores gratuitos** de modelos (nube con plan free + Ollama local).
- **Herramientas**: búsqueda web, memoria, calculadora, recordatorios, clima,
  acceso al PC (archivos + terminal con aprobación), RAG de código, depuración
  de scripts, informes, captura de pantalla con visión, tareas autónomas.
- **UX premium**: streaming real, voz (leer/dictar), tema claro/oscuro,
  conversaciones guardadas, Markdown, paleta de comandos (Ctrl+K), HUD de
  telemetría, pantalla de arranque futurista, red neuronal animada de fondo,
  multi-dispositivo con PIN.

**Versión actual: 1.4.0** — todo commiteado y empujado al branch
`arena/01a05486-testing` (ver §9 para el PR).

---

## 2. Cómo ponerte al día en 3 minutos

```bash
cd testing                # raíz del repo (este checkout)
git log --oneline -12     # historial de todo lo construido
scripts/arrancar.sh       # o: python -m asistente.main  → http://localhost:8000
```

Luego abre http://localhost:8000: verás la pantalla de arranque, el chat con
sugerencias, Ajustes (proveedores/claves/modos/RAG/PIN) y Memoria
(apuntes/recordatorios/tareas/informes). Sin claves API configuradas, el chat
devuelve errores legibles («Falta la clave de X»); el botón ⚡ Probar conexión
de Ajustes verifica una clave real.

---

## 3. Mapa del repositorio

```
testing/
├── README.md                        → doc de producto (funcionalidades, instalación)
├── docs/ESTADO-DEL-PROYECTO.md      → ESTE documento (guía de retoma y PR)
├── requirements.txt                 → deps: fastapi, uvicorn, httpx, ddgs,
│                                       pypdf, python-docx, openpyxl, Pillow
├── .gitignore                       → data/ (datos locales) y artefactos Python
├── scripts/
│   ├── instalar.sh / arrancar.sh    → Linux/macOS (crea .venv, arranca)
│   └── instalar.bat / arrancar.bat  → Windows (CRLF; doble clic)
├── INSTALAR.bat / ARRANCAR.bat      → atajos en la raíz para Windows
└── asistente/
    ├── main.py          → servidor FastAPI: endpoints, middleware PIN, hilo de tareas
    ├── agent.py         → orquesta conversación + herramientas + permisos + streaming
    ├── providers.py     → 11 proveedores gratis + builders de visión + streaming
    ├── config.py        → config.json (claves, modelo, modo, PIN, custom)
    ├── tools.py         → registro de herramientas + ejecutores (web, nota, calc, …)
    ├── pc.py            → acceso al PC: archivos, terminal, grep, docs, diff, captura
    ├── memory.py        → memoria/apuntes persistente (data/memoria/)
    ├── conversaciones.py→ chats guardados (data/conversaciones/)
    ├── recordatorios.py → avisos con parser de fechas en español
    ├── tareas.py        → tareas autónomas (+ recurrentes: "cada día a las 9")
    ├── rag.py           → índice de código local (preguntas sobre tu proyecto)
    ├── informes.py      → informes Markdown (data/informes/)
    └── static/
        ├── index.html   → interfaz (chat, ajustes, memoria, lock, paleta, modal)
        ├── styles.css   → tema oscuro/claro premium + futurista
        └── app.js       → todo el frontend (streaming, voz, temas, RAG, PIN…)
```

**Datos locales** (NO se suben a git, creados en tiempo de ejecución):
`data/config.json` (claves y ajustes), `data/conversaciones/`, `data/memoria/`,
`data/recordatorios.json`, `data/tareas.json`, `data/informes/`,
`data/capturas/`, `data/rag_index.json`.

---

## 4. Funcionalidades implementadas (por versión)

| Versión | Qué añadió |
|---|---|
| **v0.1** | Base: chat con Gemini/Groq/OpenRouter/Ollama, búsqueda web (DuckDuckGo), memoria, frontend básico |
| **v0.2** | +8 proveedores (Alibaba Qwen 3.8-Max, Mistral, Cerebras, Z.ai, GitHub Models, SambaNova, personalizado OpenAI-compatible) y **acceso al PC** con aprobación (leer/escribir/terminal) |
| **v1.0** | Conversaciones guardadas, Markdown, máquina de escribir, botón Probar conexión, exportar, diseño premium |
| **v1.1** | Streaming real (SSE/NDJSON), voz (leer + dictado), modo claro/oscuro, calculadora, recordatorios, clima |
| **v1.2** | Visión (adjuntar imágenes/archivos), tareas autónomas, paleta de comandos (Ctrl+K), HUD de telemetría, red neuronal de fondo, boot futurista, instaladores Windows |
| **v1.3** | Modos de trabajo (General/Programador/Investigador/Escritor), acciones en lote (casillas), grep/listar carpetas, leer PDF/Word/Excel, tareas recurrentes |
| **v1.4** | **Diff visual** antes de modificar archivos, **captura de pantalla** con visión, **multi-dispositivo con PIN**, doc de retoma (este archivo) |

### Detalle de capacidades actuales

**Chat / modelos:** 11 proveedores todos gratis; el proveedor **Personalizado**
acepta CUALQUIER API compatible con OpenAI (URL base + modelos + clave) sin tocar
código. Modelos recomendados para programar: Qwen3-Coder-Plus (Alibaba), GPT-OSS
120B (Groq), Codestral (Mistral), DeepSeek V3 (`:free` OpenRouter).

**Herramientas (el agente las elige solo):**
- Automáticas (`@@TOOL:id@@`): web (DuckDuckGo), nota (memoria), calc
  (segura, sin eval), recordatorio, tarea, clima (wttr.in), codigo (RAG),
  informe (Markdown), apuntes.
- Con permiso (`@@PC:accion@@`): ver, escribir, terminal, listar, buscar (grep),
  documento (PDF/Word/Excel), depurar (ejecuta script y captura traceback),
  captura (pantalla → visión). **Todas piden Aprobación/Rechazo en el chat** y
  pueden venir en **lote** (varias acciones con casillas).
- Sandbox de rutas: solo tu carpeta de usuario + la del proyecto (+ carpeta
  extra configurable en Ajustes).

**Seguridad:** cada acción sobre el PC se aprueba manualmente; las tareas
automáticas corren con `no_pc=True` (prohibido tocar el PC); claves y PIN
guardados solo en local (PIN con hash); **PIN opcional** que bloquea toda la
API para accesos desde otros dispositivos (el token se guarda en localStorage
del navegador, expira a los 7 días).

**Streaming:** `/api/chat` devuelve NDJSON de eventos:
`{"tipo":"token"|"tool"|"permiso"|"error"|"done", ...}`. `done` incluye
`segundos` y `tokens` (telemetría). Las herramientas se resuelven dentro del
mismo stream (el agente ejecuta y continúa hasta `max_tool_rounds=5`).

**Visión:** los mensajes pueden llevar `{"role":"user","content":...,"imagen":"data:image/..."}`;
los builders de providers (`_build_openai_messages`, `_build_gemini_contents`,
`_build_ollama_messages`) lo convierten al formato nativo de cada API.

**Modos:** la persona del sistema cambia según el modo elegido (programador →
ingeniero senior que usa herramientas para entender/corregir código).

---

## 5. Arquitectura y flujo de una conversación

1. El usuario escribe en el chat → el frontend envía `{messages, tool_result?}`
   a `POST /api/chat` (streaming NDJSON).
2. `agent.responder_stream()` construye el system prompt
   (`_build_system_prompt()`: persona del modo + fecha de hoy + lista de
   herramientas con formato exacto + memoria) y llama a `providers.stream_chat`.
3. Si el modelo devuelve un token de herramienta:
   - `@@TOOL:...@@` → `tools.ejecutar()` (automática) y se continúa otra ronda.
   - `@@PC:...@@` → evento `permiso`; el frontend muestra la tarjeta
     Aprobar/Rechazar (con **diff** si es `escribir`); al aprobar ejecuta
     `POST /api/pc/ejecutar` y reenvía con `tool_result` (mensaje `tool`).
   - `lote` → varias `@@PC:...@@` en un mensaje → tarjeta con casillas.
4. La respuesta final llega como `done` y se guarda en la conversación.

**Trampas conocidas al editar:**
- `SYSTEM_PROMPT` usa `.format()` → las llaves literales del prompt deben
  escaparse como `{{ }}` (p. ej. `{{qué recordar}}`).
- Las herramientas se registran en `tools.TOOLS` Y en el texto de `REGLAS DE USO`
  del prompt; si añades una, hay que tocar ambos + `tools.ejecutar()`.
- Los tokens de herramienta se detectan por regex en `agent._extraer_tool()` y
  `pc.parsear()`; los formatos exactos están en `tools.TOOLS[].formato`.
- `data/` está gitignored: nunca commitees claves ni datos locales.
- Para arrancar: `python -m asistente.main` (no `python asistente/main.py`,
  fallan los imports relativos).

---

## 6. Cómo probar (y qué NO se puede probar aquí)

**Entorno actual (sandbox):** el servidor corre en el puerto 8000 (0.0.0.0) y la
UI se ve en el preview. **El sandbox NO tiene salida a las APIs de IA ni a
DuckDuckGo** (bloqueo de red), por lo que las llamadas reales a modelos no
pueden verificarse aquí; sí se prueban con modelos simulados
(monkeypatching `providers.stream_chat`) y con TestClient.

**Lo que SÍ se ha probado y verificado:**
- CRUD de conversaciones, memoria, recordatorios (parser de fechas), tareas
  (incluidas recurrentes), informes, RAG (indexar + buscar), depuración de
  scripts (traceback real), diff, PIN (401→token→200), `/api/red`, visión
  (builders + flujo `@@IMAGEN@@`), lote de acciones, streaming de eventos
  (tool→token→done), errores legibles sin clave, sintaxis JS (`node --check`).
- La captura de pantalla **falla en el sandbox** (headless, sin X): devuelve un
  mensaje elegante; en el PC del usuario con escritorio funciona (Pillow
  `ImageGrab`).

**Prueba manual rápida en un PC real:** poner una clave gratis (Gemini en
aistudio.google.com/apikey, o Alibaba Qwen), Ajustes → ⚡ Probar conexión, y
probar: «busca en internet…», «recuerda que…», «crea un script y ejecútalo»,
«arregla mi script» (depurar), Ajustes → RAG → Indexar → «¿dónde está la
función X?», activar PIN → abrir `http://IP-del-PC:8000` desde el móvil.

---

## 7. Trabajo pendiente / ideas futuras (no implementadas)

- **Modo agente multi-paso autónomo** con límites (encadenar muchas herramientas sin confirmar cada una, con tope).
- **Búsqueda de imágenes en la web** (herramienta que devuelva imágenes).
- **Correo electrónico** (Gmail OAuth) e integraciones de calendario.
- **Streaming con indicador de herramienta en curso** ya existe; falta *streaming
  del razonamiento* (p. ej. tokens de pensamiento de QwQ/DeepSeek-R1).
- **Multi-sesión de PIN** (varios dispositivos con tokens distintos visibles).
- **Docker / instalador único** para distribuir a otras personas.
- **Pruebas automatizadas** (pytest) de los módulos: hoy son smoke-tests manuales.
- **Base de datos SQLite** en vez de JSON por carpeta (si crecen los datos).

---

## 8. Convenciones del repositorio

- **Idioma**: todo el producto y los mensajes en español; código y commits en
  español también (se ha hecho así hasta ahora).
- **Branch de trabajo**: `arena/01a05486-testing` (único branch donde se
  commitea y empuja; NUNCA crear otros).
- **Commits**: mensajes en español, resumen de qué añade cada versión
  (ver `git log`).
- **Dependencias**: se añaden a `requirements.txt` y se instalan en `.venv`.
- **Frontend**: JS plano (sin frameworks), CSS plano, sin build step.
- **Seguridad**: ninguna acción de PC sin aprobación; PIN opcional; claves solo
  en `data/config.json` (gitignored).

---

## 9. Cómo hacer el Pull Request (próximo paso)

Estado actual: todo commiteado y empujado a `origin/arena/01a05486-testing`.
La rama `main` sigue en el commit original (6f13f53, la página estática vieja).

```bash
cd testing
git status                          # debe estar limpio (solo data/ ignorada)
git log --oneline origin/arena/01a05486-testing..origin/main   # lo que queda por integrar
git push origin arena/01a05486-testing   # ya empujado; por si acaso

# Opción A — con GitHub CLI:
gh pr create --base main --head arena/01a05486-testing \
  --title "MiClaw: asistente personal de IA gratis y local (v1.4)" \
  --body "Asistente estilo OpenClaw, 100% gratuito... (resumen de funcionalidades)"

# Opción B — web:
# https://github.com/gtrespana-bit/testing/pull/new/arena/01a05486-testing
```

Antes del PR conviene: revisar que `README.md` y este doc están actualizados,
borrar `data/` local si existe (está gitignored de todos modos), y quizá
añadir una captura de la UI al cuerpo del PR.

---

## 10. Contacto con el usuario (contexto)

- El usuario es hispanohablante (España/Venezuela), no técnico, y quiere un
  asistente **gratis** («no quiero gastar nada de dinero»), que use modelos
  capaces (Qwen 3.8-Max, etc.), con acceso a su PC y a internet.
- Prefiere que las cosas sean «fáciles, sin enredos» y le gusta que el
  producto se sienta premium/futurista.
- Ha ido pidiendo iterativamente: proveedores gratis → acceso PC → premium →
  «superfunciones» → compañero de programación → nivel actual (diff, captura,
  multi-dispositivo) + documentación para el PR.
- El próximo chat hará el PR (sección 9) y probablemente seguirá añadiendo
  funciones o puliendo.

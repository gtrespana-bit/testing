/* ============================================================
   MiClaw — frontend v1.2 (modo superinteligencia)
   ============================================================ */
"use strict";

const $ = (id) => document.getElementById(id);

let estado = null;
let historial = [];
let chatId = null;          // id de la conversación actual (null = nueva sin guardar)
let pendiente = null;       // plan de acción sobre el PC esperando aprobación
let ocupado = false;        // hay una petición en curso
let adjuntosPendientes = []; // adjuntos del mensaje en curso
let tareasVistas = new Set(); // ids de tareas ya notificadas
let token = localStorage.getItem("miclaw-token") || "";  // token de acceso (PIN)
let lockVisible = false;

/* ---------------- utilidades ---------------- */

function headersExtra() {
  const h = { "Content-Type": "application/json" };
  if (token) h["X-Miclaw-Token"] = token;
  return h;
}

function mostrarLock() {
  if (lockVisible) return;
  lockVisible = true;
  const lock = $("lock");
  lock.classList.remove("hidden");
  setTimeout(() => $("lock-pin")?.focus(), 50);
}

function ocultarLock() {
  lockVisible = false;
  $("lock").classList.add("hidden");
}

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: headersExtra(), ...opts });
  if (res.status === 401) { mostrarLock(); throw new Error("PIN requerido"); }
  return res.json();
}

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 3400);
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = String(s ?? "");
  return d.innerHTML;
}

function ahora() {
  return new Date().toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
}

function fechaRelativa(iso) {
  if (!iso) return "";
  const d = new Date(iso.replace(" ", "T"));
  const hoy = new Date();
  const ayer = new Date(hoy.getTime() - 864e5);
  if (d.toDateString() === hoy.toDateString())
    return "hoy " + d.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
  if (d.toDateString() === ayer.toDateString()) return "ayer";
  return d.toLocaleDateString("es", { day: "numeric", month: "short" });
}

function scrollBottom() {
  const m = $("messages");
  m.scrollTop = m.scrollHeight;
}

let _ultimoScroll = 0;
function scrollThrottled() {
  const t = Date.now();
  if (t - _ultimoScroll > 80) { _ultimoScroll = t; scrollBottom(); }
}

/* ---------------- PANTALLA DE ARRANQUE ---------------- */

function arrancarBoot() {
  const boot = $("boot");
  if (!boot) return;
  const logs = [
    ["Inicializando núcleo neuronal…", ""],
    ["Cargando matrices de proveedores…", ""],
    ["[OK] 11 proveedores gratuitos detectados", "ok"],
    ["Sincronizando memoria local…", ""],
    "[OK] Cifrado local activado",
    ["Conectando herramientas: web · PC · clima · tareas…", ""],
    ["[OK] Sistema operativo MiClaw listo", "ok"],
  ];
  const fill = $("boot-fill");
  const cont = $("boot-logs");
  let i = 0;
  const paso = () => {
    if (i >= logs.length) {
      setTimeout(() => boot.classList.add("off"), 380);
      setTimeout(() => boot.remove(), 950);
      return;
    }
    const [txt, cls] = logs[i];
    const div = document.createElement("div");
    if (cls) div.className = cls;
    div.textContent = txt;
    cont.appendChild(div);
    fill.style.width = (((i + 1) / logs.length) * 100) + "%";
    i++;
    setTimeout(paso, 250);
  };
  boot.onclick = () => { boot.classList.add("off"); setTimeout(() => boot.remove(), 400); };
  paso();
}

/* ---------------- RED NEURONAL DE FONDO ---------------- */

function iniciarRedNeuronal() {
  const canvas = $("neural");
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  let W, H;
  const N = 48;
  const nodos = [];
  const resize = () => { W = canvas.width = innerWidth; H = canvas.height = innerHeight; };
  resize();
  addEventListener("resize", resize);
  for (let i = 0; i < N; i++) {
    nodos.push({
      x: Math.random() * innerWidth, y: Math.random() * innerHeight,
      vx: (Math.random() - .5) * .38, vy: (Math.random() - .5) * .38,
      r: Math.random() * 1.7 + .7,
    });
  }
  let last = performance.now();
  const frame = (now) => {
    const dt = Math.min((now - last) / 16.7, 3);
    last = now;
    ctx.clearRect(0, 0, W, H);
    for (const n of nodos) {
      n.x += n.vx * dt; n.y += n.vy * dt;
      if (n.x < 0 || n.x > W) n.vx *= -1;
      if (n.y < 0 || n.y > H) n.vy *= -1;
    }
    for (let i = 0; i < nodos.length; i++) {
      for (let j = i + 1; j < nodos.length; j++) {
        const a = nodos[i], b = nodos[j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 135) {
          ctx.strokeStyle = "rgba(124,92,255," + (0.15 * (1 - d / 135)).toFixed(3) + ")";
          ctx.lineWidth = .6;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        }
      }
    }
    ctx.fillStyle = "rgba(124,92,255,.5)";
    for (const n of nodos) { ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2); ctx.fill(); }
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}

/* ---------------- markdown (renderizador ligero y seguro) ---------------- */

function mdInline(s) {
  let t = esc(s);
  t = t.replace(/`([^`\n]+)`/g, "<code>$1</code>");
  t = t.replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  t = t.replace(/~~([^~\n]+)~~/g, "<del>$1</del>");
  t = t.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  return t;
}

function mdCodeBlock(lang, code) {
  const id = "cb" + Math.random().toString(36).slice(2, 9);
  return `<div class="codeblock"><div class="codehead"><span>${esc(lang || "código")}</span>` +
    `<button class="copy-btn" data-cb="${id}">⧉ Copiar</button></div>` +
    `<pre id="${id}"><code>${esc(code)}</code></pre></div>`;
}

function mdTable(rows) {
  const parse = (r) => r.trim().replace(/^\||\|$/g, "").split("|").map((c) => mdInline(c.trim()));
  const header = parse(rows[0]);
  const sep = /^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$/;
  const body = rows.slice(1).filter((r) => !sep.test(r));
  let h = "<table><thead><tr>" + header.map((c) => `<th>${c}</th>`).join("") + "</tr></thead>";
  if (body.length) h += "<tbody>" + body.map((r) => "<tr>" + parse(r).map((c) => `<td>${c}</td>`).join("") + "</tr>").join("") + "</tbody>";
  return h + "</table>";
}

function renderMarkdown(src) {
  const lines = String(src || "").replace(/\r\n/g, "\n").split("\n");
  let html = "", i = 0;
  let inCode = false, codeLang = "", codeBuf = [];
  let listTag = null;
  const flushList = () => { if (listTag) { html += `</${listTag}>`; listTag = null; } };

  while (i < lines.length) {
    const line = lines[i];
    const fence = line.match(/^```(\w*)\s*$/);
    if (fence) {
      flushList();
      if (inCode) { html += mdCodeBlock(codeLang, codeBuf.join("\n")); inCode = false; codeLang = ""; codeBuf = []; }
      else { inCode = true; codeLang = fence[1] || ""; }
      i++; continue;
    }
    if (inCode) { codeBuf.push(line); i++; continue; }

    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) { flushList(); html += `<h${h[1].length}>${mdInline(h[2])}</h${h[1].length}>`; i++; continue; }

    if (/^\s*(---|\*\*\*+)\s*$/.test(line)) { flushList(); html += "<hr>"; i++; continue; }

    if (line.trim().startsWith("|")) {
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) { rows.push(lines[i]); i++; }
      flushList();
      html += mdTable(rows);
      continue;
    }

    const ul = line.match(/^\s*[-*+]\s+(.*)$/);
    const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (ul || ol) {
      const tag = ul ? "ul" : "ol";
      if (listTag !== tag) { flushList(); html += `<${tag}>`; listTag = tag; }
      html += `<li>${mdInline((ul || ol)[1])}</li>`;
      i++; continue;
    }
    flushList();

    const bq = line.match(/^>\s?(.*)$/);
    if (bq) { html += `<blockquote>${mdInline(bq[1])}</blockquote>`; i++; continue; }

    if (!line.trim()) { i++; continue; }
    html += `<p>${mdInline(line)}</p>`;
    i++;
  }
  if (inCode) html += mdCodeBlock(codeLang, codeBuf.join("\n"));
  flushList();
  return `<div class="md">${html}</div>`;
}

/* ---------------- mensajes ---------------- */

function addMsg(role, texto) {
  const cont = $("messages");
  const row = document.createElement("div");
  row.className = "msg-row " + (role === "user" ? "user" : role === "error" ? "assistant error" : role);
  const avatar = role === "user" ? "👤" : role === "toolnote" ? "📎" : "🦞";
  row.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-body">
      <div class="msg-bubble">${esc(texto)}</div>
      <div class="msg-time">${ahora()}</div>
    </div>`;
  cont.appendChild(row);
  scrollBottom();
  return row;
}

function addMarkdown(role, texto) {
  const cont = $("messages");
  const row = document.createElement("div");
  row.className = "msg-row " + role;
  const avatar = role === "user" ? "👤" : "🦞";
  const acciones = role === "assistant"
    ? `<div class="msg-actions">
        <button class="msg-act" data-act="copy">⧉ Copiar</button>
        <button class="msg-act" data-act="regen">↻ Regenerar</button>
        <button class="msg-act" data-act="speak">🔊 Leer</button>
      </div>`
    : "";
  row.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-body">
      <div class="msg-bubble md"></div>
      <div class="msg-time">${ahora()}</div>
      ${acciones}
    </div>`;
  row.querySelector(".msg-bubble").innerHTML = renderMarkdown(texto);
  cont.appendChild(row);
  scrollBottom();
  return row;
}

function crearFilaStream(resumen) {
  const cont = $("messages");
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `
    <div class="msg-avatar">🦞</div>
    <div class="msg-body">
      ${resumen || ""}
      <div class="msg-bubble"></div>
    </div>`;
  cont.appendChild(row);
  scrollBottom();
  return { row, bubble: row.querySelector(".msg-bubble") };
}

/* Panel de actividad: muestra EN VIVO qué está haciendo MiClaw mientras piensa
   (pasos, herramientas en ejecución y, si el modelo lo envía, su razonamiento). */
function crearPanelActividad() {
  const cont = $("messages");
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `
    <div class="msg-avatar">🦞</div>
    <div class="msg-body">
      <div class="actividad">
        <div class="act-cab">
          <span class="act-spinner"></span>
          <span class="act-titulo">Trabajando…</span>
          <span class="act-tiempo">0.0s</span>
        </div>
        <div class="act-pasos"></div>
        <div class="act-razon hidden">
          <button class="act-razon-toggle">💭 Lo que piensa ▾</button>
          <div class="act-razon-cuerpo"></div>
        </div>
      </div>
    </div>`;
  cont.appendChild(row);
  scrollBottom();

  const pasosEl = row.querySelector(".act-pasos");
  const tiempoEl = row.querySelector(".act-tiempo");
  const razonWrap = row.querySelector(".act-razon");
  const razonCuerpo = row.querySelector(".act-razon-cuerpo");
  const razonToggle = row.querySelector(".act-razon-toggle");

  const t0 = Date.now();
  const timer = setInterval(() => {
    tiempoEl.textContent = ((Date.now() - t0) / 1000).toFixed(1) + "s";
  }, 100);

  const pasos = [];

  function renderPaso(p, texto) {
    p.el.className = "act-paso " + p.estado;
    p.el.querySelector(".act-paso-texto").textContent = texto;
    p.el.querySelector(".act-paso-detalle").textContent = p.detalle || "";
  }

  function addPaso(id, texto, estado, detalle) {
    const el = document.createElement("div");
    el.className = "act-paso " + (estado || "activo");
    el.innerHTML = `
      <span class="act-paso-icon"></span>
      <div class="act-paso-cuerpo">
        <div class="act-paso-texto"></div>
        <div class="act-paso-detalle"></div>
      </div>`;
    pasosEl.appendChild(el);
    const p = { id, el, estado: estado || "activo", texto: texto || "", detalle: detalle || "" };
    pasos.push(p);
    renderPaso(p, p.texto);
    scrollThrottled();
    return p;
  }

  function setPaso(id, estado, texto, detalle) {
    let p = pasos.find((x) => x.id === id);
    if (!p) p = addPaso(id, texto || id, estado, detalle);
    else {
      if (estado) p.estado = estado;
      if (detalle !== undefined) p.detalle = detalle;
      p.texto = texto || p.texto;
      renderPaso(p, p.texto);
    }
    scrollThrottled();
    return p;
  }

  razonToggle.onclick = () => {
    const abierta = razonWrap.classList.toggle("abierto");
    razonToggle.textContent = abierta ? "💭 Lo que piensa ▾" : "💭 Lo que piensa ▸";
  };

  function pensamiento(texto) {
    razonWrap.classList.remove("hidden");
    if (!razonWrap.classList.contains("abierto")) razonWrap.classList.add("abierto");
    razonToggle.textContent = "💭 Lo que piensa ▾";
    razonCuerpo.textContent += texto;
    scrollThrottled();
  }

  function finalizar() {
    clearInterval(timer);
    const seg = ((Date.now() - t0) / 1000).toFixed(1);
    const relevantes = pasos.filter((p) => p.id !== "inicio");
    const razon = razonCuerpo.textContent.trim();
    if (!relevantes.length && !razon) { row.remove(); return ""; }
    const pasosHtml = relevantes.map((p) =>
      `<div class="act-resumen-paso">${esc(p.texto)}${p.detalle ? `<span class="act-resumen-detalle">${esc(p.detalle)}</span>` : ""}</div>`
    ).join("");
    const html = `
      <details class="act-resumen"${razon ? " open" : ""}>
        <summary>⚙️ Cómo lo hice · ${seg}s</summary>
        <div class="act-resumen-body">
          ${pasosHtml}
          ${razon ? `<div class="act-resumen-razon">${esc(razon)}</div>` : ""}
        </div>
      </details>`;
    row.remove();
    return html;
  }

  function quitar() {
    clearInterval(timer);
    row.remove();
  }

  return { row, addPaso, setPaso, pensamiento, finalizar, quitar };
}

const TITULOS_PERMISO = {
  ver: "👀 Leer archivo", escribir: "✍️ Escribir archivo",
  terminal: "💻 Ejecutar comando", apuntes: "🧠 Leer apuntes",
  listar: "📁 Listar carpeta", buscar: "🔍 Buscar en archivos",
  documento: "📄 Leer documento", depurar: "🐞 Depurar script",
  captura: "🖥️ Capturar pantalla",
  lote: "📦 Plan de acción múltiple",
};

const ICONO_TOOL = {
  web: "🔍", nota: "📝", calc: "🧮", recordatorio: "⏰", tarea: "🤖",
  clima: "🌤️", codigo: "🧠", informe: "📊", apuntes: "🧠",
  ver: "👀", escribir: "✍️", terminal: "💻", listar: "📁",
  buscar: "🔍", documento: "📄", depurar: "🐞", captura: "🖥️",
};

function detallePermiso(accion, datos) {
  if (accion === "ver") return String(datos || "");
  if (accion === "terminal") return "COMANDO: " + String(datos || "");
  if (accion === "listar") return "RUTA: " + String(datos || "");
  if (accion === "documento") return "RUTA: " + String(datos || "");
  if (accion === "buscar" && datos) return "RUTA: " + (datos.ruta || "") + "\nTEXTO: " + (datos.texto || "");
  if (accion === "depurar" && datos) return "RUTA: " + (datos.ruta || "") + (datos.arg ? "\nARG: " + datos.arg : "");
  if (accion === "escribir" && datos && datos.ruta) {
    return "RUTA: " + datos.ruta + "\n\n" + String(datos.contenido || "").slice(0, 500);
  }
  if (accion === "apuntes") return "Mostrar los apuntes guardados";
  if (accion === "captura") return "Captura de pantalla del escritorio";
  return "(sin datos)";
}

/* Muestra el diff (verde/rojo) antes de aprobar una escritura sobre un archivo existente */
async function cargarDiff(ruta, contenido, pre) {
  try {
    const r = await api("/api/pc/diff", {
      method: "POST",
      body: JSON.stringify({ ruta, contenido }),
    });
    if (!r.diff) return;
    if (r.diff === "(archivo nuevo)") { pre.textContent = "📄 Archivo nuevo"; return; }
    pre.classList.add("diff");
    pre.innerHTML = r.diff.split("\n").map((l) => {
      const c = l[0];
      const cls = c === "+" ? "add" : c === "-" ? "del" : c === "@" ? "meta" : "";
      return `<div class="${cls}">${esc(l) || "&nbsp;"}</div>`;
    }).join("");
  } catch { /* sin servidor o PIN */ }
}

function tarjetaPermiso(plan) {
  const cont = $("messages");
  const row = document.createElement("div");
  row.className = "msg-row assistant permiso";
  const titulo = TITULOS_PERMISO[plan.accion] || plan.accion;

  let cuerpo = "";
  if (plan.accion === "lote" && Array.isArray(plan.datos)) {
    // varias acciones → lista con casillas
    const items = plan.datos.map((a, i) => `
      <div class="lote-item">
        <label class="lote-linea">
          <input type="checkbox" class="lote-check" data-i="${i}" checked>
          <span><strong>${esc(TITULOS_PERMISO[a.accion] || a.accion)}</strong></span>
        </label>
        <pre class="permiso-detalle">${esc(detallePermiso(a.accion, a.datos))}</pre>
      </div>`).join("");
    cuerpo = `<div class="lote-lista">${items}</div>`;
  } else {
    cuerpo = `<pre class="permiso-detalle">${esc(detallePermiso(plan.accion, plan.datos))}</pre>`;
  }

  row.innerHTML = `
    <div class="msg-avatar">🦞</div>
    <div class="msg-body">
      <div class="msg-bubble">
        <div class="permiso-titulo">${titulo} — ¿lo apruebas?</div>
        ${cuerpo}
        <div class="permiso-botones">
          <button class="btn-ok" id="permiso-si">✔ Aprobar</button>
          <button class="btn-no" id="permiso-no">✖ Rechazar</button>
        </div>
      </div>
    </div>`;
  cont.appendChild(row);
  scrollBottom();

  // diff visual para escrituras
  if (plan.accion === "escribir" && plan.datos && plan.datos.ruta) {
    cargarDiff(plan.datos.ruta, plan.datos.contenido || "", row.querySelector(".permiso-detalle"));
  }
  if (plan.accion === "lote" && Array.isArray(plan.datos)) {
    row.querySelectorAll(".lote-item").forEach((item, i) => {
      const a = plan.datos[i];
      if (a && a.accion === "escribir" && a.datos && a.datos.ruta) {
        cargarDiff(a.datos.ruta, a.datos.contenido || "", item.querySelector(".permiso-detalle"));
      }
    });
  }
  return row;
}

/* ---------------- ADJUNTOS ---------------- */

function leerAdjunto(file) {
  return new Promise((resolve) => {
    const esImg = file.type.startsWith("image/");
    const esTexto = /\.(txt|md|py|json|csv|log|js|html|css|ts|tsx|jsx)$/i.test(file.name) || file.type.startsWith("text/");
    const lector = new FileReader();
    if (esImg) {
      lector.onload = () => resolve({ nombre: file.name, tipo: "imagen", data: lector.result });
      lector.readAsDataURL(file);
    } else if (esTexto && file.size < 300000) {
      lector.onload = () => resolve({ nombre: file.name, tipo: "texto", data: lector.result });
      lector.readAsText(file);
    } else {
      resolve({ nombre: file.name, tipo: "otro", data: "" });
    }
  });
}

async function manejarArchivos(files) {
  for (const f of files) {
    const a = await leerAdjunto(f);
    if (a.tipo === "otro") {
      toast("«" + a.nombre + "» no se puede adjuntar (solo imágenes o texto <300KB)");
      continue;
    }
    adjuntosPendientes.push(a);
  }
  pintarAdjuntos();
}

function pintarAdjuntos() {
  const cont = $("adjuntos");
  cont.innerHTML = "";
  adjuntosPendientes.forEach((a, idx) => {
    const chip = document.createElement("div");
    chip.className = "adjunto-chip";
    chip.innerHTML = (a.tipo === "imagen" ? `<img src="${a.data}" alt="">` : `<span>📄</span>`) +
      `<span class="ad-nombre">${esc(a.nombre)}</span><span class="ad-x" data-i="${idx}">✕</span>`;
    chip.querySelector(".ad-x").onclick = () => { adjuntosPendientes.splice(idx, 1); pintarAdjuntos(); };
    cont.appendChild(chip);
  });
}

/* ---------------- conversaciones ---------------- */

async function cargarListaConversaciones() {
  const res = await api("/api/conversaciones");
  pintarListaConversaciones(res.conversaciones || []);
}

function pintarListaConversaciones(lista) {
  const cont = $("lista-conversaciones");
  cont.innerHTML = "";
  const q = ($("buscar-conv").value || "").toLowerCase();
  const filtradas = q ? lista.filter((c) => (c.titulo || "").toLowerCase().includes(q)) : lista;

  if (!filtradas.length) {
    cont.innerHTML = `<div class="empty-state" style="padding:20px 0;font-size:12.5px;">${q ? "Sin resultados" : "Aún no hay conversaciones"}</div>`;
    return;
  }
  for (const c of filtradas) {
    const item = document.createElement("div");
    item.className = "conv-item" + (c.id === chatId ? " active" : "");
    item.innerHTML = `
      <div class="conv-txt">
        <div class="conv-titulo">${esc(c.titulo)}</div>
        <div class="conv-fecha">${fechaRelativa(c.actualizada)}</div>
      </div>
      <button class="conv-del" title="Eliminar">✕</button>`;
    item.onclick = () => cargarConversacion(c.id);
    item.querySelector(".conv-del").onclick = async (e) => {
      e.stopPropagation();
      if (!confirm("¿Eliminar esta conversación?")) return;
      await api("/api/conversaciones/" + c.id, { method: "DELETE" });
      if (chatId === c.id) nuevaConversacion();
      else cargarListaConversaciones();
    };
    cont.appendChild(item);
  }
}

function nuevaConversacion() {
  chatId = null;
  historial = [];
  pendiente = null;
  $("messages").innerHTML = "";
  $("welcome").style.display = "flex";
  $("chat-titulo").textContent = "Nueva conversación";
  cargarListaConversaciones();
  $("input").focus();
}

async function crearSiHaceFalta() {
  if (chatId) return;
  const titulo = historial[0]?.content?.slice(0, 48) || "Nueva conversación";
  const res = await api("/api/conversaciones", { method: "POST", body: JSON.stringify({ titulo }) });
  chatId = res.id;
  $("chat-titulo").textContent = titulo;
  cargarListaConversaciones();
}

async function guardarConversacion() {
  if (!chatId) return;
  await api("/api/conversaciones/" + chatId, {
    method: "PUT",
    body: JSON.stringify({ messages: historial }),
  });
  cargarListaConversaciones();
}

async function cargarConversacion(id) {
  const d = await api("/api/conversaciones/" + id);
  if (d.error) { toast("No se pudo cargar la conversación"); return; }
  chatId = id;
  historial = d.messages || [];
  pendiente = null;
  $("messages").innerHTML = "";
  $("welcome").style.display = "none";
  $("chat-titulo").textContent = d.titulo || "Conversación";
  for (const m of historial) {
    if (m.role === "user") addMarkdown("user", m.content);
    else if (m.role === "assistant") addMarkdown("assistant", m.content);
  }
  if (!historial.length) $("welcome").style.display = "flex";
  cargarListaConversaciones();
  scrollBottom();
}

/* ---------------- envío con STREAMING ---------------- */

async function enviar() {
  const input = $("input");
  const texto = input.value.trim();
  if ((!texto && !adjuntosPendientes.length) || ocupado) return;

  $("welcome").style.display = "none";

  // adjuntos → mensaje
  let contenido = texto;
  let imagen = null;
  for (const a of adjuntosPendientes) {
    if (a.tipo === "imagen" && !imagen) imagen = a.data;
    else if (a.tipo === "texto") contenido += `\n\n[Archivo adjunto: ${a.nombre}]\n${a.data}`;
  }
  if (imagen && !contenido.trim()) contenido = "Describe esta imagen.";

  const msg = { role: "user", content: contenido };
  if (imagen) msg.imagen = imagen;

  addMarkdown("user", contenido + (imagen ? "\n\n🖼️ [imagen adjunta]" : ""));
  historial.push(msg);
  adjuntosPendientes = [];
  pintarAdjuntos();
  input.value = "";
  autosize(input);
  await crearSiHaceFalta();
  guardarConversacion();
  await pedirRespuesta();
}

async function pedirRespuesta() {
  ocupado = true;
  $("btn-send").disabled = true;

  const panel = crearPanelActividad();

  let fila = null;
  let acumulado = "";
  let finalizado = false;

  try {
    const body = { messages: historial };
    if (pendiente && pendiente.resultado !== undefined) {
      body.tool_result = pendiente.resultado;
      pendiente = null;
    }
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: headersExtra(),
      body: JSON.stringify(body),
    });
    if (!res.ok || !res.body) throw new Error("respuesta no válida");

    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line) continue;
        let ev;
        try { ev = JSON.parse(line); } catch { continue; }

        if (ev.tipo === "paso") {
          panel.addPaso("inicio", (ev.icono || "🧠") + " " + (ev.texto || "Pensando…"), "activo");
        } else if (ev.tipo === "pensamiento") {
          panel.pensamiento(ev.texto || "");
        } else if (ev.tipo === "token") {
          if (!fila) {
            const resumen = panel.finalizar();
            fila = crearFilaStream(resumen);
          }
          acumulado += ev.texto;
          fila.bubble.textContent = acumulado + "▍";
          scrollThrottled();
        } else if (ev.tipo === "tool") {
          const icono = ICONO_TOOL[ev.id] || "🔧";
          panel.setPaso("inicio", "hecho");
          panel.setPaso("tool-" + ev.id, "activo", icono + " " + (ev.nombre || ev.id));
        } else if (ev.tipo === "tool_done") {
          const icono = ICONO_TOOL[ev.id] || "🔧";
          panel.setPaso("tool-" + ev.id, "hecho", icono + " " + (ev.nombre || ev.id), ev.resumen || "");
        } else if (ev.tipo === "permiso") {
          if (fila) { fila.row.remove(); fila = null; }
          acumulado = "";
          panel.quitar();
          pendiente = { accion: ev.accion, datos: ev.datos };
          const card = tarjetaPermiso(ev);
          card.querySelector("#permiso-si").onclick = async () => {
            card.remove();
            let accion = ev.accion, datos = ev.datos;
            if (ev.accion === "lote" && Array.isArray(ev.datos)) {
              // solo las acciones marcadas
              const sel = [...card.querySelectorAll(".lote-check")]
                .filter((c) => c.checked)
                .map((c) => ev.datos[+c.dataset.i]);
              if (!sel.length) { pendiente = { resultado: "El usuario no seleccionó ninguna acción." }; }
              else { accion = "lote"; datos = sel; }
            }
            const ejec = await api("/api/pc/ejecutar", {
              method: "POST",
              body: JSON.stringify({ accion, datos }),
            });
            historial.push({ role: "assistant", content: ev.texto });
            pendiente = { resultado: ejec.resultado };
            addMsg("toolnote", "✔ Acción aprobada y ejecutada.");
            guardarConversacion();
            await pedirRespuesta();
          };
          card.querySelector("#permiso-no").onclick = async () => {
            card.remove();
            historial.push({ role: "assistant", content: ev.texto });
            pendiente = { resultado: "El usuario RECHAZÓ la acción. No la ejecutes; pregúntale si quiere otra cosa." };
            addMsg("toolnote", "✖ Acción rechazada.");
            guardarConversacion();
            await pedirRespuesta();
          };
          finalizado = true;
        } else if (ev.tipo === "error") {
          if (fila) { fila.row.remove(); fila = null; }
          panel.quitar();
          addMsg("error", "⚠️ " + ev.texto);
          finalizado = true;
        } else if (ev.tipo === "done") {
          if (fila) {
            const textoFinal = acumulado;
            fila.bubble.classList.add("md");
            fila.bubble.innerHTML = renderMarkdown(textoFinal || "_(sin respuesta)_");
            const body = fila.row.querySelector(".msg-body");
            const time = document.createElement("div");
            time.className = "msg-time";
            time.textContent = ahora();
            const tele = document.createElement("div");
            tele.className = "msg-tele";
            tele.innerHTML = `◉ sintetizada en <span class="t-ok">${ev.segundos ?? "?"}s</span> · ≈${ev.tokens ?? "?"} tokens`;
            const acc = document.createElement("div");
            acc.className = "msg-actions";
            acc.innerHTML = `
              <button class="msg-act" data-act="copy">⧉ Copiar</button>
              <button class="msg-act" data-act="regen">↻ Regenerar</button>
              <button class="msg-act" data-act="speak">🔊 Leer</button>`;
            body.appendChild(time);
            body.appendChild(tele);
            body.appendChild(acc);
            historial.push({ role: "assistant", content: textoFinal });
            guardarConversacion();
            $("hud-tele").textContent = `última síntesis: ${ev.segundos ?? "?"}s · ≈${ev.tokens ?? "?"} tok`;
            if ($("toggle-voz").checked && textoFinal.trim()) leerTexto(textoFinal);
          } else {
            // Sin tokens: cerramos el panel y avisamos si no hay nada que mostrar
            const resumen = panel.finalizar();
            if (resumen) {
              const r = crearFilaStream(resumen);
              r.bubble.classList.add("md");
              r.bubble.innerHTML = renderMarkdown("_(respuesta vacía)_");
              historial.push({ role: "assistant", content: "" });
              guardarConversacion();
            }
          }
          fila = null;
          acumulado = "";
          finalizado = true;
        }
      }
    }

    if (!finalizado) {
      if (fila) {
        fila.bubble.classList.add("md");
        fila.bubble.innerHTML = renderMarkdown(acumulado || "_(sin respuesta)_");
        historial.push({ role: "assistant", content: acumulado });
        guardarConversacion();
      } else {
        panel.quitar();
        addMsg("error", "⚠️ La conexión se cortó a mitad de la respuesta.");
      }
    }
  } catch (e) {
    if (fila) fila.row.remove();
    panel.quitar();
    addMsg("error", "⚠️ No se pudo conectar con el servidor. ¿Está arrancado?");
  } finally {
    panel.quitar();
    ocupado = false;
    $("btn-send").disabled = false;
    $("input").focus();
  }
}

function regenerar() {
  if (ocupado || !historial.length) return;
  while (historial.length && historial[historial.length - 1].role === "assistant") historial.pop();
  const cont = $("messages");
  while (cont.lastElementChild) {
    const el = cont.lastElementChild;
    if (el.classList.contains("msg-row") && el.classList.contains("user")) break;
    cont.removeChild(el);
  }
  guardarConversacion();
  pedirRespuesta();
}

/* ---------------- acciones de mensaje (delegadas) ---------------- */

document.addEventListener("click", async (e) => {
  const act = e.target.closest("[data-act]");
  if (act) {
    const row = act.closest(".msg-row");
    const bubble = row?.querySelector(".msg-bubble");
    const texto = bubble ? (bubble.textContent || "") : "";
    if (act.dataset.act === "copy") {
      try { await navigator.clipboard.writeText(texto); toast("Copiado al portapapeles"); }
      catch { toast("No se pudo copiar"); }
    } else if (act.dataset.act === "regen") {
      regenerar();
    } else if (act.dataset.act === "speak") {
      leerTexto(texto);
    }
    return;
  }
  const cb = e.target.closest("[data-cb]");
  if (cb) {
    const pre = document.getElementById(cb.dataset.cb);
    try {
      await navigator.clipboard.writeText(pre.textContent);
      cb.textContent = "✔ Copiado";
      setTimeout(() => (cb.textContent = "⧉ Copiar"), 1600);
    } catch { toast("No se pudo copiar"); }
  }
});

/* ---------------- VOZ ---------------- */

let vozUtter = null;

function leerTexto(texto) {
  if (!("speechSynthesis" in window)) { toast("Tu navegador no soporta voz"); return; }
  if (vozUtter) { speechSynthesis.cancel(); vozUtter = null; return; }
  const u = new SpeechSynthesisUtterance(texto);
  u.lang = "es-ES";
  const voces = speechSynthesis.getVoices();
  const uri = localStorage.getItem("miclaw-voz-uri");
  const voz = voces.find((v) => v.voiceURI === uri) || voces.find((v) => /^es/i.test(v.lang));
  if (voz) u.voice = voz;
  u.rate = parseFloat(localStorage.getItem("miclaw-voz-rate") || "1");
  u.onend = () => { vozUtter = null; };
  u.onerror = () => { vozUtter = null; };
  vozUtter = u;
  speechSynthesis.speak(u);
}

function cargarVoces() {
  if (!("speechSynthesis" in window)) return;
  const sel = $("select-voz");
  const voces = speechSynthesis.getVoices().filter((v) => /^es/i.test(v.lang));
  if (!voces.length) { sel.innerHTML = `<option value="">(sin voces en español)</option>`; return; }
  const uri = localStorage.getItem("miclaw-voz-uri");
  sel.innerHTML = voces.map((v) =>
    `<option value="${esc(v.voiceURI)}" ${v.voiceURI === uri ? "selected" : ""}>${esc(v.name)}</option>`
  ).join("");
  sel.onchange = () => localStorage.setItem("miclaw-voz-uri", sel.value);
}

let reconocedor = null;

function dictar() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) { toast("Tu navegador no soporta dictado (prueba Chrome o Edge)"); return; }
  if (reconocedor) {
    reconocedor.stop();
    reconocedor = null;
    $("btn-mic").classList.remove("active");
    return;
  }
  reconocedor = new SR();
  reconocedor.lang = "es-ES";
  reconocedor.interimResults = true;
  reconocedor.continuous = false;
  reconocedor.onresult = (e) => {
    let txt = "";
    for (const r of e.results) txt += r[0].transcript;
    $("input").value = txt;
    autosize($("input"));
  };
  reconocedor.onend = () => { reconocedor = null; $("btn-mic").classList.remove("active"); };
  reconocedor.onerror = (err) => {
    reconocedor = null;
    $("btn-mic").classList.remove("active");
    if (err.error !== "aborted") toast("Error de dictado: " + err.error);
  };
  reconocedor.start();
  $("btn-mic").classList.add("active");
  toast("🎤 Escuchando… habla ahora");
}

/* ---------------- TEMAS ---------------- */

function aplicarTema(t) {
  document.documentElement.dataset.theme = t;
  localStorage.setItem("miclaw-tema", t);
  $("btn-tema").textContent = t === "dark" ? "☀️ Tema claro" : "🌙 Tema oscuro";
}

function toggleTema() {
  aplicarTema(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
}

/* ---------------- PALETA DE COMANDOS ---------------- */

function abrirPaleta() {
  const pal = $("paleta");
  pal.classList.remove("hidden");
  const input = $("paleta-input");
  input.value = "";
  pintarPaleta("");
  input.focus();
}

function cerrarPaleta() {
  $("paleta").classList.add("hidden");
}

function accionesPaleta() {
  const acciones = [
    { icon: "✚", label: "Nueva conversación", kbd: "Ctrl+N", fn: () => nuevaConversacion() },
    { icon: "⬇", label: "Exportar conversación", fn: () => exportarConversacion() },
    { icon: "◐", label: "Cambiar tema claro/oscuro", fn: toggleTema },
    { icon: "⚙️", label: "Ir a Ajustes", kbd: "Ctrl+,", fn: () => switchView("ajustes") },
    { icon: "🧠", label: "Ir a Memoria", fn: () => switchView("memoria") },
    { icon: "⚡", label: "Probar conexión del proveedor", fn: probarConexion },
    { icon: "🦞", label: "Ir al Chat", fn: () => switchView("chat") },
  ];
  if (estado) {
    for (const [pid, info] of Object.entries(estado.proveedores)) {
      acciones.push({
        icon: "➤", label: "Usar proveedor: " + info.nombre,
        fn: () => seleccionarProveedor(pid),
      });
    }
  }
  return acciones;
}

function pintarPaleta(q) {
  const cont = $("paleta-items");
  const lista = accionesPaleta().filter((a) => a.label.toLowerCase().includes(q.toLowerCase()));
  if (!lista.length) { cont.innerHTML = `<div class="paleta-empty">Sin resultados</div>`; return; }
  cont.innerHTML = "";
  lista.forEach((a, idx) => {
    const item = document.createElement("div");
    item.className = "paleta-item" + (idx === 0 ? " sel" : "");
    item.innerHTML = `<span>${a.icon}</span><span>${esc(a.label)}</span>${a.kbd ? `<span class="pi-kbd">${esc(a.kbd)}</span>` : ""}`;
    item.onclick = () => { cerrarPaleta(); a.fn(); };
    item.onmouseenter = () => { cont.querySelectorAll(".paleta-item").forEach((x) => x.classList.remove("sel")); item.classList.add("sel"); };
    cont.appendChild(item);
  });
}

function paletaNavegar(delta) {
  const items = [...$("paleta-items").querySelectorAll(".paleta-item")];
  if (!items.length) return;
  let idx = items.findIndex((x) => x.classList.contains("sel"));
  idx = (idx + delta + items.length) % items.length;
  items.forEach((x) => x.classList.remove("sel"));
  items[idx].classList.add("sel");
  items[idx].scrollIntoView({ block: "nearest" });
}

/* ---------------- recordatorios ---------------- */

function notificar(titulo, cuerpo) {
  toast("⏰ " + titulo + " — " + cuerpo);
  if ("Notification" in window) {
    if (Notification.permission === "granted") {
      try { new Notification(titulo, { body: cuerpo }); } catch { /* noop */ }
    } else if (Notification.permission === "default") {
      Notification.requestPermission();
    }
  }
}

async function cargarRecordatorios() {
  try {
    const res = await api("/api/recordatorios");
    pintarRecordatorios(res.recordatorios || []);
  } catch { /* servidor apagado */ }
}

function pintarRecordatorios(lista) {
  const cont = $("recordatorios-list");
  cont.innerHTML = "";
  if (!lista.length) {
    cont.innerHTML = `<div class="empty-state">Sin recordatorios.<br>Pídele a MiClaw: «recuérdame llamar a Ana mañana a las 9»</div>`;
    return;
  }
  for (const r of lista) {
    const card = document.createElement("div");
    card.className = "apunte-card";
    card.innerHTML = `
      <div class="ap-icon">⏰</div>
      <div class="ap-body">
        <div class="ap-contenido">${esc(r.texto)}</div>
        <div class="ap-fecha">${esc(r.cuando)}</div>
      </div>
      <button class="ap-del" data-rid="${esc(r.id)}">✕</button>`;
    card.querySelector(".ap-del").onclick = async () => {
      await api("/api/recordatorios/" + r.id, { method: "DELETE" });
      cargarRecordatorios();
    };
    cont.appendChild(card);
  }
}

function iniciarVigilanciaRecordatorios() {
  setInterval(async () => {
    try {
      const res = await api("/api/recordatorios/vencidos");
      const v = res.vencidos || [];
      for (const r of v) {
        notificar("Recordatorio", r.texto);
        await api("/api/recordatorios/" + r.id, { method: "DELETE" });
      }
      if (v.length) cargarRecordatorios();
    } catch { /* sin servidor */ }
  }, 15000);
}

/* ---------------- TAREAS AUTÓNOMAS ---------------- */

async function cargarTareas() {
  try {
    const res = await api("/api/tareas");
    const lista = res.tareas || [];
    pintarTareas(lista);
    for (const t of lista) {
      if ((t.estado === "hecho" || t.estado === "error") && !tareasVistas.has(t.id)) {
        tareasVistas.add(t.id);
        if (t.estado === "hecho") notificar("🤖 Tarea completada", t.prompt);
        else notificar("⚠️ Tarea con error", t.prompt);
      }
    }
  } catch { /* servidor apagado */ }
}

function pintarTareas(lista) {
  const cont = $("tareas-list");
  cont.innerHTML = "";
  if (!lista.length) {
    cont.innerHTML = `<div class="empty-state">Sin tareas programadas.<br>Pídele: «programa una tarea para mañana a las 9 que busque las noticias»</div>`;
    return;
  }
  const ETI = { pendiente: "⏳ pendiente", ejecutando: "⚙️ ejecutando", hecho: "✔ hecha", error: "✖ error" };
  for (const t of lista) {
    const card = document.createElement("div");
    card.className = "apunte-card tarea-card";
    const repite = t.repite ? (t.repite.tipo === "diaria" ? " · 🔁 cada día"
      : t.repite.tipo === "horaria" ? " · 🔁 cada hora"
      : t.repite.tipo === "semanal" ? " · 🔁 cada semana" : "") : "";
    card.innerHTML = `
      <div class="ap-icon">🤖</div>
      <div class="ap-body">
        <div class="ap-contenido">
          ${esc(t.prompt)}
          <span class="tarea-estado ${esc(t.estado)}">${ETI[t.estado] || t.estado}</span>
        </div>
        <div class="ap-fecha">⏱ ${esc(t.cuando)}${repite}</div>
        ${t.resultado ? `<div class="tarea-resultado">${esc(t.resultado.slice(0, 400))}</div>` : ""}
      </div>
      <button class="ap-del" data-tid="${esc(t.id)}">✕</button>`;
    card.querySelector(".ap-del").onclick = async () => {
      await api("/api/tareas/" + t.id, { method: "DELETE" });
      cargarTareas();
    };
    cont.appendChild(card);
  }
}

/* ---------------- ajustes ---------------- */

function pintarProveedores() {
  const cont = $("provider-list");
  cont.innerHTML = "";
  const ICONOS = {
    ollama: "🦙", gemini: "💎", groq: "🚄", openrouter: "🧭", alibaba: "🦔",
    mistral: "🌬️", cerebras: "⚡", zai: "🔮", github: "🐙", sambanova: "🧠", custom: "🔧",
  };
  for (const [pid, info] of Object.entries(estado.proveedores)) {
    const div = document.createElement("div");
    div.className = "provider-item" + (estado.proveedor === pid ? " sel" : "");
    const lista = info.tipo === "clave" ? Boolean(estado.claves[pid]) : true;
    div.innerHTML = `
      <div class="p-icon">${ICONOS[pid] || "🤖"}</div>
      <h4>${esc(info.nombre)}</h4>
      <p>${esc(info.info)}</p>
      <span class="badge ${lista ? "ok" : "warn"}">${lista ? "✔ listo" : "necesita clave"}</span>`;
    div.onclick = () => seleccionarProveedor(pid);
    cont.appendChild(div);
  }
}

function pintarModelos() {
  const sel = $("select-modelo");
  sel.innerHTML = "";
  const info = estado.proveedores[estado.proveedor];
  const modelos = info ? info.modelos : [];
  if (!modelos.length) {
    const opt = document.createElement("option");
    opt.textContent = estado.proveedor === "ollama"
      ? "(Ollama no responde — instálalo en ollama.com y haz 'ollama pull llama3.2')"
      : "(sin modelos disponibles — configura el proveedor personalizado)";
    opt.value = "";
    sel.appendChild(opt);
  }
  for (const m of modelos) {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.textContent = m.nombre;
    if (m.id === estado.modelo) opt.selected = true;
    sel.appendChild(opt);
  }
  sel.onchange = async () => {
    await api("/api/modelo", { method: "POST", body: JSON.stringify({ provider: estado.proveedor, model: sel.value }) });
    estado.modelo = sel.value;
    pintarCajaProveedor();
    toast("Modelo actualizado");
  };
}

function pintarClaves() {
  const cont = $("key-list");
  cont.innerHTML = "";
  const NOMBRES = {
    gemini: "Gemini", groq: "Groq", openrouter: "OpenRouter", alibaba: "Alibaba",
    mistral: "Mistral", cerebras: "Cerebras", zai: "Z.ai", github: "GitHub",
    sambanova: "SambaNova", custom: "Personalizado",
  };
  for (const [pid, info] of Object.entries(estado.proveedores)) {
    if (info.tipo !== "clave") continue;
    const row = document.createElement("div");
    row.className = "key-row";
    const tiene = estado.claves[pid];
    row.innerHTML = `
      <label title="${esc(info.nombre)}">${NOMBRES[pid] || pid}</label>
      <input type="password" class="key-input" placeholder="${tiene ? "•••••••• (guardada)" : "pega tu clave aquí"}">
      <button data-save="${pid}">Guardar</button>
      <span class="key-status ${tiene ? "ok" : ""}">${tiene ? "✔ guardada" : ""}</span>`;
    row.querySelector(`[data-save="${pid}"]`).onclick = async () => {
      const input = row.querySelector(".key-input");
      const valor = input.value.trim();
      if (!valor) { toast("Escribe la clave primero"); return; }
      await api("/api/clave", { method: "POST", body: JSON.stringify({ provider: pid, key: valor }) });
      input.value = "";
      toast("Clave de " + (NOMBRES[pid] || pid) + " guardada");
      await cargarEstado();
    };
    cont.appendChild(row);
  }
}

function pintarCajaProveedor() {
  const info = estado.proveedores[estado.proveedor];
  const nombre = info ? info.nombre : estado.proveedor;
  $("provider-name").textContent = nombre;
  $("provider-model").textContent = estado.modelo || "";
  const activo = estado.proveedor === "ollama"
    ? estado.ollama_activo
    : Boolean(estado.claves[estado.proveedor]);
  $("provider-dot").className = "dot" + (activo ? " on" : "");
  $("chip-proveedor").textContent = nombre;
  $("welcome-provider").textContent = nombre;
  $("hud-prov").textContent = estado.proveedor + " · " + (estado.modelo || "?");
  $("card-custom").style.display = estado.proveedor === "custom" ? "" : "none";
}

function pintarCustom() {
  $("custom-url").value = estado.custom.base_url || "";
  $("custom-modelos").value = (estado.custom.modelos || []).join("\n");
}

/* ---------------- RAG (base de conocimiento) ---------------- */

function pintarRag() {
  const est = estado.rag || {};
  $("rag-ruta").value = est.ruta || "";
  const out = $("rag-estado");
  if (est.indexado) {
    out.className = "probar-resultado ok";
    out.textContent = `✔ ${est.archivos} archivos indexados (${est.trozos} trozos) · ${est.actualizado}`;
  } else {
    out.className = "probar-resultado";
    out.textContent = "Sin índice todavía. Pulsa «Indexar ahora».";
  }
}

async function indexarRag() {
  const btn = $("btn-rag-indexar");
  const out = $("rag-estado");
  btn.disabled = true;
  out.className = "probar-resultado loading";
  out.textContent = "Indexando…";
  try {
    const r = await api("/api/rag/indexar", {
      method: "POST",
      body: JSON.stringify({ ruta: $("rag-ruta").value.trim() }),
    });
    if (r.ok) {
      out.className = "probar-resultado ok";
      out.textContent = `✔ ${r.archivos} archivos indexados (${r.trozos} trozos) en ${r.segundos}s`;
      estado.rag = { indexado: true, ruta: r.ruta || $("rag-ruta").value, archivos: r.archivos, trozos: r.trozos, actualizado: "ahora" };
    } else {
      out.className = "probar-resultado err";
      out.textContent = "✖ " + (r.error || "error al indexar");
    }
  } catch {
    out.className = "probar-resultado err";
    out.textContent = "✖ Sin conexión con el servidor";
  } finally {
    btn.disabled = false;
  }
}

/* ---------------- informes ---------------- */

async function cargarInformes() {
  try {
    const res = await api("/api/informes");
    const cont = $("informes-list");
    cont.innerHTML = "";
    const lista = res.informes || [];
    if (!lista.length) {
      cont.innerHTML = `<div class="empty-state">Sin informes todavía.<br>Pídele: «guarda un informe de las noticias de hoy»</div>`;
      return;
    }
    for (const inf of lista) {
      const card = document.createElement("div");
      card.className = "apunte-card";
      card.innerHTML = `
        <div class="ap-icon">📊</div>
        <div class="ap-body">
          <div class="ap-contenido">${esc(inf.nombre)}</div>
          <div class="ap-fecha">${esc(inf.fecha)} · ${(inf.tamano / 1024).toFixed(1)} KB</div>
        </div>
        <div class="informe-btns">
          <button class="ap-del" data-ver="${esc(inf.nombre)}">👁 Ver</button>
          <button class="ap-del" data-borrar="${esc(inf.nombre)}">✕</button>
        </div>`;
      card.querySelector('[data-ver]').onclick = async () => {
        const r = await api("/api/informes/" + inf.nombre);
        if (r.error) { toast("No se pudo leer"); return; }
        $("modal-titulo").textContent = "📊 " + inf.nombre;
        $("modal-content").textContent = r.contenido;
        $("modal").classList.remove("hidden");
      };
      card.querySelector('[data-borrar]').onclick = async () => {
        await api("/api/informes/" + inf.nombre, { method: "DELETE" });
        cargarInformes();
      };
      cont.appendChild(card);
    }
  } catch { /* servidor apagado */ }
}

/* ---------------- modos ---------------- */
function pintarModos() {
  const sel = $("select-modo");
  sel.innerHTML = "";
  for (const [id, nombre] of Object.entries(estado.modos || {})) {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = nombre;
    if (id === estado.modo) opt.selected = true;
    sel.appendChild(opt);
  }
  sel.onchange = async () => {
    await api("/api/config", { method: "POST", body: JSON.stringify({ modo: sel.value }) });
    estado.modo = sel.value;
    toast("Modo: " + (estado.modos[sel.value] || sel.value));
  };
}

async function seleccionarProveedor(pid) {
  const modelos = estado.proveedores[pid].modelos;
  const modelo = modelos.length ? modelos[0].id : ($("select-modelo").value || "");
  await api("/api/modelo", { method: "POST", body: JSON.stringify({ provider: pid, model: modelo }) });
  estado.proveedor = pid;
  estado.modelo = modelo;
  await cargarEstado();
  toast("Proveedor: " + estado.proveedores[pid].nombre);
}

async function probarConexion() {
  const btn = $("btn-probar");
  const res = $("probar-resultado");
  btn.disabled = true;
  res.className = "probar-resultado loading";
  res.textContent = "Probando…";
  try {
    const r = await api("/api/probar", { method: "POST", body: JSON.stringify({}) });
    if (r.ok) {
      res.className = "probar-resultado ok";
      res.textContent = "✔ Conexión correcta · «" + r.respuesta + "»";
    } else {
      res.className = "probar-resultado err";
      res.textContent = "✖ " + r.error;
    }
  } catch {
    res.className = "probar-resultado err";
    res.textContent = "✖ Sin conexión con el servidor";
  } finally {
    btn.disabled = false;
  }
}

/* ---------------- memoria ---------------- */

async function cargarMemoria() {
  const res = await api("/api/memoria");
  const cont = $("apuntes-list");
  cont.innerHTML = "";
  const apuntes = res.apuntes || [];
  if (!apuntes.length) {
    cont.innerHTML = `<div class="empty-state">🧠 Vacía — MiClaw aún no sabe nada de ti.<br>Pídele: «recuerda que…»</div>`;
    return;
  }
  for (const a of apuntes) {
    const card = document.createElement("div");
    card.className = "apunte-card";
    card.innerHTML = `
      <div class="ap-icon">📝</div>
      <div class="ap-body">
        <div class="ap-contenido">${esc(a.contenido)}</div>
        <div class="ap-fecha">${esc(a.nombre)} · ${esc(a.fecha || "")}</div>
      </div>
      <button class="ap-del" data-apunte="${esc(a.nombre)}">✕</button>`;
    card.querySelector(".ap-del").onclick = async () => {
      await api("/api/memoria/" + a.nombre, { method: "DELETE" });
      cargarMemoria();
      toast("Apunte borrado");
    };
    cont.appendChild(card);
  }
}

/* ---------------- exportar ---------------- */

function exportarConversacion() {
  if (!historial.length) { toast("No hay nada que exportar"); return; }
  const titulo = $("chat-titulo").textContent || "conversacion";
  let md = `# ${titulo}\n\n`;
  for (const m of historial) {
    md += `**${m.role === "user" ? "Tú" : "MiClaw"}:**\n\n${m.content}\n\n---\n\n`;
  }
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = titulo.replace(/[^\w\sáéíóúñ-]/gi, "").slice(0, 40) + ".md";
  a.click();
  URL.revokeObjectURL(url);
  toast("Conversación exportada");
}

/* ---------------- navegación ---------------- */

function switchView(vista) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.querySelectorAll(".nav-btn[data-view]").forEach((b) => b.classList.remove("active"));
  $("view-" + vista).classList.add("active");
  document.querySelector(`.nav-btn[data-view="${vista}"]`)?.classList.add("active");
  if (vista === "memoria") { cargarMemoria(); cargarRecordatorios(); cargarTareas(); cargarInformes(); }
  if (vista === "ajustes") cargarEstado();
}

/* ---------------- estado global ---------------- */

async function cargarEstado() {
  estado = await api("/api/estado");
  pintarProveedores();
  pintarModelos();
  pintarClaves();
  pintarCajaProveedor();
  pintarCustom();
  pintarModos();
  pintarRag();
  $("pc-carpeta").value = estado.pc.carpeta_extra || "";
  $("toggle-memoria").checked = estado.memoria_incluida !== false;
  $("toggle-auto").checked = estado.auto_aprobar === true;
  $("toggle-razonamiento").checked = estado.razonamiento === true;
  $("hud-auto").hidden = estado.auto_aprobar !== true;
  // PIN: estado
  const pe = $("pin-estado");
  if (estado.pin_activo) {
    pe.className = "probar-resultado ok";
    pe.textContent = "✔ PIN activo";
  } else {
    pe.className = "probar-resultado";
    pe.textContent = "PIN desactivado (acceso libre en tu red local)";
  }
  // direcciones IP locales para el móvil
  try {
    const red = await api("/api/red");
    $("red-ips").textContent = red.ips.length
      ? red.ips.map((ip) => `http://${ip}:${red.puerto}`).join("  ·  ")
      : "http://[IP-de-tu-PC]:8000";
  } catch { $("red-ips").textContent = "http://[IP-de-tu-PC]:8000"; }
}

function autosize(ta) {
  ta.style.height = "auto";
  ta.style.height = Math.min(ta.scrollHeight, 170) + "px";
}

/* ---------------- init ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  // arranque futurista
  arrancarBoot();
  iniciarRedNeuronal();

  // tema
  aplicarTema(localStorage.getItem("miclaw-tema") || "dark");
  $("btn-tema").onclick = toggleTema;

  // navegación
  document.querySelectorAll(".nav-btn[data-view]").forEach((b) => {
    b.onclick = () => switchView(b.dataset.view);
  });
  $("ir-ajustes").onclick = () => switchView("ajustes");

  // conversaciones
  $("btn-nueva").onclick = nuevaConversacion;
  $("buscar-conv").addEventListener("input", () => cargarListaConversaciones());

  // chat
  $("chat-form").onsubmit = (e) => { e.preventDefault(); enviar(); };
  const ta = $("input");
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); enviar(); }
  });
  ta.addEventListener("input", () => autosize(ta));
  $("btn-exportar").onclick = exportarConversacion;
  $("btn-mic").onclick = dictar;

  // adjuntos
  $("btn-adjunto").onclick = () => $("file-input").click();
  $("file-input").onchange = (e) => { manejarArchivos(e.target.files); e.target.value = ""; };
  ["messages", "welcome"].forEach((id) => {
    const el = $(id);
    if (!el) return;
    el.addEventListener("dragover", (e) => { e.preventDefault(); el.style.outline = "2px dashed rgba(124,92,255,.6)"; el.style.outlineOffset = "-8px"; });
    el.addEventListener("dragleave", () => { el.style.outline = ""; });
    el.addEventListener("drop", (e) => {
      e.preventDefault(); el.style.outline = "";
      if (e.dataTransfer.files.length) manejarArchivos(e.dataTransfer.files);
    });
  });

  // chips de bienvenida
  document.querySelectorAll(".chip-sug").forEach((ch) => {
    ch.onclick = () => {
      $("input").value = ch.dataset.s;
      enviar();
    };
  });

  // paleta de comandos
  $("btn-paleta").onclick = abrirPaleta;
  $("paleta").addEventListener("click", (e) => { if (e.target.id === "paleta") cerrarPaleta(); });
  $("paleta-input").addEventListener("input", (e) => pintarPaleta(e.target.value));
  $("paleta-input").addEventListener("keydown", (e) => {
    if (e.key === "Escape") cerrarPaleta();
    if (e.key === "ArrowDown") { e.preventDefault(); paletaNavegar(1); }
    if (e.key === "ArrowUp") { e.preventDefault(); paletaNavegar(-1); }
    if (e.key === "Enter") {
      e.preventDefault();
      const sel = $("paleta-items").querySelector(".paleta-item.sel");
      if (sel) { cerrarPaleta(); sel.click(); }
    }
  });

  // voz
  cargarVoces();
  if ("speechSynthesis" in window) speechSynthesis.onvoiceschanged = cargarVoces;
  $("toggle-voz").checked = localStorage.getItem("miclaw-voz-auto") === "1";
  $("toggle-voz").onchange = () =>
    localStorage.setItem("miclaw-voz-auto", $("toggle-voz").checked ? "1" : "0");
  $("rango-voz").value = localStorage.getItem("miclaw-voz-rate") || "1";
  $("voz-vel-label").textContent = parseFloat($("rango-voz").value).toFixed(2) + "×";
  $("rango-voz").oninput = () => {
    localStorage.setItem("miclaw-voz-rate", $("rango-voz").value);
    $("voz-vel-label").textContent = parseFloat($("rango-voz").value).toFixed(2) + "×";
  };
  $("btn-probar-voz").onclick = () => leerTexto("Hola, soy MiClaw. Superinteligencia local activada.");

  // PIN / desbloqueo
  $("lock-btn").onclick = async () => {
    const pin = $("lock-pin").value.trim();
    $("lock-err").textContent = "";
    try {
      const r = await api("/api/pin", { method: "POST", body: JSON.stringify({ pin }) });
      if (r.ok) {
        token = r.token;
        localStorage.setItem("miclaw-token", token);
        ocultarLock();
        cargarEstado();
        cargarListaConversaciones();
        cargarTareas();
        toast("🔓 Desbloqueado");
      } else {
        $("lock-err").textContent = "PIN incorrecto";
      }
    } catch {
      $("lock-err").textContent = "Sin conexión con el servidor";
    }
  };
  $("lock-pin").addEventListener("keydown", (e) => {
    if (e.key === "Enter") $("lock-btn").click();
  });

  $("btn-pin").onclick = async () => {
    const pin = $("pin-input").value;
    await api("/api/config", { method: "POST", body: JSON.stringify({ pin }) });
    $("pin-input").value = "";
    toast(pin.trim() ? "🔐 PIN activado" : "PIN desactivado");
    await cargarEstado();
  };

  // ajustes
  $("btn-probar").onclick = probarConexion;
  $("btn-rag-indexar").onclick = indexarRag;
  $("modal-cerrar").onclick = () => $("modal").classList.add("hidden");
  $("modal").addEventListener("click", (e) => { if (e.target.id === "modal") $("modal").classList.add("hidden"); });
  $("btn-custom").onclick = async () => {
    const modelos = $("custom-modelos").value.split("\n").map((s) => s.trim()).filter(Boolean);
    await api("/api/custom", { method: "POST", body: JSON.stringify({ base_url: $("custom-url").value.trim(), modelos }) });
    toast("Proveedor personalizado guardado");
    await cargarEstado();
  };
  $("btn-pc-config").onclick = async () => {
    await api("/api/pc/config", { method: "POST", body: JSON.stringify({ carpeta_extra: $("pc-carpeta").value.trim() }) });
    toast("Carpeta permitida guardada");
  };
  $("toggle-memoria").onchange = async () => {
    await api("/api/config", { method: "POST", body: JSON.stringify({ memoria_incluida: $("toggle-memoria").checked }) });
    toast($("toggle-memoria").checked ? "Memoria activada" : "Memoria desactivada");
  };
  $("toggle-auto").onchange = async () => {
    await api("/api/config", { method: "POST", body: JSON.stringify({ auto_aprobar: $("toggle-auto").checked }) });
    $("hud-auto").hidden = !$("toggle-auto").checked;
    toast($("toggle-auto").checked
      ? "🚀 Auto-aprobación activada: ejecutaré comandos y herramientas sin pedir permiso"
      : "🔒 Auto-aprobación desactivada: volveré a pedirte confirmación");
  };
  $("toggle-razonamiento").onchange = async () => {
    await api("/api/config", { method: "POST", body: JSON.stringify({ razonamiento: $("toggle-razonamiento").checked }) });
    toast($("toggle-razonamiento").checked
      ? "🧠 Razonamiento profundo activado (más reflexivo, más lento)"
      : "⚡ Modo rápido activado: respuestas más veloces");
  };

  // tareas
  $("btn-tarea-crear").onclick = async () => {
    const prompt = $("tarea-prompt").value.trim();
    const cuando = $("tarea-cuando").value.trim();
    if (!prompt || !cuando) { toast("Rellena qué hacer y cuándo"); return; }
    const r = await api("/api/tareas", { method: "POST", body: JSON.stringify({ prompt, cuando }) });
    if (r.ok) {
      toast(r.msg);
      $("tarea-prompt").value = ""; $("tarea-cuando").value = "";
      cargarTareas();
    } else {
      toast(r.msg);
    }
  };

  // memoria
  $("btn-borrar-memoria").onclick = async () => {
    if (!confirm("¿Seguro que quieres borrar TODA la memoria?")) return;
    await api("/api/memoria", { method: "DELETE" });
    cargarMemoria();
    toast("Memoria borrada");
  };

  // atajos de teclado
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "n") { e.preventDefault(); nuevaConversacion(); }
    if ((e.ctrlKey || e.metaKey) && e.key === ",") { e.preventDefault(); switchView("ajustes"); }
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); abrirPaleta(); }
  });

  // vigilancia: recordatorios + tareas
  iniciarVigilanciaRecordatorios();
  setInterval(cargarTareas, 15000);

  // arranque
  cargarEstado();
  cargarListaConversaciones();
  cargarTareas();
  setTimeout(() => $("input").focus(), 900);
});

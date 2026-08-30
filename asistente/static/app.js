/* ============================================================
   MiClaw — frontend premium (v1.1: streaming, voz, temas, más)
   ============================================================ */
"use strict";

const $ = (id) => document.getElementById(id);

let estado = null;
let historial = [];
let chatId = null;          // id de la conversación actual (null = nueva sin guardar)
let pendiente = null;       // plan de acción sobre el PC esperando aprobación
let ocupado = false;        // hay una petición en curso

/* ---------------- utilidades ---------------- */

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  return res.json();
}

function toast(msg) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 3200);
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

function crearFilaStream() {
  const cont = $("messages");
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `
    <div class="msg-avatar">🦞</div>
    <div class="msg-body"><div class="msg-bubble"></div></div>`;
  cont.appendChild(row);
  scrollBottom();
  return { row, bubble: row.querySelector(".msg-bubble") };
}

function mostrarPensando(texto) {
  const cont = $("messages");
  const row = document.createElement("div");
  row.className = "msg-row assistant";
  row.innerHTML = `
    <div class="msg-avatar">🦞</div>
    <div class="msg-body"><div class="thinking">
      <span class="dots"><span></span><span></span><span></span></span>
      <span class="thinking-txt">${esc(texto)}</span>
    </div></div>`;
  cont.appendChild(row);
  scrollBottom();
  return row;
}

function tarjetaPermiso(plan) {
  const cont = $("messages");
  const row = document.createElement("div");
  row.className = "msg-row assistant permiso";
  const titulos = {
    ver: "👀 Leer archivo", escribir: "✍️ Escribir archivo",
    terminal: "💻 Ejecutar comando", apuntes: "🧠 Leer apuntes",
  };
  let detalle = "";
  if (plan.accion === "ver") detalle = String(plan.datos || "");
  if (plan.accion === "terminal") detalle = String(plan.datos || "");
  if (plan.accion === "escribir" && plan.datos && plan.datos.ruta) {
    detalle = "RUTA: " + plan.datos.ruta + "\n\n" + String(plan.datos.contenido || "").slice(0, 500);
  }
  if (plan.accion === "apuntes") detalle = "Mostrar los apuntes guardados";
  row.innerHTML = `
    <div class="msg-avatar">🦞</div>
    <div class="msg-body">
      <div class="msg-bubble">
        <div class="permiso-titulo">${titulos[plan.accion] || plan.accion} — ¿lo apruebas?</div>
        <pre class="permiso-detalle">${esc(detalle || "(sin datos)")}</pre>
        <div class="permiso-botones">
          <button class="btn-ok" id="permiso-si">✔ Aprobar</button>
          <button class="btn-no" id="permiso-no">✖ Rechazar</button>
        </div>
      </div>
    </div>`;
  cont.appendChild(row);
  scrollBottom();
  return row;
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
  if (!texto || ocupado) return;

  $("welcome").style.display = "none";
  addMarkdown("user", texto);
  historial.push({ role: "user", content: texto });
  pendiente = null; // un mensaje nuevo resetea cualquier flujo de herramienta anterior
  input.value = "";
  autosize(input);
  await crearSiHaceFalta();
  guardarConversacion();
  await pedirRespuesta();
}

async function pedirRespuesta() {
  ocupado = true;
  $("btn-send").disabled = true;

  const prov = estado?.proveedores?.[estado.proveedor];
  const pensando = mostrarPensando(`Conectando con ${prov?.nombre || estado?.proveedor || "…"}`);
  const rotador = setInterval(() => {
    const f = pensando.querySelector(".thinking-txt");
    if (f) f.textContent = ["Pensando…", "Consultando…", "Casi listo…"][Math.floor(Math.random() * 3)];
  }, 4200);

  let fila = null;          // burbuja provisional del asistente (streaming)
  let acumulado = "";
  let finalizado = false;
  let pensandoVivo = true;

  const quitarPensando = () => {
    if (pensandoVivo && document.body.contains(pensando)) pensando.remove();
    clearInterval(rotador);
    pensandoVivo = false;
  };

  try {
    const body = { messages: historial };
    if (pendiente && pendiente.resultado !== undefined) {
      body.tool_result = pendiente.resultado;
      pendiente = null;
    }
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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

        if (ev.tipo === "token") {
          if (!fila) { quitarPensando(); fila = crearFilaStream(); }
          acumulado += ev.texto;
          fila.bubble.textContent = acumulado + "▍";
          scrollThrottled();
        } else if (ev.tipo === "tool") {
          if (fila) { fila.row.remove(); fila = null; }
          acumulado = "";
          addMsg("toolnote", "🔧 He usado la herramienta «" + (ev.nombre || ev.id) + "»");
        } else if (ev.tipo === "permiso") {
          if (fila) { fila.row.remove(); fila = null; }
          acumulado = "";
          pendiente = { accion: ev.accion, datos: ev.datos };
          const card = tarjetaPermiso(ev);
          card.querySelector("#permiso-si").onclick = async () => {
            card.remove();
            const ejec = await api("/api/pc/ejecutar", {
              method: "POST",
              body: JSON.stringify({ accion: ev.accion, datos: ev.datos }),
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
            const acc = document.createElement("div");
            acc.className = "msg-actions";
            acc.innerHTML = `
              <button class="msg-act" data-act="copy">⧉ Copiar</button>
              <button class="msg-act" data-act="regen">↻ Regenerar</button>
              <button class="msg-act" data-act="speak">🔊 Leer</button>`;
            body.appendChild(time);
            body.appendChild(acc);
            historial.push({ role: "assistant", content: textoFinal });
            guardarConversacion();
            if ($("toggle-voz").checked && textoFinal.trim()) leerTexto(textoFinal);
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
        addMsg("error", "⚠️ La conexión se cortó a mitad de la respuesta.");
      }
    }
  } catch (e) {
    if (fila) fila.row.remove();
    addMsg("error", "⚠️ No se pudo conectar con el servidor. ¿Está arrancado?");
  } finally {
    quitarPensando();
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

/* dictado por micrófono */
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
  $("card-custom").style.display = estado.proveedor === "custom" ? "" : "none";
}

function pintarCustom() {
  $("custom-url").value = estado.custom.base_url || "";
  $("custom-modelos").value = (estado.custom.modelos || []).join("\n");
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
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
  $("view-" + vista).classList.add("active");
  document.querySelector(`.nav-btn[data-view="${vista}"]`)?.classList.add("active");
  if (vista === "memoria") { cargarMemoria(); cargarRecordatorios(); }
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
  $("pc-carpeta").value = estado.pc.carpeta_extra || "";
  $("toggle-memoria").checked = estado.memoria_incluida !== false;
}

function autosize(ta) {
  ta.style.height = "auto";
  ta.style.height = Math.min(ta.scrollHeight, 170) + "px";
}

/* ---------------- init ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  // tema
  aplicarTema(localStorage.getItem("miclaw-tema") || "dark");
  $("btn-tema").onclick = () =>
    aplicarTema(document.documentElement.dataset.theme === "dark" ? "light" : "dark");

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

  // chips de bienvenida
  document.querySelectorAll(".chip-sug").forEach((ch) => {
    ch.onclick = () => {
      $("input").value = ch.dataset.s;
      enviar();
    };
  });

  // voz
  cargarVoces();
  if ("speechSynthesis" in window) {
    speechSynthesis.onvoiceschanged = cargarVoces;
  }
  $("toggle-voz").checked = localStorage.getItem("miclaw-voz-auto") === "1";
  $("toggle-voz").onchange = () =>
    localStorage.setItem("miclaw-voz-auto", $("toggle-voz").checked ? "1" : "0");
  $("rango-voz").value = localStorage.getItem("miclaw-voz-rate") || "1";
  $("voz-vel-label").textContent = parseFloat($("rango-voz").value).toFixed(2) + "×";
  $("rango-voz").oninput = () => {
    localStorage.setItem("miclaw-voz-rate", $("rango-voz").value);
    $("voz-vel-label").textContent = parseFloat($("rango-voz").value).toFixed(2) + "×";
  };
  $("btn-probar-voz").onclick = () => leerTexto("Hola, soy MiClaw. ¡Listo para ayudarte!");

  // ajustes
  $("btn-probar").onclick = probarConexion;
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
  });

  // recordatorios
  iniciarVigilanciaRecordatorios();

  // arranque
  cargarEstado();
  cargarListaConversaciones();
  $("input").focus();
});

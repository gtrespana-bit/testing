/* MiClaw — frontend */

const $ = (id) => document.getElementById(id);

let estado = null;
let historial = [];

/* ---------------- utilidades ---------------- */

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  return res.json();
}

function toast(msg) {
  const t = $("toast") || (() => {
    const el = document.createElement("div");
    el.id = "toast";
    el.className = "toast";
    document.body.appendChild(el);
    return el;
  })();
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove("show"), 2600);
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

/* ---------------- estado / navegación ---------------- */

function switchView(vista) {
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
  $("view-" + vista).classList.add("active");
  document.querySelector(`.nav-btn[data-view="${vista}"]`).classList.add("active");
}

async function cargarEstado() {
  estado = await api("/api/estado");
  pintarProveedores();
  pintarModelos();
  pintarClaves();
  pintarCajaProveedor();
}

/* ---------------- ajustes ---------------- */

function pintarProveedores() {
  const cont = $("provider-list");
  cont.innerHTML = "";
  const NOMBRES = {
    ollama: "🖥️ Ollama (local)",
    gemini: "🔮 Google Gemini",
    groq: "⚡ Groq",
    openrouter: "🌐 OpenRouter",
  };
  for (const [pid, info] of Object.entries(estado.proveedores)) {
    const div = document.createElement("div");
    div.className = "provider-item" + (estado.proveedor === pid ? " sel" : "");
    const tieneClave = estado.claves[pid] || pid === "ollama";
    div.innerHTML = `
      <h4>${NOMBRES[pid]}</h4>
      <p>${esc(info.info)}</p>
      <span class="badge">${tieneClave ? "✔ listo" : "sin clave"}</span>`;
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
      ? "(Ollama no responde — ¿lo tienes abierto? Instálalo en ollama.com)"
      : "(sin modelos disponibles)";
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
  for (const [pid, info] of Object.entries(estado.proveedores)) {
    if (pid === "ollama") continue; // local: no necesita clave
    const row = document.createElement("div");
    row.className = "key-row";
    const tiene = estado.claves[pid];
    row.innerHTML = `
      <label>${pid}</label>
      <input type="password" class="key-input" placeholder="${tiene ? "•••••••• (guardada)" : "pega tu clave aquí"}"
             data-provider="${pid}">
      <button data-save="${pid}">Guardar</button>
      <span class="key-status ${tiene ? "ok" : ""}" id="ks-${pid}">${tiene ? "✔ guardada" : ""}</span>`;
    row.querySelector(`[data-save="${pid}"]`).onclick = async () => {
      const input = row.querySelector(".key-input");
      const valor = input.value.trim();
      if (!valor) { toast("Escribe la clave primero"); return; }
      await api("/api/clave", { method: "POST", body: JSON.stringify({ provider: pid, key: valor }) });
      input.value = "";
      const ks = row.querySelector(".key-status");
      ks.textContent = "✔ guardada";
      ks.className = "key-status ok";
      toast("Clave de " + pid + " guardada");
      await cargarEstado();
    };
    cont.appendChild(row);
  }
}

function pintarCajaProveedor() {
  const info = estado.proveedores[estado.proveedor];
  $("provider-name").textContent = info ? ({
    ollama: "Ollama (local)", gemini: "Google Gemini", groq: "Groq", openrouter: "OpenRouter",
  })[estado.proveedor] : estado.proveedor;
  $("provider-model").textContent = estado.modelo || "";
  $("provider-dot").className = "dot" + (estado.proveedor === "ollama" && estado.ollama_activo ? " on" : "");
}

async function seleccionarProveedor(pid) {
  const sel = $("select-modelo");
  const modelos = estado.proveedores[pid].modelos;
  const modelo = modelos.length ? modelos[0].id : (sel.value || "");
  await api("/api/modelo", { method: "POST", body: JSON.stringify({ provider: pid, model: modelo }) });
  estado.proveedor = pid;
  estado.modelo = modelo;
  await cargarEstado();
  toast("Proveedor: " + pid);
}

/* ---------------- chat ---------------- */

function addMsg(role, texto) {
  const cont = $("messages");
  const div = document.createElement("div");
  div.className = "msg " + (role === "user" ? "user" : role === "error" ? "error" : "assistant");
  div.textContent = texto;
  cont.appendChild(div);
  cont.scrollTop = cont.scrollHeight;
  return div;
}

function indicadorEscribiendo() {
  const cont = $("messages");
  const div = document.createElement("div");
  div.className = "msg assistant";
  div.textContent = "…";
  cont.appendChild(div);
  cont.scrollTop = cont.scrollHeight;
  return div;
}

function redimensionar(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 160) + "px";
}

async function enviar() {
  const input = $("input");
  const texto = input.value.trim();
  if (!texto || $("btn-send").disabled) return;

  addMsg("user", texto);
  historial.push({ role: "user", content: texto });
  input.value = "";
  redimensionar(input);

  const spinner = indicadorEscribiendo();
  $("btn-send").disabled = true;

  try {
    const res = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ messages: historial }),
    });
    spinner.remove();
    if (res.error) {
      addMsg("error", "⚠️ " + res.error);
    } else {
      addMsg("assistant", res.respuesta);
      historial.push({ role: "assistant", content: res.respuesta });
    }
  } catch (e) {
    spinner.remove();
    addMsg("error", "⚠️ No se pudo conectar con el servidor. ¿Está arrancado?");
  } finally {
    $("btn-send").disabled = false;
    input.focus();
  }
}

/* ---------------- memoria ---------------- */

async function cargarMemoria() {
  const res = await api("/api/memoria");
  $("memoria-contenido").textContent = res.contenido || "(vacía — MiClaw aún no sabe nada de ti)";
}

/* ---------------- init ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".nav-btn").forEach((b) => {
    b.onclick = () => {
      switchView(b.dataset.view);
      if (b.dataset.view === "memoria") cargarMemoria();
    };
  });

  $("btn-nueva").onclick = () => {
    historial = [];
    $("messages").innerHTML = "";
    addMsg("assistant", "Nueva conversación. ¿En qué te ayudo?");
  };

  $("chat-form").onsubmit = (e) => { e.preventDefault(); enviar(); };

  const ta = $("input");
  ta.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviar(); }
  });
  ta.addEventListener("input", () => redimensionar(ta));

  $("btn-borrar-memoria").onclick = async () => {
    if (!confirm("¿Seguro que quieres borrar TODA la memoria de MiClaw?")) return;
    await api("/api/memoria", { method: "DELETE" });
    cargarMemoria();
    toast("Memoria borrada");
  };

  cargarEstado().then(() => {
    addMsg("assistant", "¡Hola! Soy MiClaw 🦞\n\nEscribe tu primer mensaje. Recuerda que puedes pedirme buscar en internet (por ejemplo: «busca en internet las mejores ofertas de portátiles») o guardar notas («recuerda que mi cumpleaños es el 3 de mayo»).");
  });
});

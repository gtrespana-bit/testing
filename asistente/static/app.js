/* MiClaw — frontend */

const $ = (id) => document.getElementById(id);

let estado = null;
let historial = [];
let pendiente = null;   // plan de acción sobre el PC esperando aprobación

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
  t._timer = setTimeout(() => t.classList.remove("show"), 3000);
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
  pintarCustom();
  $("pc-carpeta").value = estado.pc.carpeta_extra || "";
}

/* ---------------- ajustes ---------------- */

function pintarProveedores() {
  const cont = $("provider-list");
  cont.innerHTML = "";
  for (const [pid, info] of Object.entries(estado.proveedores)) {
    const div = document.createElement("div");
    div.className = "provider-item" + (estado.proveedor === pid ? " sel" : "");
    const lista = info.tipo === "clave" ? Boolean(estado.claves[pid]) : true;
    div.innerHTML = `
      <h4>${esc(info.nombre)}</h4>
      <p>${esc(info.info)}</p>
      <span class="badge">${lista ? "✔ listo" : "sin clave"}</span>`;
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
    if (info.tipo !== "clave") continue; // ollama es local
    const row = document.createElement("div");
    row.className = "key-row";
    const tiene = estado.claves[pid];
    row.innerHTML = `
      <label title="${esc(info.nombre)}">${pid}</label>
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
  $("provider-name").textContent = info ? info.nombre : estado.proveedor;
  $("provider-model").textContent = estado.modelo || "";
  $("provider-dot").className = "dot" + (estado.proveedor === "ollama" && estado.ollama_activo ? " on" : "");
}

function pintarCustom() {
  $("custom-url").value = estado.custom.base_url || "";
  $("custom-modelos").value = (estado.custom.modelos || []).join("\n");
  $("card-custom").style.display = estado.proveedor === "custom" ? "" : "none";
}

async function seleccionarProveedor(pid) {
  const sel = $("select-modelo");
  const modelos = estado.proveedores[pid].modelos;
  const modelo = modelos.length ? modelos[0].id : (sel.value || "");
  await api("/api/modelo", { method: "POST", body: JSON.stringify({ provider: pid, model: modelo }) });
  estado.proveedor = pid;
  estado.modelo = modelo;
  await cargarEstado();
  toast("Proveedor: " + estado.proveedores[pid].nombre);
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

/* Tarjeta de confirmación para acciones sobre el PC */
function tarjetaPermiso(plan) {
  const cont = $("messages");
  const div = document.createElement("div");
  div.className = "msg permiso";

  const titulos = {
    ver: "👀 Leer archivo",
    escribir: "✍️ Escribir archivo",
    terminal: "💻 Ejecutar comando",
    apuntes: "🧠 Leer apuntes",
  };
  let detalle = "";
  if (plan.accion === "ver") detalle = esc(String(plan.datos || ""));
  if (plan.accion === "terminal") detalle = esc(String(plan.datos || ""));
  if (plan.accion === "escribir" && plan.datos && plan.datos.ruta) {
    detalle = "RUTA: " + esc(plan.datos.ruta) + "\n\n" + esc(String(plan.datos.contenido || "").slice(0, 400));
  }
  if (plan.accion === "apuntes") detalle = "Mostrar los apuntes guardados";

  div.innerHTML = `
    <div class="permiso-titulo">${titulos[plan.accion] || plan.accion} — ¿lo apruebas?</div>
    <pre class="permiso-detalle">${detalle || "(sin datos)"}</pre>
    <div class="permiso-botones">
      <button class="btn-ok" id="permiso-si">✔ Aprobar</button>
      <button class="btn-no" id="permiso-no">✖ Rechazar</button>
    </div>`;
  cont.appendChild(div);
  cont.scrollTop = cont.scrollHeight;
  return div;
}

async function enviar() {
  const input = $("input");
  const texto = input.value.trim();
  if (!texto || $("btn-send").disabled) return;

  addMsg("user", texto);
  historial.push({ role: "user", content: texto });
  input.value = "";
  redimensionar(input);
  await pedirRespuesta();
}

async function pedirRespuesta() {
  const spinner = indicadorEscribiendo();
  $("btn-send").disabled = true;
  try {
    const body = { messages: historial };
    if (pendiente && pendiente.resultado) {
      body.tool_result = pendiente.resultado;
      pendiente = null;
    }
    const res = await api("/api/chat", { method: "POST", body: JSON.stringify(body) });
    spinner.remove();

    if (res.tipo === "error") {
      addMsg("error", "⚠️ " + res.texto);
    } else if (res.tipo === "permiso") {
      pendiente = { accion: res.accion, datos: res.datos, resultado: null };
      const card = tarjetaPermiso(res);
      card.querySelector("#permiso-si").onclick = async () => {
        card.remove();
        const ejec = await api("/api/pc/ejecutar", {
          method: "POST",
          body: JSON.stringify({ accion: res.accion, datos: res.datos }),
        });
        historial.push({ role: "assistant", content: res.texto });
        pendiente = { resultado: ejec.resultado };
        addMsg("toolnote", "✔ Acción aprobada y ejecutada.");
        await pedirRespuesta();
      };
      card.querySelector("#permiso-no").onclick = async () => {
        card.remove();
        historial.push({ role: "assistant", content: res.texto });
        pendiente = { resultado: "El usuario RECHAZÓ la acción. No la ejecutes. Pregúntale si quiere otra cosa." };
        addMsg("toolnote", "✖ Acción rechazada.");
        await pedirRespuesta();
      };
    } else {
      addMsg("assistant", res.texto);
      historial.push({ role: "assistant", content: res.texto });
    }
  } catch (e) {
    spinner.remove();
    addMsg("error", "⚠️ No se pudo conectar con el servidor. ¿Está arrancado?");
  } finally {
    $("btn-send").disabled = false;
    $("input").focus();
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
    pendiente = null;
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

  $("btn-custom").onclick = async () => {
    const modelos = $("custom-modelos").value.split("\n").map((s) => s.trim()).filter(Boolean);
    await api("/api/custom", {
      method: "POST",
      body: JSON.stringify({ base_url: $("custom-url").value.trim(), modelos }),
    });
    toast("Proveedor personalizado guardado");
    await cargarEstado();
  };

  $("btn-pc-config").onclick = async () => {
    await api("/api/pc/config", {
      method: "POST",
      body: JSON.stringify({ carpeta_extra: $("pc-carpeta").value.trim() }),
    });
    toast("Carpeta permitida guardada");
  };

  cargarEstado().then(() => {
    addMsg("assistant", "¡Hola! Soy MiClaw 🦞\n\nPuedo chatear contigo, buscar en internet, guardar notas, y también tocar tu PC (leer/escribir archivos, ejecutar comandos) — siempre pidiéndote permiso antes.\n\nPrueba: «busca en internet…», «recuerda que…», «mira qué hay en mi carpeta Descargas», «crea un archivo notas.txt con una lista de la compra».");
  });
});

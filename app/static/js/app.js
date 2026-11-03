// CodificaMed v1.0 - Logica Frontend JavaScript

let casosEjemplo = [];
let ultimoResultado = null;

// Control de concurrencia y cronometros
let inferenciaEnCurso = false;
let cronometroInterval = null;
let cronometroInicio = null;

function iniciarCronometro(elementoId) {
  detenerCronometro();
  const el = document.getElementById(elementoId);
  if (!el) return;
  cronometroInicio = Date.now();
  el.innerText = "0.0 s";
  cronometroInterval = setInterval(() => {
    const s = ((Date.now() - cronometroInicio) / 1000).toFixed(1);
    el.innerText = `${s} s`;
  }, 100);
}

function detenerCronometro() {
  if (cronometroInterval) {
    clearInterval(cronometroInterval);
    cronometroInterval = null;
  }
}

function bloquearAccionesInferencia() {
  inferenciaEnCurso = true;
  const btnCod = document.getElementById("btnCodificar");
  const btnComp = document.getElementById("btnEjecutarComparacion");
  const btnEval = document.getElementById("btnEjecutarEvaluacion");
  if (btnCod) btnCod.disabled = true;
  if (btnComp) btnComp.disabled = true;
  if (btnEval) btnEval.disabled = true;
}

function liberarAccionesInferencia() {
  inferenciaEnCurso = false;
  detenerCronometro();
  const btnCod = document.getElementById("btnCodificar");
  const btnComp = document.getElementById("btnEjecutarComparacion");
  const btnEval = document.getElementById("btnEjecutarEvaluacion");
  if (btnCod) btnCod.disabled = false;
  if (btnComp) btnComp.disabled = false;
  if (btnEval) btnEval.disabled = false;
}

// Almacenamiento reactivo de credenciales en navegador
const apiKeys = {
  gemini: localStorage.getItem("codificamed_key_gemini") || "",
  openai: localStorage.getItem("codificamed_key_openai") || "",
  claude: localStorage.getItem("codificamed_key_claude") || "",
};

const nombresProv = {
  ollama: "Ollama Local",
  gemini: "Google Gemini",
  openai: "OpenAI ChatGPT",
  claude: "Anthropic Claude",
};

const placeholders = {
  gemini: "Ingresa tu clave de API...",
  openai: "Ingresa tu clave de API...",
  claude: "Ingresa tu clave de API...",
};

// Inicializacion general al cargar DOM
document.addEventListener("DOMContentLoaded", () => {
  inicializarTabs();
  cargarConfiguracion();
  cargarCasosEjemplo();
  cargarCatalogo();

  cambiarProveedorTab1();
  cambiarProveedorComparacion();
  cambiarProveedorEvaluacion();
  actualizarIndicadorClavesGlobal();

  const txtArea = document.getElementById("inputNotaClinica");
  if (txtArea) {
    txtArea.addEventListener("input", actualizarContador);
  }
});

// -------------------------------------------------------------
// Pestañas (Tabs)
// -------------------------------------------------------------
function inicializarTabs() {
  const botones = document.querySelectorAll(".tab-button");
  botones.forEach((btn) => {
    btn.addEventListener("click", () => {
      botones.forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((c) => c.classList.remove("active"));

      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      const target = document.getElementById(tabId);
      if (target) target.classList.add("active");
    });
  });
}

// -------------------------------------------------------------
// Gestion de Claves de API
// -------------------------------------------------------------
function guardarClaveEnTiempoReal(prov, valor) {
  if (!prov || prov === "ollama") return;
  const valLimpio = (valor || "").trim();
  apiKeys[prov] = valLimpio;
  try {
    localStorage.setItem(`codificamed_key_${prov}`, valLimpio);
  } catch (e) {
    console.warn("Error guardando credenciales locales", e);
  }
  sincronizarUIsClaves(prov);
  actualizarIndicadorClavesGlobal();
}

function sincronizarUIsClaves(prov) {
  const activa = (apiKeys[prov] || "").length > 5;
  const textoEstado = activa ? "Configurada" : "No configurada";
  const claseEstado = activa ? "status-pill status-ok" : "status-pill status-warn";

  // Sincroniza estado en Pestaña 1
  const provActualTab1 = document.getElementById("selectProveedor")?.value;
  if (provActualTab1 === prov) {
    const badge1 = document.getElementById("badgeClaveTab1");
    if (badge1) {
      badge1.innerText = textoEstado;
      badge1.className = claseEstado;
    }
    const input1 = document.getElementById("inputClaveTab1");
    if (input1 && document.activeElement !== input1) {
      input1.value = apiKeys[prov] || "";
    }
  }

  // Sincroniza estado en Pestaña 2
  const provActualComp = document.getElementById("compApiProv")?.value;
  if (provActualComp === prov) {
    const badge2 = document.getElementById("compBadgeApiKey");
    if (badge2) {
      badge2.innerText = textoEstado;
      badge2.className = claseEstado;
    }
    const input2 = document.getElementById("compApiKeyInput");
    if (input2 && document.activeElement !== input2) {
      input2.value = apiKeys[prov] || "";
    }
  }

  // Sincroniza estado en Pestaña 3
  const provActualEval = document.getElementById("evalProveedor")?.value;
  if (provActualEval === prov) {
    const badge3 = document.getElementById("evalBadgeApiKey");
    if (badge3) {
      badge3.innerText = textoEstado;
      badge3.className = claseEstado;
    }
    const input3 = document.getElementById("evalApiKeyInput");
    if (input3 && document.activeElement !== input3) {
      input3.value = apiKeys[prov] || "";
    }
  }

  // Sincroniza estado en ventana modal
  const mapModal = {
    gemini: { input: "keyModalGemini", badge: "badgeModalGemini" },
    openai: { input: "keyModalOpenai", badge: "badgeModalOpenai" },
    claude: { input: "keyModalClaude", badge: "badgeModalClaude" },
  };
  if (mapModal[prov]) {
    const elInp = document.getElementById(mapModal[prov].input);
    const elBdg = document.getElementById(mapModal[prov].badge);
    if (elInp && document.activeElement !== elInp) {
      elInp.value = apiKeys[prov] || "";
    }
    if (elBdg) {
      elBdg.innerText = textoEstado;
      elBdg.className = claseEstado;
    }
  }
}

function actualizarIndicadorClavesGlobal() {
  const dot = document.getElementById("headerApiKeyDot");
  if (!dot) return;
  const tieneClaves = ["gemini", "openai", "claude"].some(
    (p) => (apiKeys[p] || "").length > 5
  );
  dot.classList.toggle("active", tieneClaves);
  dot.title = tieneClaves
    ? "Credenciales de API configuradas"
    : "Sin credenciales de API externas";
}

function toggleVisibilidadClave(inputId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const esPassword = input.type === "password";
  input.type = esPassword ? "text" : "password";

  const btn = input.parentElement?.querySelector(".btn-toggle-eye");
  if (btn) {
    btn.innerText = esPassword ? "Ocultar" : "Ver";
  }
}

function abrirModalApiKeys() {
  const modal = document.getElementById("modalApiKeys");
  if (!modal) return;
  modal.style.display = "flex";

  ["gemini", "openai", "claude"].forEach((prov) => {
    sincronizarUIsClaves(prov);
  });
}

function cerrarModalApiKeys() {
  const modal = document.getElementById("modalApiKeys");
  if (modal) modal.style.display = "none";
}

function cerrarModalAlFondo(event) {
  if (event.target.id === "modalApiKeys") {
    cerrarModalApiKeys();
  }
}

// -------------------------------------------------------------
// Reactividad de Proveedores en Pestañas
// -------------------------------------------------------------
function cambiarProveedorTab1() {
  const prov = document.getElementById("selectProveedor").value;
  const container = document.getElementById("contenedorProveedorInfo");
  if (!container) return;

  if (prov === "ollama") {
    container.innerHTML = `
      <div class="field-label-row">
        <label>Estado del Motor Local:</label>
        <span class="status-pill status-ok">Listo</span>
      </div>
      <div class="static-control-display">
        <span class="status-indicator" style="background: #10b981;"></span>
        <span class="static-control-title" id="txtDetalleOllama">Ollama Local activo · No requiere clave de API</span>
      </div>
    `;
  } else {
    const activa = (apiKeys[prov] || "").length > 5;
    container.innerHTML = `
      <div class="field-label-row">
        <label id="lblClaveTab1" for="inputClaveTab1">Clave de API (${nombresProv[prov]}):</label>
        <span id="badgeClaveTab1" class="status-pill ${activa ? "status-ok" : "status-warn"}">
          ${activa ? "Configurada" : "No configurada"}
        </span>
      </div>
      <div class="api-key-input-row">
        <input type="password" id="inputClaveTab1" value="${apiKeys[prov] || ""}"
               placeholder="${placeholders[prov]}"
               oninput="guardarClaveEnTiempoReal('${prov}', this.value)">
        <button type="button" class="btn-toggle-eye" onclick="toggleVisibilidadClave('inputClaveTab1')">Ver</button>
      </div>
    `;
  }
}

function cambiarProveedorComparacion() {
  const prov = document.getElementById("compApiProv").value;
  const lbl = document.getElementById("compLblApiKey");
  const badge = document.getElementById("compBadgeApiKey");
  const input = document.getElementById("compApiKeyInput");

  if (lbl) lbl.innerText = `Clave de API (${nombresProv[prov]}):`;
  if (input) {
    input.value = apiKeys[prov] || "";
    input.placeholder = placeholders[prov];
  }
  if (badge) {
    const activa = (apiKeys[prov] || "").length > 5;
    badge.innerText = activa ? "Configurada" : "No configurada";
    badge.className = `status-pill ${activa ? "status-ok" : "status-warn"}`;
  }
}

function cambiarProveedorEvaluacion() {
  const prov = document.getElementById("evalProveedor").value;
  const container = document.getElementById("evalApiKeyBox");
  if (!container) return;

  if (prov === "ollama") {
    container.innerHTML = `
      <div class="field-label-row">
        <label>Estado del Motor Local:</label>
        <span class="status-pill status-ok">Listo</span>
      </div>
      <div class="static-control-display">
        <span class="status-indicator" style="background: #10b981;"></span>
        <span class="static-control-title">Ollama Local activo · No requiere clave de API</span>
      </div>
    `;
  } else {
    const activa = (apiKeys[prov] || "").length > 5;
    container.innerHTML = `
      <div class="field-label-row">
        <label id="evalLblApiKey" for="evalApiKeyInput">Clave de API (${nombresProv[prov]}):</label>
        <span id="evalBadgeApiKey" class="status-pill ${activa ? "status-ok" : "status-warn"}">
          ${activa ? "Configurada" : "No configurada"}
        </span>
      </div>
      <div class="api-key-input-row">
        <input type="password" id="evalApiKeyInput" value="${apiKeys[prov] || ""}"
               placeholder="${placeholders[prov]}"
               oninput="guardarClaveEnTiempoReal('${prov}', this.value)">
        <button type="button" class="btn-toggle-eye" onclick="toggleVisibilidadClave('evalApiKeyInput')">Ver</button>
      </div>
    `;
  }
}

// -------------------------------------------------------------
// Carga de Configuracion Inicial
// -------------------------------------------------------------
async function cargarConfiguracion() {
  try {
    const res = await fetch("/api/config");
    const data = await res.json();

    const pill = document.getElementById("statusOllama");
    const text = document.getElementById("statusOllamaText");

    if (data.ollama && data.ollama.disponible) {
      pill.className = "status-pill status-ok";
      text.innerText = `Ollama: ${data.ollama.modelo} listo`;

      const compBadge = document.getElementById("compLocalModelBadge");
      if (compBadge && data.ollama.modelo) {
        compBadge.innerText = data.ollama.modelo;
      }

      const compHint = document.getElementById("compLocalHint");
      if (compHint) compHint.innerText = `Modelo activo: ${data.ollama.modelo}`;

      const txtDetalle = document.getElementById("txtDetalleOllama");
      if (txtDetalle) {
        txtDetalle.innerText = `Servicio local activo (Ollama: ${data.ollama.modelo}).`;
      }
    } else if (data.ollama && data.ollama.modelos_instalados && data.ollama.modelos_instalados.length > 0) {
      pill.className = "status-pill status-warn";
      text.innerText = `Ollama: Activo (${data.ollama.modelos_instalados[0]})`;
    } else if (data.ollama && data.ollama.mensaje) {
      pill.className = "status-pill status-warn";
      text.innerText = data.ollama.mensaje;
    } else {
      pill.className = "status-pill status-warn";
      text.innerText = "Ollama: Servicio no detectado";
    }

    // Registra claves provistas por entorno de servidor
    ["gemini", "openai", "claude"].forEach((p) => {
      if (!apiKeys[p] && data[p] && data[p].configurado) {
        apiKeys[p] = "configured_in_server";
        sincronizarUIsClaves(p);
      }
    });
    actualizarIndicadorClavesGlobal();
  } catch (err) {
    console.warn("Fallo al obtener configuracion del servidor", err);
  }
}

// -------------------------------------------------------------
// Casos Clinicos de Prueba Predeterminados
// -------------------------------------------------------------
async function cargarCasosEjemplo() {
  try {
    const res = await fetch("/api/casos-ejemplo");
    casosEjemplo = await res.json();
    if (casosEjemplo.length > 0) {
      cargarCasoEjemplo(0);
    }
  } catch (err) {
    console.warn("Fallo al cargar casos de prueba", err);
  }
}

function cargarCasoEjemplo(index) {
  if (casosEjemplo && casosEjemplo[index]) {
    const txtArea = document.getElementById("inputNotaClinica");
    txtArea.value = casosEjemplo[index].texto;
    actualizarContador();
    txtArea.scrollIntoView({ behavior: "smooth", block: "center" });

    // Actualiza estilo activo en botones de casos
    document.querySelectorAll(".btn-preset").forEach((b, i) => {
      b.classList.toggle("active", i === index);
    });
  }
}

function actualizarContador() {
  const txtArea = document.getElementById("inputNotaClinica");
  const countEl = document.getElementById("charCount");
  if (!txtArea || !countEl) return;
  const text = txtArea.value.trim();
  const palabras = text ? text.split(/\s+/).length : 0;
  countEl.innerText = `${text.length} caracteres | ${palabras} palabras`;
}

function limpiarTexto() {
  const txtArea = document.getElementById("inputNotaClinica");
  if (txtArea) txtArea.value = "";
  actualizarContador();
  const sec = document.getElementById("sectionResultados");
  if (sec) sec.style.display = "none";
}

// -------------------------------------------------------------
// Ejecutar Codificacion de la Nota (Pestaña 1)
// -------------------------------------------------------------
async function ejecutarCodificacion() {
  if (inferenciaEnCurso) {
    mostrarToast("Ya hay un proceso de inferencia activo. Espera a que finalice para no sobrecargar la GPU/CPU.", "error");
    return;
  }

  const texto = document.getElementById("inputNotaClinica").value.trim();
  if (!texto || texto.length < 5) {
    mostrarToast("Por favor, ingresa o carga una nota clínica antes de codificar.", "error");
    return;
  }

  const proveedor = document.getElementById("selectProveedor").value;
  const apiKey = apiKeys[proveedor] || "";

  if (proveedor !== "ollama" && !apiKey) {
    mostrarToast(`Ingresa la clave de API para ${nombresProv[proveedor]} antes de analizar.`, "error");
    return;
  }

  const status = document.getElementById("pipelineStatus");
  const statusText = document.getElementById("pipelineStatusText");
  const secResultados = document.getElementById("sectionResultados");

  bloquearAccionesInferencia();
  status.style.display = "flex";
  statusText.innerText = `Analizando nota clínica con ${nombresProv[proveedor]}...`;
  iniciarCronometro("pipelineTime");
  if (secResultados) secResultados.style.display = "none";

  try {
    const res = await fetch("/api/codificar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        texto: texto,
        proveedor: proveedor,
        api_key: apiKey === "configured_in_server" ? null : apiKey || null,
        modelo: null,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Error HTTP ${res.status}`);
    }

    const data = await res.json();
    ultimoResultado = data;
    renderizarResultados(data);
    mostrarToast("Codificación clínica completada con éxito.", "success");
  } catch (err) {
    mostrarToast(`Error al procesar: ${err.message}`, "error");
  } finally {
    liberarAccionesInferencia();
    status.style.display = "none";
  }
}

// -------------------------------------------------------------
// Renderizado de Resultados Clinicos
// -------------------------------------------------------------
function renderizarResultados(data) {
  const sec = document.getElementById("sectionResultados");
  if (!sec) return;
  sec.style.display = "block";

  const resumenEl = document.getElementById("clinicalSummaryText");
  if (resumenEl) {
    resumenEl.innerText = data.resumen_clinico || "Nota procesada con éxito.";
  }

  const m = data.metricas_asercion || {};
  const diags = data.diagnosticos || [];

  const elTot = document.getElementById("metricTotal");
  if (elTot) elTot.innerText = diags.length;

  const elConf = document.getElementById("metricConfirmados");
  if (elConf) elConf.innerText = m.total_confirmados || 0;

  const elNeg = document.getElementById("metricNegados");
  if (elNeg) elNeg.innerText = m.total_negados || 0;

  const elSosp = document.getElementById("metricSospechas");
  if (elSosp) elSosp.innerText = m.total_sospechas || 0;

  const elTiempo = document.getElementById("metricTiempo");
  if (elTiempo) elTiempo.innerText = `${data.tiempos?.duracion_total_s || 0}s`;

  const elTokens = document.getElementById("metricTokensTab1");
  if (elTokens) {
    const tks = data.tokens_estimados || 180;
    const esLocal = data.proveedor_usado === "ollama";
    elTokens.innerText = `~${tks} tokens · ${esLocal ? "Local" : "Nube"}`;
  }

  const badgeCount = document.getElementById("diagnosesCountBadge");
  if (badgeCount) {
    badgeCount.innerText = `${diags.length} diagnósticos asignados`;
  }

  const textoOriginal = data.texto_original || document.getElementById("inputNotaClinica")?.value || "";
  renderizarTextoAnotado(textoOriginal, diags);
  renderizarTarjetasDiagnosticos(diags);

  sec.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderizarTextoAnotado(texto, diagnosticos) {
  const container = document.getElementById("annotatedText");
  if (!container) return;
  if (!texto || texto.trim().length === 0) {
    container.innerHTML = `<p style="color: var(--text-muted); font-style: italic;">No se encontró texto clínico para marcar evidencia.</p>`;
    return;
  }
  if (!diagnosticos || diagnosticos.length === 0) {
    container.innerText = texto;
    return;
  }

  let html = escaparHtml(texto);

  diagnosticos.forEach((d) => {
    if (!d.evidencia) return;
    const evLimpia = d.evidencia.trim();
    if (evLimpia.length < 3) return;

    const regex = new RegExp(`(${escaparRegex(evLimpia)})`, "gi");
    const claseHighlight =
      d.estado === "CONFIRMADO"
        ? "hl-confirmado"
        : d.estado === "NEGADO"
        ? "hl-negado"
        : "hl-sospecha";

    html = html.replace(
      regex,
      `<mark class="${claseHighlight}" data-codigo="${d.codigo}" title="Código: ${d.codigo} (${d.estado})">$1</mark>`
    );
  });

  container.innerHTML = html;

  // Asigna eventos bidireccionales al texto anotado
  container.querySelectorAll("mark").forEach((m) => {
    const cod = m.getAttribute("data-codigo");
    m.addEventListener("mouseenter", () => {
      activarResaltadoBidireccional(cod);
      const card = document.querySelector(`.diag-card[data-codigo="${cod}"]`);
      if (card) {
        card.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    });
    m.addEventListener("mouseleave", () => {
      desactivarResaltadoBidireccional();
    });
  });
}

function renderizarTarjetasDiagnosticos(diagnosticos) {
  const container = document.getElementById("diagnosesList");
  if (!container) return;
  container.innerHTML = "";

  if (!diagnosticos || diagnosticos.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>No se identificaron códigos CIE-10 para esta nota.</p>
      </div>
    `;
    return;
  }

  diagnosticos.forEach((d) => {
    const card = document.createElement("div");
    card.className = "diag-card";
    card.setAttribute("data-codigo", d.codigo);

    const badgeClass =
      d.estado === "CONFIRMADO"
        ? "badge-confirmado"
        : d.estado === "NEGADO"
        ? "badge-negado"
        : "badge-sospecha";

    card.innerHTML = `
      <div class="diag-header">
        <span class="diag-code">${d.codigo}</span>
        <span class="badge ${badgeClass}">${d.estado}</span>
      </div>
      <div class="diag-desc">${d.descripcion}</div>
      <div class="diag-meta">
        <strong>Justificación:</strong> ${d.justificacion || "Asignado por concordancia clínica"}
      </div>
      ${
        d.evidencia
          ? `<div class="diag-evidence"><strong>Evidencia textual:</strong> "${escaparHtml(d.evidencia)}"</div>`
          : ""
      }
    `;

    card.addEventListener("mouseenter", () => activarResaltadoBidireccional(d.codigo));
    card.addEventListener("mouseleave", () => desactivarResaltadoBidireccional());

    container.appendChild(card);
  });
}

function activarResaltadoBidireccional(codigo) {
  if (!codigo) return;
  document.querySelectorAll(`#annotatedText mark[data-codigo="${codigo}"]`).forEach((m) => {
    m.classList.add("active-highlight");
  });
  document.querySelectorAll(`.diag-card[data-codigo="${codigo}"]`).forEach((c) => {
    c.classList.add("active-card");
  });
}

function desactivarResaltadoBidireccional() {
  document.querySelectorAll("#annotatedText mark").forEach((m) => {
    m.classList.remove("active-highlight");
  });
  document.querySelectorAll(".diag-card").forEach((c) => {
    c.classList.remove("active-card");
  });
}

// -------------------------------------------------------------
// Acciones de Exportacion Formal
// -------------------------------------------------------------
function copiarJson() {
  if (!ultimoResultado) {
    mostrarToast("No hay resultados disponibles para copiar.", "error");
    return;
  }
  const jsonStr = JSON.stringify(ultimoResultado, null, 2);
  navigator.clipboard.writeText(jsonStr).then(() => {
    mostrarToast("Estructura JSON copiada al portapapeles.", "success");
  }).catch(() => {
    mostrarToast("Error al copiar JSON al portapapeles.", "error");
  });
}

function exportarInforme() {
  if (!ultimoResultado) {
    mostrarToast("No hay resultados disponibles para exportar.", "error");
    return;
  }
  const fecha = new Date().toLocaleString("es-EC", { dateStyle: "full", timeStyle: "medium" });
  const prov = ultimoResultado.proveedor_usado || "Ollama Local";
  const modelo = ultimoResultado.modelo_usado || "llama3.1:latest";
  const duracion = ultimoResultado.tiempos?.duracion_total_s || 0;
  const m = ultimoResultado.metricas_asercion || {};
  const diags = ultimoResultado.diagnosticos || [];

  let md = `# CodificaMed v1.0 - Informe Clínico de Codificación CIE-10\n\n`;
  md += `- **Fecha y Hora de Emisión:** ${fecha}\n`;
  md += `- **Motor de Inteligencia Artificial:** ${prov} (\`${modelo}\`)\n`;
  md += `- **Tiempo de Procesamiento:** ${duracion} segundos\n`;
  md += `- **Métricas de Aserción:** Total: ${diags.length} | Confirmados: ${m.total_confirmados || 0} | Negados: ${m.total_negados || 0} | Sospechas: ${m.total_sospechas || 0}\n\n`;
  md += `## 1. Síntesis Clínica Estructurada\n\n${ultimoResultado.resumen_clinico || "Sin resumen disponible."}\n\n`;
  md += `## 2. Diagnósticos Codificados (CIE-10)\n\n`;
  md += `| Código | Estado Clínico | Descripción CIE-10 | Justificación | Evidencia Textual |\n`;
  md += `|:------:|:--------------:|:-------------------|:--------------|:------------------|\n`;

  diags.forEach((d) => {
    const ev = (d.evidencia || "").replace(/\|/g, "\\|");
    const just = (d.justificacion || "").replace(/\|/g, "\\|");
    const desc = (d.descripcion || "").replace(/\|/g, "\\|");
    md += `| **${d.codigo}** | \`${d.estado}\` | ${desc} | ${just} | *"${ev}"* |\n`;
  });

  md += `\n## 3. Texto Original de la Historia Clínica\n\n\`\`\`text\n${ultimoResultado.texto_original || ""}\n\`\`\`\n\n`;
  md += `---\n*Documento generado automáticamente por CodificaMed v1.0 - Escuela Superior Politécnica de Chimborazo (ESPOCH).*\n`;

  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `informe_codificacion_${Date.now()}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  mostrarToast("Informe clínico descargado en formato Markdown.", "success");
}

function mostrarToast(mensaje, tipo = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;

  // Evita apilamiento limpiando notificaciones previas
  container.innerHTML = "";

  const toast = document.createElement("div");
  toast.className = `toast toast-${tipo}`;

  let icono = "";
  if (tipo === "success") {
    icono = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"/></svg>`;
  } else if (tipo === "error") {
    icono = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
  } else {
    icono = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
  }

  toast.innerHTML = `${icono}<span>${escaparHtml(mensaje)}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(8px)";
    toast.style.transition = "opacity 200ms ease, transform 200ms ease";
    setTimeout(() => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
    }, 220);
  }, 3200);
}

// -------------------------------------------------------------
// Comparador de Modelos (Pestaña 2)
// -------------------------------------------------------------
async function ejecutarComparacion() {
  if (inferenciaEnCurso) {
    mostrarToast("Ya hay un proceso de inferencia activo. Espera a que finalice para no sobrecargar la GPU/CPU.", "error");
    return;
  }

  const texto = document.getElementById("inputNotaClinica").value.trim();
  if (!texto) {
    mostrarToast("Por favor, ingresa o carga una nota clínica en la pestaña principal.", "error");
    return;
  }

  const provApi = document.getElementById("compApiProv").value;
  const apiKey = apiKeys[provApi] || "";

  if (!apiKey) {
    mostrarToast(`Ingresa la clave de API de ${nombresProv[provApi]} para ejecutar la comparación.`, "error");
    return;
  }

  const progress = document.getElementById("compProgress");
  const results = document.getElementById("compResults");

  bloquearAccionesInferencia();
  progress.style.display = "flex";
  iniciarCronometro("compTime");
  results.style.display = "none";

  try {
    const res = await fetch("/api/comparar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        texto: texto,
        proveedor_local: "ollama",
        modelo_local: null,
        proveedor_api: provApi,
        modelo_api: null,
        api_key_api: apiKey === "configured_in_server" ? null : apiKey || null,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Error HTTP ${res.status}`);
    }
    const data = await res.json();

    renderizarComparacion(data);
    mostrarToast("Comparación completada con éxito.", "success");
  } catch (err) {
    mostrarToast(`Error al comparar: ${err.message}`, "error");
  } finally {
    liberarAccionesInferencia();
    progress.style.display = "none";
  }
}

function renderizarComparacion(data) {
  const strip = document.getElementById("compMetricsStrip");
  const results = document.getElementById("compResults");

  const loc = data.local || {};
  const api = data.api || {};

  const tLoc = Number(loc.tiempos?.duracion_total_s || 0);
  const tApi = Number(api.tiempos?.duracion_total_s || 0);
  const tkLoc = loc.tokens_estimados || 180;
  const tkApi = api.tokens_estimados || 180;

  if (strip) {
    strip.style.display = "grid";
    const elLocTime = document.getElementById("compLocalTimeVal");
    if (elLocTime) elLocTime.innerText = `${tLoc.toFixed(2)}s`;
    const elLocTk = document.getElementById("compLocalTokenVal");
    if (elLocTk) elLocTk.innerText = `~${tkLoc} tokens · ${loc.modelo_usado || "llama3.1"}`;

    const elApiTime = document.getElementById("compApiTimeVal");
    if (elApiTime) elApiTime.innerText = `${tApi.toFixed(2)}s`;
    const elApiTk = document.getElementById("compApiTokenVal");
    if (elApiTk) elApiTk.innerText = `~${tkApi} tokens · ${api.proveedor_usado || "Nube"}`;

    const speedVal = document.getElementById("compSpeedupVal");
    const speedNote = document.getElementById("compSpeedupNote");

    if (speedVal && speedNote) {
      if (tLoc > 0 && tApi > 0) {
        if (tApi < tLoc) {
          const ratio = (tLoc / tApi).toFixed(1);
          speedVal.innerText = `${ratio}x más rápida`;
          speedNote.innerText = "API en la nube completó con menor latencia";
        } else {
          const ratio = (tApi / tLoc).toFixed(1);
          speedVal.innerText = `${ratio}x más rápido`;
          speedNote.innerText = "Motor local completó con menor latencia";
        }
      } else {
        speedVal.innerText = "Completado";
        speedNote.innerText = "Inferencia ejecutada en paralelo";
      }
    }
  }

  results.style.display = "grid";

  const localEl = document.getElementById("compLocalList");
  const localMeta = document.getElementById("compLocalMeta");
  if (localMeta) localMeta.innerText = `${loc.modelo_usado || "llama3.1"} · ${tLoc.toFixed(2)}s · ~${tkLoc} tokens`;
  if (localEl) {
    localEl.innerHTML = loc.error
      ? `<div style="color: #dc2626; padding: 12px; font-size: 13px; background: #fef2f2; border-radius: 6px; border: 1px solid #fecaca;">${escaparHtml(loc.error)}</div>`
      : generarListaDiagnosticosHtml(loc.diagnosticos || []);
  }

  const apiEl = document.getElementById("compApiList");
  const apiMeta = document.getElementById("compApiMeta");
  if (apiMeta) apiMeta.innerText = `${api.proveedor_usado || "API Nube"} · ${tApi.toFixed(2)}s · ~${tkApi} tokens`;
  if (apiEl) {
    apiEl.innerHTML = api.error
      ? `<div style="color: #dc2626; padding: 12px; font-size: 13px; background: #fef2f2; border-radius: 6px; border: 1px solid #fecaca;">${escaparHtml(api.error)}</div>`
      : generarListaDiagnosticosHtml(api.diagnosticos || []);
  }
}

function generarListaDiagnosticosHtml(diags) {
  if (!diags || diags.length === 0) {
    return `<div style="color: #64748b; padding: 12px; font-size: 13px;">Sin diagnósticos detectados.</div>`;
  }
  return diags
    .map((d) => {
      const cls =
        d.estado === "CONFIRMADO"
          ? "badge-confirmado"
          : d.estado === "NEGADO"
          ? "badge-negado"
          : "badge-sospecha";
      return `
      <div style="border-bottom: 1px solid #f1f5f9; padding: 10px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span class="diag-code">${d.codigo}</span>
          <span class="badge ${cls}">${d.estado}</span>
        </div>
        <div style="font-size: 13px; font-weight: 600; margin: 4px 0; color: #0f172a;">${escaparHtml(d.descripcion)}</div>
        <div style="font-size: 12px; color: #475569;">"${escaparHtml(d.evidencia || "")}"</div>
      </div>
    `;
    })
    .join("");
}

// -------------------------------------------------------------
// Evaluacion CRISP-ML(Q) (Pestaña 3)
// -------------------------------------------------------------
async function ejecutarEvaluacion() {
  if (inferenciaEnCurso) {
    mostrarToast("Ya hay un proceso de inferencia activo. Espera a que finalice para no sobrecargar la GPU/CPU.", "error");
    return;
  }

  const prov = document.getElementById("evalProveedor").value;
  const apiKey = apiKeys[prov] || "";

  if (prov !== "ollama" && !apiKey) {
    mostrarToast(`Ingresa la clave de API de ${nombresProv[prov]} antes de evaluar.`, "error");
    return;
  }

  const limite = parseInt(document.getElementById("evalLimite")?.value || "5", 10);
  const progress = document.getElementById("evalProgress");
  const results = document.getElementById("evalResults");

  bloquearAccionesInferencia();
  progress.style.display = "flex";
  iniciarCronometro("evalTime");
  results.style.display = "none";

  try {
    const res = await fetch("/api/evaluar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        proveedor: prov,
        modelo: null,
        api_key: apiKey === "configured_in_server" ? null : apiKey || null,
        limite_casos: limite,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Error HTTP ${res.status}`);
    }
    const data = await res.json();

    const m = data.metricas_globales || {};
    document.getElementById("metricEvalF1").innerText = `${(m.f1_score * 100).toFixed(1)}%`;
    document.getElementById("metricEvalPrecision").innerText = `${(m.precision * 100).toFixed(1)}%`;
    document.getElementById("metricEvalRecall").innerText = `${(m.recall * 100).toFixed(1)}%`;
    document.getElementById("metricEvalAsercion").innerText = `${(m.exactitud_asercion * 100).toFixed(1)}%`;
    document.getElementById("metricEvalLatencia").innerText = `${m.tiempo_promedio_s}s`;

    const elTotalTime = document.getElementById("metricEvalTotalTime");
    if (elTotalTime) {
      elTotalTime.innerText = `${m.tiempo_total_s || 0}s`;
    }

    const tbody = document.getElementById("evalTableBody");
    tbody.innerHTML = "";

    (data.detalles || []).forEach((c) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${c.id}</strong></td>
        <td>${escaparHtml(c.titulo)}</td>
        <td style="text-align: center;"><span style="color: #065f46; font-weight: 600;">${c.tp}</span></td>
        <td style="text-align: center;"><span style="color: #b45309; font-weight: 600;">${c.fp}</span></td>
        <td style="text-align: center;"><span style="color: #b91c1c; font-weight: 600;">${c.fn}</span></td>
        <td style="text-align: center;">${(c.f1_score * 100).toFixed(1)}%</td>
        <td style="text-align: center;">${c.duracion_s}s</td>
      `;
      tbody.appendChild(tr);
    });

    results.style.display = "block";
    results.scrollIntoView({ behavior: "smooth", block: "start" });
    mostrarToast("Evaluación completada con éxito.", "success");
  } catch (err) {
    mostrarToast(`Error al evaluar: ${err.message}`, "error");
  } finally {
    liberarAccionesInferencia();
    progress.style.display = "none";
  }
}

// -------------------------------------------------------------
// Catalogo CIE-10 (Pestaña 4)
// -------------------------------------------------------------
async function cargarCatalogo() {
  try {
    const res = await fetch("/api/catalogo");
    const catalogo = await res.json();
    renderizarCatalogo(catalogo);
  } catch (err) {
    console.warn("Fallo al cargar catálogo CIE-10", err);
  }
}

function renderizarCatalogo(catalogo) {
  const tbody = document.getElementById("catalogoTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const sub = document.getElementById("catalogoCountSubtitle");
  if (sub) {
    sub.innerText = `${catalogo.length} códigos CIE-10 indexados`;
  }

  catalogo.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><span class="diag-code">${item.codigo}</span></td>
      <td><strong>${escaparHtml(item.descripcion)}</strong></td>
      <td><span class="category-pill">${escaparHtml(item.capitulo || "General")}</span></td>
      <td style="font-size: 12px; color: #475569;">${escaparHtml((item.sinonimos || []).join(", "))}</td>
    `;
    tbody.appendChild(tr);
  });
}

function filtrarCatalogo() {
  const query = (document.getElementById("inputBuscarCatalogo")?.value || "").toLowerCase().trim();
  const rows = document.querySelectorAll("#catalogoTableBody tr");
  let visibles = 0;

  rows.forEach((r) => {
    const text = r.innerText.toLowerCase();
    const match = !query || text.includes(query);
    r.style.display = match ? "" : "none";
    if (match) visibles++;
  });

  const sub = document.getElementById("catalogoCountSubtitle");
  if (sub) {
    sub.innerText = query ? `${visibles} códigos encontrados para "${query}"` : `${rows.length} códigos CIE-10 indexados`;
  }
}

// -------------------------------------------------------------
// Utilidades de Escape HTML
// -------------------------------------------------------------
function escaparHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

function escaparRegex(text) {
  return text.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, "\\$&");
}

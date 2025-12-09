// apps/citaciones/static/citaciones/js/pendientes.js
console.log("[PENDIENTES] JS cargado");

// ================= Helpers generales =================

function getCookie(name) {
  const value = `; ${document.cookie}`.split(`; ${name}=`);
  if (value.length === 2) return value.pop().split(";").shift();
}

function showOverlayLocal() {
  if (document.getElementById("ui-lock")) return;
  const ov = document.createElement("div");
  ov.id = "ui-lock";
  ov.innerHTML =
    '<div class="ui-lock__box"><div class="ui-lock__spinner"></div><p>Procesando…</p></div>';
  Object.assign(ov.style, {
    position: "fixed",
    inset: "0",
    zIndex: "9999",
    background: "rgba(255,255,255,.6)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backdropFilter: "saturate(180%) blur(2px)",
  });
  document.body.appendChild(ov);
  document.body.style.overflow = "hidden";
}

function hideOverlayLocal() {
  const ov = document.getElementById("ui-lock");
  if (ov) ov.remove();
  document.body.style.overflow = "";
}

async function postWithTimeout(url, body = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      },
      body: new URLSearchParams(body),
      signal: controller.signal,
      redirect: "manual",
    });
    return resp;
  } finally {
    clearTimeout(timer);
  }
}

// ================= Modal Kárdex =================

function crearModalBase() {
  let modal = document.getElementById("kardex-modal");
  if (modal) modal.remove();

  modal = document.createElement("div");
  modal.id = "kardex-modal";
  Object.assign(modal.style, {
    position: "fixed",
    inset: "0",
    background: "rgba(0,0,0,.45)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: "10000",
  });

  const box = document.createElement("div");
  box.className = "kardex-modal-box";
  Object.assign(box.style, {
    background: "#fff",
    borderRadius: "12px",
    maxWidth: "650px",
    width: "90%",
    padding: "18px 20px",
    boxShadow: "0 10px 30px rgba(0,0,0,.2)",
    fontSize: "0.95rem",
  });

  modal.appendChild(box);
  document.body.appendChild(modal);
  return box;
}

function mostrarModalKardex(data) {
  const box = crearModalBase();
  const { estudiante, registros } = data;

  box.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
      <h3 style="margin:0;font-size:1.2rem;">Registros de Kárdex vinculados</h3>
      <button type="button" id="kardex-modal-close"
              style="border:none;background:none;font-size:1.4rem;cursor:pointer;">×</button>
    </div>
    <p style="margin:0 0 12px 0;">
      <strong>Estudiante:</strong> ${estudiante}
    </p>
    ${
      !registros || !registros.length
        ? '<p style="margin:0;">No hay registros de Kárdex asociados a esta citación.</p>'
        : `
      <div class="kardex-list">
        ${registros
          .map(
            (r) => `
          <div class="kardex-item"
               style="border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;margin-bottom:8px;">
            <div><strong>Fecha:</strong> ${r.fecha}${
              r.hora ? " " + r.hora : ""
            }</div>
            <div><strong>Ítem:</strong> ${r.item}</div>
            <div><strong>Área:</strong> ${r.area} · <strong>Sentido:</strong> ${
              r.sentido
            }</div>
            ${
              r.observacion
                ? `<div><strong>Observación:</strong> ${r.observacion}</div>`
                : ""
            }
            ${
              r.docente ? `<div><strong>Docente:</strong> ${r.docente}</div>` : ""
            }
            ${
              r.sello_maestro
                ? `<div><strong>Validado por maestro:</strong> Sí</div>`
                : ""
            }
          </div>
        `
          )
          .join("")}
      </div>
      `
    }
  `;

  const root = document.getElementById("kardex-modal");
  box.querySelector("#kardex-modal-close").addEventListener("click", () => {
    root && root.remove();
  });
  root.addEventListener("click", (ev) => {
    if (ev.target.id === "kardex-modal") root.remove();
  });
}

// ================= Handlers aprobar / rechazar =================

document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".btn-aprobar, .btn-rechazar");
  if (!btn) return;

  e.preventDefault();
  const id = btn.dataset.id;
  if (!id) return;

  btn.disabled = true;
  showOverlayLocal();

  try {
    const url = btn.classList.contains("btn-aprobar")
      ? `/citaciones/${id}/aprobar/`
      : `/citaciones/${id}/rechazar/`;

    const res = await postWithTimeout(url);
    if (!res || !res.ok) {
      // si algo raro pasa (redirect, 500, etc.) recargamos
      window.location.reload();
      return;
    }

    const data = await res.json();
    if (!data.ok) {
      alert(
        data.error ||
          data.message ||
          `Error al procesar la citación (HTTP ${res.status})`
      );
      return;
    }

    const row = btn.closest("tr");
    if (row) row.remove();
  } catch (err) {
    alert(
      err?.name === "AbortError"
        ? "Tiempo de espera agotado. Intenta de nuevo."
        : "Error de red: " + err.message
    );
  } finally {
    hideOverlayLocal();
    btn.disabled = false;
  }
});

// ================= Handler “Ver Kárdex” =================

document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".btn-kardex");
  if (!btn) return;

  e.preventDefault();
  const id = btn.dataset.id;
  if (!id) return;

  showOverlayLocal();
  try {
    const res = await fetch(`/citaciones/${id}/kardex/`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    if (!res.ok) {
      window.alert(
        `Error al cargar los registros de Kárdex (HTTP ${res.status}).`
      );
      return;
    }
    const data = await res.json();

    if (!data.ok) {
      window.alert(data.error || "No hay registros de Kárdex para esta citación.");
      return;
    }

    mostrarModalKardex(data);
  } catch (err) {
    window.alert("Error de red: " + err.message);
  } finally {
    hideOverlayLocal();
  }
});

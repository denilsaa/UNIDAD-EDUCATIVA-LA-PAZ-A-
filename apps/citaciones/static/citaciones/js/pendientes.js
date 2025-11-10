// apps/citaciones/static/citaciones/js/pendientes.js
console.log("[PENDIENTES] JS cargado");

// ===== Helpers =====
function getCookie(name){
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(';').shift();
}

// Overlay local (JS puro, sin CSS extra)
function showOverlayLocal() {
  if (document.getElementById("ui-lock")) return;
  const ov = document.createElement("div");
  ov.id = "ui-lock";
  ov.innerHTML = '<div class="ui-lock__box"><div class="ui-lock__spinner"></div><p>Procesando…</p></div>';
  Object.assign(ov.style, {
    position:"fixed", inset:"0", zIndex:"9999",
    background:"rgba(255,255,255,.6)",
    display:"flex", alignItems:"center", justifyContent:"center",
    backdropFilter:"saturate(180%) blur(2px)"
  });
  document.body.appendChild(ov);
  document.body.style.overflow = "hidden";
}
function hideOverlayLocal() {
  const ov = document.getElementById("ui-lock");
  if (ov) ov.remove();
  document.body.style.overflow = "";
}

async function postWithTimeout(url, data, timeoutMs = 20000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      credentials: 'same-origin',
      body: new URLSearchParams(data || {}).toString(),
      signal: controller.signal,
      redirect: 'manual', // evita “colgarse” en 302
    });
    return resp;
  } finally {
    clearTimeout(timer);
  }
}

// ===== Handlers aprobar / rechazar =====
document.addEventListener('click', async (e) => {
  const btn = e.target.closest('.btn-aprobar, .btn-rechazar');
  if (!btn) return;

  // marca explícita de acción AJAX
  btn.setAttribute('data-ajax', '1');

  e.preventDefault();
  const id = btn.dataset.id;
  if (!id) return;

  btn.disabled = true;
  showOverlayLocal();

  try {
    if (btn.classList.contains('btn-aprobar')) {
      const res = await postWithTimeout(`/citaciones/${id}/aprobar/`);
      if (!res || (res.type === 'opaqueredirect') || (res.status >= 300 && res.status !== 400)) {
        window.location.reload();
        return;
      }
      let data = {};
      try { data = await res.json(); } catch {}
      if (res.ok && data.ok) {
        const row = btn.closest('tr');
        if (row) row.remove();
        // Si prefieres refrescar todo: window.location.reload();
      } else {
        alert((data && (data.error || data.message)) || `Error al aprobar (HTTP ${res.status})`);
      }
    } else if (btn.classList.contains('btn-rechazar')) {
      if (!confirm('¿Cancelar esta citación?')) return;
      const res = await postWithTimeout(`/citaciones/${id}/rechazar/`);
      if (!res || (res.type === 'opaqueredirect') || (res.status >= 300 && res.status !== 400)) {
        window.location.reload();
        return;
      }
      let data = {};
      try { data = await res.json(); } catch {}
      if (res.ok && data.ok) {
        const row = btn.closest('tr');
        if (row) row.remove();
      } else {
        alert((data && (data.error || data.message)) || `Error al cancelar (HTTP ${res.status})`);
      }
    }
  } catch (err) {
    alert(err?.name === 'AbortError' ? 'Tiempo de espera agotado. Intenta de nuevo.' : ('Error de red: ' + err.message));
  } finally {
    hideOverlayLocal();
    btn.disabled = false;
  }
});

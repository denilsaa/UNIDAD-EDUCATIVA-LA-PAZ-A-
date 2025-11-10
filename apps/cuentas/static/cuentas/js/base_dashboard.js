// -----------------------------------------------
//  BASE DASHBOARD JS - OVERLAY GLOBAL
// -----------------------------------------------
document.addEventListener("DOMContentLoaded", function () {

  // === Función para mostrar overlay ===
  function showOverlay() {
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

  // === Función para ocultar overlay (por si otras páginas quisieran usarla) ===
  function hideOverlay() {
    const ov = document.getElementById("ui-lock");
    if (ov) ov.remove();
    document.body.style.overflow = "";
  }

  // Exponer mínimamente por si otro script quiere cerrarlo explícitamente
  window.__uiLock = { show: showOverlay, hide: hideOverlay };

  // === Bloqueo global al hacer click en enlaces o botones ===
// === Bloqueo global al hacer click en enlaces o botones ===
document.body.addEventListener("click", function(e) {
  if (document.getElementById("ui-lock")) return; // Ya bloqueado

  // Detectar solo navegación real: <a href>, <button type=submit>, <input type=submit>
  const target = e.target.closest("a[href], button[type=submit], input[type=submit]");
  if (!target) return;

  // Evitar pseudo enlaces internos (#ancla)
  if (target.tagName === "A" && (target.getAttribute("href") || "").startsWith("#")) return;

  // ⛔️ NO bloquear si es una acción AJAX (botones aprobar/rechazar u otros marcados)
  if (e.target.closest('[data-ajax="1"], .btn-aprobar, .btn-rechazar')) return;

  // Mostrar overlay global SOLO para navegación/submit real
  (window.__uiLock?.show || function(){
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
  })();

  // Para enlaces, dejamos que el navegador haga la navegación
  if (target.tagName === "A") return;

  // Para formularios, submit explícito (UX consistente)
  if (target.tagName === "BUTTON" || (target.tagName === "INPUT" && target.type === "submit")) {
    target.classList.add("is-loading");
    const form = target.closest("form");
    if (form) form.submit();
  }
}, true);


  // === Toggle panel notificaciones ===
  const bell = document.getElementById('notif-bell');
  const panel = document.getElementById('notif-panel');
  const closeBtn = document.getElementById('notif-close');
  if (bell && panel) bell.addEventListener('click', () => panel.hidden = !panel.hidden);
  if (closeBtn && panel) closeBtn.addEventListener('click', () => panel.hidden = true);

});

// -----------------------------------------------
//  WEBSOCKET NOTIFICACIONES
// -----------------------------------------------
(function () {
  const uid = window.userData?.id || 0;
  if (!uid) return;

  const $ = (sel) => document.querySelector(sel);
  const badge = $("#notif-badge");
  const panel = $("#notif-panel");
  const panelContent = panel?.querySelector(".notif-panel__content") || null;

  const WS = (path) => {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    return `${proto}://${location.host}${path}`;
  };

  function incBadge(n = 1) {
    if (!badge) return;
    const current = parseInt(badge.textContent || "0", 10) || 0;
    const total = current + (parseInt(n, 10) || 0);
    badge.textContent = total;
    badge.style.display = total > 0 ? "inline-block" : "none";
  }

  function addNotifRow(html) {
    if (!panelContent) return;
    const row = document.createElement("div");
    row.style.padding = "8px 0";
    row.style.borderBottom = "1px solid #f3f3f3";
    row.innerHTML = html;
    panelContent.prepend(row);
  }

  // === WebSocket Notificaciones ===
  const notifs = new WebSocket(WS(`/ws/notifs/?uid=${uid}`));

  notifs.onopen  = () => console.log("[WS NOTIFS] OPEN");
  notifs.onclose = (e) => console.log("[WS NOTIFS] CLOSE", e.code, e.reason);
  notifs.onerror = (e) => console.warn("[WS NOTIFS] ERROR", e);

  notifs.onmessage = (e) => {
    let msg;
    try { msg = JSON.parse(e.data); } catch { return; }

    if (msg.type === "notify.unread" && msg.event === "citacion") {
      incBadge(msg.unread || 1);
      addNotifRow(`
        <strong>Citación #${msg.citacion_id || "—"}</strong><br>
        <small>${msg.estudiante || ""} — ${msg.mensaje || "Nueva citación"}</small><br>
        <small>${msg.cuando ? new Date(msg.cuando).toLocaleString() : ""}</small>
      `);
      return;
    }

    if (msg.type === "director.citacion" && msg.data) {
      const d = msg.data;
      addNotifRow(`
        <strong>Propuesta de citación</strong><br>
        <small>#${d.citacion_id || "—"} · ${d.estudiante || ""}</small><br>
        <small>${d.motivo || ""} · ${d.razon || ""}</small><br>
        <small>ρ≈${(d.rho || 0).toFixed(2)} · Wq≈${d.Wq ? d.Wq.toFixed(1) : "—"} min</small><br>
        <small>Sugerido: ${d.sugerido ? new Date(d.sugerido).toLocaleString() : "—"}</small><br>
        <a href="${location.origin}/citaciones/pendientes/"
           class="btn btn-sm btn-primary"
           style="margin-top:6px; display:inline-block;">
           Revisar
        </a>
      `);
      return;
    }

    console.log("[WS NOTIFS RAW]", msg);
  };

  // === WebSocket COLA ===
  (function () {
    const s = new WebSocket(WS("/ws/cola/"));
    s.onopen = () => console.log("[WS COLA] OPEN");
    s.onmessage = (e) => {
      try { console.log("[WS COLA]", JSON.parse(e.data)); }
      catch { console.log("[WS COLA]", e.data); }
    };
    s.onclose = () => console.log("[WS COLA] CLOSE");
  })();

  // === WebSocket DASHBOARD ===
  (function () {
    const s = new WebSocket(WS("/ws/dashboard/"));
    s.onopen = () => console.log("[WS DASH] OPEN");
    s.onmessage = (e) => {
      try { console.log("[WS DASH]", JSON.parse(e.data)); }
      catch { console.log("[WS DASH]", e.data); }
    };
    s.onclose = () => console.log("[WS DASH] CLOSE");
  })();

})();

// -----------------------------------------------
//  Mensajes Django
// -----------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  const mensajes = document.querySelectorAll('.msg');
  mensajes.forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = '0';
      msg.style.transform = 'translateY(-20px)';
      setTimeout(() => msg.remove(), 500);
    }, 5000);
  });
});

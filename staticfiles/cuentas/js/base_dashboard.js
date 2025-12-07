// static/cuentas/js/base_dashboard.js
document.addEventListener("DOMContentLoaded", function () {

  // ==========================
  // Helpers generales
  // ==========================
  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) {
      return decodeURIComponent(parts.pop().split(";").shift());
    }
    return null;
  }

  function buildWsUrl(path) {
    const scheme = window.location.protocol === "https:" ? "wss" : "ws";
    return `${scheme}://${window.location.host}${path}`;
  }

  function resetBadge() {
    const badge = document.querySelector("#notif-badge");
    if (!badge) return;
    badge.textContent = "0";
    badge.style.display = "none";
  }

  function incrementBadge(delta) {
    const badge = document.querySelector("#notif-badge");
    if (!badge) return;
    const current = parseInt(badge.textContent || "0", 10) || 0;
    const next = current + delta;
    if (next <= 0) {
      badge.textContent = "0";
      badge.style.display = "none";
    } else {
      badge.textContent = String(next);
      badge.style.display = "inline-block";
    }
  }

  // ==========================
  // MENU HAMBURGUESA (MÓVIL)
  // ==========================
  (function initMobileSidebar() {
    const btn = document.getElementById("menu-toggle");
    const sidenav = document.getElementById("sidenav");
    const overlay = document.getElementById("sidebar-overlay");

    if (!btn || !sidenav || !overlay) return;

    const open = () => {
      sidenav.classList.add("open");
      overlay.hidden = false;
      document.body.classList.add("sidebar-open");
      btn.setAttribute("aria-label", "Cerrar menú");
    };

    const close = () => {
      sidenav.classList.remove("open");
      overlay.hidden = true;
      document.body.classList.remove("sidebar-open");
      btn.setAttribute("aria-label", "Abrir menú");
    };

    // Siempre inicia cerrado
    close();

    btn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (sidenav.classList.contains("open")) close();
      else open();
    });

    overlay.addEventListener("click", close);

    // Cierra con ESC
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });

    // Si pasas a desktop, cierra y limpia estados
    window.addEventListener("resize", () => {
      if (window.innerWidth > 900) close();
    });

    // Si haces click en un link del menú en móvil, cierra
    sidenav.addEventListener("click", (e) => {
      const a = e.target.closest("a");
      if (a && window.innerWidth <= 900) close();
    });
  })();

  // ==========================
  // Overlay global "Procesando..."
  // ==========================
  function showOverlay() {
    if (document.getElementById("ui-lock")) return;
    const ov = document.createElement("div");
    ov.id = "ui-lock";
    ov.innerHTML = '<div class="ui-lock__box"><div class="ui-lock__spinner"></div><p>Procesando…</p></div>';
    Object.assign(ov.style, {
      position: "fixed",
      inset: "0",
      zIndex: "9999",
      background: "rgba(255,255,255,.6)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      backdropFilter: "saturate(180%) blur(2px)"
    });
    document.body.appendChild(ov);
    document.body.style.overflow = "hidden";
  }

  function hideOverlay() {
    const ov = document.getElementById("ui-lock");
    if (ov) ov.remove();
    document.body.style.overflow = "";
  }

  window.__uiLock = { show: showOverlay, hide: hideOverlay };

  // ==========================
  // Bloqueo global al hacer submit/click en botones principales
  // ==========================
  document.addEventListener("click", function (e) {
    const target = e.target.closest("[data-ui-lock], button[type=submit], input[type=submit]");
    if (!target) return;

    // Evita doble clic
    if (target.dataset.uiLocking === "1") {
      e.preventDefault();
      return;
    }
    target.dataset.uiLocking = "1";

    (window.__uiLock?.show || showOverlay)();

    if (target.tagName === "A") return;

    if (target.tagName === "BUTTON" || (target.tagName === "INPUT" && target.type === "submit")) {
      target.classList.add("is-loading");
      const form = target.closest("form");
      if (form) form.submit();
    }
  }, true);

  // ==========================
  // Panel de notificaciones
  // ==========================
  const bell = document.getElementById("notif-bell");
  const panel = document.getElementById("notif-panel");
  const closeBtn = document.getElementById("notif-close");
  const panelContent = panel ? panel.querySelector(".notif-panel__content") : null;

  function addNotifRow(html) {
    if (!panelContent) return;

    // Quitar mensaje "Sin notificaciones aún" si existe
    const empty = panelContent.querySelector("[data-no-notifs]");
    if (empty) empty.remove();

    const row = document.createElement("div");
    row.style.padding = "8px 0";
    row.style.borderBottom = "1px solid #f3f3f3";
    row.innerHTML = html;
    panelContent.prepend(row);
  }

  if (bell && panel && closeBtn) {
    bell.addEventListener("click", () => {
      panel.removeAttribute("hidden");

      // Marcar todas como leídas cuando se abre el panel
      fetch("/notifs/marcar-leidas/", {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "X-Requested-With": "XMLHttpRequest",
        },
      })
        .then(r => (r.ok ? r.json() : Promise.reject(r)))
        .then(data => {
          if (data.ok) resetBadge();
        })
        .catch(err => console.error("Error marcando notificaciones:", err));
    });

    closeBtn.addEventListener("click", () => {
      panel.setAttribute("hidden", "");
    });
  }

  // ==========================
  // WebSocket de notificaciones
  // ==========================
  (function initNotifSocket() {
    let socket;
    try {
      const uid = (window.userData && window.userData.id) ? String(window.userData.id) : "";
      const path = uid ? `/ws/notifs/?uid=${encodeURIComponent(uid)}` : "/ws/notifs/";
      socket = new WebSocket(buildWsUrl(path));
    } catch (err) {
      console.error("[WS NOTIFS] Error al crear socket:", err);
      return;
    }

    socket.onopen = function () {
      console.log("[WS NOTIFS] OPEN");
    };

    socket.onclose = function (e) {
      console.warn("[WS NOTIFS] CLOSE", e.code, e.reason || "");
    };

    socket.onerror = function (e) {
      console.error("[WS NOTIFS] ERROR", e);
    };

    socket.onmessage = function (e) {
      let data;
      try {
        data = JSON.parse(e.data);
      } catch (err) {
        console.error("[WS NOTIFS] Mensaje inválido:", e.data);
        return;
      }

      if (data.type === "notify.unread") {
        incrementBadge(data.unread || 1);

        const html = `
          <strong>${data.event === "citacion" ? "Citación #" + data.citacion_id : "Notificación"}</strong><br>
          ${data.estudiante ? data.estudiante + " — " : ""}${data.mensaje}<br>
          <small style="opacity:.7">${data.cuando}</small>
        `;
        addNotifRow(html);
      }
    };
  })();

  // ==========================
  // Otros WebSockets opcionales
  // ==========================
  (function initColaSocket() {
    let socket;
    try { socket = new WebSocket(buildWsUrl("/ws/cola/")); }
    catch (err) { console.error("[WS COLA] Error al crear socket:", err); return; }

    socket.onopen = () => console.log("[WS COLA] OPEN");
    socket.onclose = (e) => console.warn("[WS COLA] CLOSE", e.code, e.reason || "");
    socket.onerror = (e) => console.error("[WS COLA] ERROR", e);
  })();

  (function initDashSocket() {
    let socket;
    try { socket = new WebSocket(buildWsUrl("/ws/dashboard/")); }
    catch (err) { console.error("[WS DASH] Error al crear socket:", err); return; }

    socket.onopen = () => console.log("[WS DASH] OPEN");
    socket.onclose = (e) => console.warn("[WS DASH] CLOSE", e.code, e.reason || "");
    socket.onerror = (e) => console.error("[WS DASH] ERROR", e);
  })();

  // ==========================
  // Mensajes Django que desaparecen
  // ==========================
  const mensajes = document.querySelectorAll(".msg");
  mensajes.forEach(msg => {
    setTimeout(() => {
      msg.style.opacity = "0";
      msg.style.transform = "translateY(-20px)";
      setTimeout(() => msg.remove(), 500);
    }, 5000);
  });

});

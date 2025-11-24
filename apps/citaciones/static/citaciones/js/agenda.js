// apps/citaciones/static/citaciones/js/agenda.js
(function () {
  // ===== Helpers básicos =====
  function getCookie(name) {
    const v = `; ${document.cookie}`.split(`; ${name}=`);
    if (v.length === 2) return v.pop().split(";").shift();
  }

  async function post(url, data = {}) {
    const body = new URLSearchParams(data).toString();
    const resp = await fetch(url, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": getCookie("csrftoken"),
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    });
    return resp.json();
  }

  // ===== Modal ligero (confirm / alert) =====
  function setupModalHelpers() {
    const modal = document.getElementById("modal-lite");
    if (!modal) return;

    const titleEl = modal.querySelector(".modal-lite__title");
    const bodyEl = modal.querySelector(".modal-lite__body");
    const btnCancel = document.getElementById("modal-lite-cancel");
    const btnOk = document.getElementById("modal-lite-ok");

    function openModal(opts) {
      const title = opts.title || "";
      const message = opts.message || "";
      const showCancel = !!opts.showCancel;

      titleEl.textContent = title;
      bodyEl.textContent = message;
      btnCancel.style.display = showCancel ? "" : "none";

      modal.classList.add("show");

      return new Promise((resolve) => {
        function cleanup(result) {
          modal.classList.remove("show");
          btnCancel.onclick = null;
          btnOk.onclick = null;
          resolve(result);
        }

        btnCancel.onclick = function () {
          cleanup(false);
        };

        btnOk.onclick = function () {
          cleanup(true);
        };
      });
    }

    window.modalLiteConfirm = function (message) {
      return openModal({
        title: "Confirmar acción",
        message: message,
        showCancel: true,
      });
    };

    window.modalLiteAlert = function (message, title) {
      return openModal({
        title: title || "Información",
        message: message,
        showCancel: false,
      });
    };
  }

  // ===== Lógica de botones (cancelar / notificar) =====
  function setupClickHandlers() {
    document.addEventListener("click", async function (e) {
      // --- Cancelar citación ---
      const cancelBtn = e.target.closest(".btn-cancelar");
      if (cancelBtn) {
        e.preventDefault();
        const id = cancelBtn.dataset.id;

        const ok = await (window.modalLiteConfirm
          ? window.modalLiteConfirm("¿Cancelar esta citación?")
          : Promise.resolve(confirm("¿Cancelar esta citación?")));
        if (!ok) return;

        (window.__uiLock?.show || function () {})();

        try {
          const r = await post(`/citaciones/${id}/rechazar/`);
          if (r && r.ok) {
            window.location.reload();
          } else {
            const msg = (r && r.error) || "Error al cancelar la citación.";
            if (window.modalLiteAlert) {
              await window.modalLiteAlert(msg);
            } else {
              alert(msg);
            }
          }
        } catch (err) {
          console.error(err);
          if (window.modalLiteAlert) {
            await window.modalLiteAlert(
              "Ocurrió un error inesperado al cancelar."
            );
          } else {
            alert("Ocurrió un error inesperado al cancelar.");
          }
        } finally {
          (window.__uiLock?.hide || function () {})();
        }

        return;
      }

      // --- Mandar notificación ---
      const notifBtn = e.target.closest(".btn-notificar");
      if (notifBtn) {
        e.preventDefault();
        const id = notifBtn.dataset.id;

        (window.__uiLock?.show || function () {})();

        let r = null;
        try {
          r = await post(`/citaciones/${id}/notificar/`);
        } catch (err) {
          console.error(err);
          (window.__uiLock?.hide || function () {})();

          if (window.modalLiteAlert) {
            await window.modalLiteAlert(
              "Ocurrió un error inesperado al enviar la notificación."
            );
          } else {
            alert(
              "Ocurrió un error inesperado al enviar la notificación."
            );
          }
          return;
        }

        // Quitamos overlay antes de mostrar modal
        (window.__uiLock?.hide || function () {})();

        try {
          if (r && r.ok) {
            if (window.modalLiteAlert) {
              await window.modalLiteAlert(
                "Notificación enviada al padre de familia."
              );
            } else {
              alert("Notificación enviada al padre de familia.");
            }
          } else {
            const msg =
              (r && r.error) || "Error al enviar la notificación.";
            if (window.modalLiteAlert) {
              await window.modalLiteAlert(msg);
            } else {
              alert(msg);
            }
          }
        } catch (err2) {
          console.error(err2);
        }

        return;
      }
    });
  }

  // ===== Inicializar =====
  document.addEventListener("DOMContentLoaded", function () {
    setupModalHelpers();
    setupClickHandlers();
  });
})();

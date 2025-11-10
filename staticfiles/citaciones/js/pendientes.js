console.log("[PENDIENTES] JS cargado");

async function post(url, data) {
  const body = new URLSearchParams(data || {});
  const resp = await fetch(url, {
    method: 'POST',
    headers: {'X-CSRFToken': getCookie('csrftoken')},
    credentials: 'same-origin',
    body
  });
  return resp.json();
}
function getCookie(name){
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(';').shift();
}

document.addEventListener('click', async (e) => {
  const b = e.target.closest('.btn-aprobar, .btn-rechazar');
  if (!b) return;
  const id = b.dataset.id;

  if (b.classList.contains('btn-aprobar')) {
    const r = await post(`/citaciones/${id}/aprobar/`);
    if (r.ok) location.reload();
    else alert(r.error || "Error al aprobar");
  } else if (b.classList.contains('btn-rechazar')) {
    if (!confirm('¿Cancelar esta citación?')) return;
    const r = await post(`/citaciones/${id}/rechazar/`);
    if (r.ok) location.reload();
    else alert(r.error || "Error al cancelar");
  }
});
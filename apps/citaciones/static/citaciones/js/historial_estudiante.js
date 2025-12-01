// apps/citaciones/static/citaciones/js/historial_estudiante.js

document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("busqueda-citaciones");
  if (!input) return;

  const rows = Array.from(
    document.querySelectorAll('table.tabla tbody tr[data-row="citacion"]')
  );

  input.addEventListener("input", function () {
    const term = input.value.trim().toLowerCase();

    rows.forEach((row) => {
      if (!term) {
        row.style.display = "";
        return;
      }
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(term) ? "" : "none";
    });
  });
});

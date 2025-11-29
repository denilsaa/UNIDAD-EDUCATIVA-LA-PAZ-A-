document.addEventListener("DOMContentLoaded", () => {
  const getJSON = (id, fallback) => {
    const el = document.getElementById(id);
    if (!el) return fallback;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      return fallback;
    }
  };

  const citEstados = getJSON("sec-citaciones-estado", {});
  const estCurso = getJSON("sec-estudiantes-curso", []);
  const altasEst = getJSON("sec-altas-estudiantes", { labels: [], values: [] });
  const citMes = getJSON("sec-citaciones-mes", { labels: [], abiertas: [], cerradas: [] });

  // === Pie citaciones por estado ===
  const ctxEstado = document.getElementById("secCitacionesEstadoChart");
  if (ctxEstado && Object.keys(citEstados).length) {
    const labels = Object.keys(citEstados);
    const data = labels.map(k => citEstados[k]);

    new Chart(ctxEstado, {
      type: "pie",
      data: {
        labels,
        datasets: [{ data }],
      },
      options: {
        plugins: { legend: { position: "bottom" } },
      },
    });
  }

  // === Barras estudiantes por curso (Top 10) ===
  const ctxCurso = document.getElementById("secEstudiantesCursoChart");
  if (ctxCurso && estCurso.length) {
    const labels = estCurso.map(r => r.curso);
    const values = estCurso.map(r => r.total);

    new Chart(ctxCurso, {
      type: "bar",
      data: {
        labels,
        datasets: [{ label: "Estudiantes", data: values }],
      },
      options: {
        scales: { y: { beginAtZero: true } },
      },
    });
  }

  // === Línea altas de estudiantes por mes ===
  const ctxAltas = document.getElementById("secAltasEstudiantesChart");
  if (ctxAltas && altasEst.labels.length) {
    new Chart(ctxAltas, {
      type: "line",
      data: {
        labels: altasEst.labels,
        datasets: [{
          label: "Altas de estudiantes",
          data: altasEst.values,
          fill: true,
          tension: 0.3,
        }],
      },
      options: {
        scales: { y: { beginAtZero: true } },
      },
    });
  }

  // === Barras abiertas vs cerradas por mes ===
  const ctxCM = document.getElementById("secCitacionesMesChart");
  if (ctxCM && citMes.labels.length) {
    new Chart(ctxCM, {
      type: "bar",
      data: {
        labels: citMes.labels,
        datasets: [
          { label: "Abiertas", data: citMes.abiertas },
          { label: "Cerradas", data: citMes.cerradas },
        ],
      },
      options: {
        scales: { y: { beginAtZero: true } },
      },
    });
  }
});

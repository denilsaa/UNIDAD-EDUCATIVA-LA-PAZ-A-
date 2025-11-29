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

  const asisHoy = getJSON("reg-asistencia-hoy", { presentes: 0, faltas: 0, atrasos: 0 });
  const asisMeses = getJSON("reg-asistencia-meses", { labels: [], values: [] });
  const faltasCurso = getJSON("reg-faltas-curso", []);
  const citEstados = getJSON("reg-citaciones-estado", {});

  // === Donut asistencia hoy ===
  const ctxHoy = document.getElementById("regAsistenciaHoyChart");
  if (ctxHoy) {
    const data = [
      asisHoy.presentes || 0,
      asisHoy.faltas || 0,
      asisHoy.atrasos || 0,
    ];
    new Chart(ctxHoy, {
      type: "doughnut",
      data: {
        labels: ["Presentes", "Faltas", "Atrasos"],
        datasets: [{
          data,
          borderWidth: 0,
        }],
      },
      options: {
        plugins: {
          legend: { display: true, position: "bottom" },
        },
        cutout: "70%",
      },
    });
  }

  // === Línea asistencia por mes ===
  const ctxMeses = document.getElementById("regAsistenciaMesesChart");
  if (ctxMeses && asisMeses.labels.length) {
    new Chart(ctxMeses, {
      type: "line",
      data: {
        labels: asisMeses.labels,
        datasets: [{
          label: "% de asistencia",
          data: asisMeses.values,
          fill: true,
          tension: 0.3,
        }],
      },
      options: {
        scales: {
          y: { min: 0, max: 100, ticks: { callback: v => v + "%" } },
        },
      },
    });
  }

  // === Barras faltas/atrasos por curso ===
  const ctxFaltasCurso = document.getElementById("regFaltasCursoChart");
  if (ctxFaltasCurso && faltasCurso.length) {
    const labels = faltasCurso.map(r => r.curso);
    const faltas = faltasCurso.map(r => r.faltas);
    const atrasos = faltasCurso.map(r => r.atrasos);

    new Chart(ctxFaltasCurso, {
      type: "bar",
      data: {
        labels,
        datasets: [
          { label: "Faltas", data: faltas },
          { label: "Atrasos", data: atrasos },
        ],
      },
      options: {
        responsive: true,
        scales: { y: { beginAtZero: true } },
      },
    });
  }

  // === Pie citaciones por estado ===
  const ctxCit = document.getElementById("regCitacionesEstadoChart");
  if (ctxCit && Object.keys(citEstados).length) {
    const labels = Object.keys(citEstados);
    const data = labels.map(k => citEstados[k]);

    new Chart(ctxCit, {
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
});

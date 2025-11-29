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

  const asisMes = getJSON("pad-asistencia-mes", { presentes: 0, faltas: 0, atrasos: 0 });
  const asisMeses = getJSON("pad-asistencia-meses", { labels: [], values: [] });
  const faltasHijo = getJSON("pad-faltas-hijo", []);

  // === Donut asistencia del mes ===
  const ctxMes = document.getElementById("padAsistenciaMesChart");
  if (ctxMes) {
    const data = [
      asisMes.presentes || 0,
      asisMes.faltas || 0,
      asisMes.atrasos || 0,
    ];
    new Chart(ctxMes, {
      type: "doughnut",
      data: {
        labels: ["Presentes", "Faltas", "Atrasos"],
        datasets: [{ data, borderWidth: 0 }],
      },
      options: {
        plugins: { legend: { position: "bottom" } },
        cutout: "65%",
      },
    });
  }

  // === Línea evolución asistencia (6 meses) ===
  const ctxMeses = document.getElementById("padAsistenciaMesesChart");
  if (ctxMeses && asisMeses.labels.length) {
    new Chart(ctxMeses, {
      type: "line",
      data: {
        labels: asisMeses.labels,
        datasets: [{
          label: "% asistencia",
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

  // === Barras faltas/atrasos por hijo ===
  const ctxFH = document.getElementById("padFaltasHijoChart");
  if (ctxFH && faltasHijo.length) {
    const labels = faltasHijo.map(r => r.estudiante);
    const faltas = faltasHijo.map(r => r.faltas);
    const atrasos = faltasHijo.map(r => r.atrasos);

    new Chart(ctxFH, {
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
});

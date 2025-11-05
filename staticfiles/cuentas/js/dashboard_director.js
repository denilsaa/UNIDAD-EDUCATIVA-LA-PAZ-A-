(() => {
  // Configuración global de Chart.js
  Chart.defaults.color = '#0f172a';
  Chart.defaults.font.family = 'Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif';
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.elements.line.tension = 0.35;

  // Variables locales
  const gridColor = '#e6e8ee';
  ['x','y'].forEach(ax => {
    if(!Chart.defaults.scales[ax]) Chart.defaults.scales[ax] = {};
    Chart.defaults.scales[ax].grid = { color: gridColor, drawBorder:false };
  });

  const C = { azul:'#0c2a57', azulSuave:'#13386f', metal:'#c7cdd6' };

  // Objeto global para guardar referencias a los charts
  window.charts = window.charts || {};

  // === Donut asistencia hoy ===
  (() => {
    const el = document.getElementById("asistencia-hoy");
    if(!el) return;
    const val = JSON.parse(el.textContent || '0');
    const canvas = document.getElementById('asistenciaHoyChart');

    if(window.charts.asistenciaHoyChart) window.charts.asistenciaHoyChart.destroy();

    window.charts.asistenciaHoyChart = new Chart(canvas, {
      type:'doughnut',
      data:{ labels:['Asistió','No asistió'], datasets:[{ data:[val, 100-val], backgroundColor:[C.azul, C.metal]}] },
      options:{ cutout:'65%', plugins:{legend:{display:false}} }
    });
  })();

  // === Línea asistencia por mes ===
  (() => {
    const el = document.getElementById("asistencia-por-mes"); if(!el) return;
    const d = JSON.parse(el.textContent || '[]');
    const canvas = document.getElementById('asistenciaMeses');

    if(window.charts.asistenciaMeses) window.charts.asistenciaMeses.destroy();

    window.charts.asistenciaMeses = new Chart(canvas, {
      type:'line',
      data:{ labels:d.map(x=>x.mes),
        datasets:[{ label:'Asistencia', data:d.map(x=>x.pct), borderColor:C.azul, backgroundColor:C.azul+'22', tension:.35, fill:true }] },
      options:{ plugins:{legend:{display:false}}, scales:{y:{ticks:{callback:v=>v+'%'}}} }
    });
  })();

  // === Barras: Kárdex negativo por área ===
  (() => {
    const el = document.getElementById("negativos-por-area"); if(!el) return;
    const d = JSON.parse(el.textContent || '[]');
    const canvas = document.getElementById('kardexArea');

    if(window.charts.kardexArea) window.charts.kardexArea.destroy();

    window.charts.kardexArea = new Chart(canvas, {
      type:'bar',
      data:{ labels:d.map(x=>x.area), datasets:[{ data:d.map(x=>x.total), backgroundColor:[C.azul,C.azulSuave,C.metal,'#8aa1c7'] }] },
      options:{ plugins:{legend:{display:false}} }
    });
  })();

  // === Mini barras: negativos (7 días) ===
  (() => {
    const el = document.getElementById("negativos-semana"); if(!el) return;
    const d = JSON.parse(el.textContent || '[]');
    const canvas = document.getElementById('negativosSemana');

    if(window.charts.negativosSemana) window.charts.negativosSemana.destroy();

    window.charts.negativosSemana = new Chart(canvas, {
      type:'bar',
      data:{ labels:d.map(x=>x.dia), datasets:[{ data:d.map(x=>x.total), backgroundColor:C.azulSuave }] },
      options:{ plugins:{legend:{display:false}}, scales:{x:{display:false}, y:{display:false}} }
    });
  })();

  // === Pie: Roles ===
  (() => {
    const el = document.getElementById("roles_counts"); if(!el) return;
    const data = JSON.parse(el.textContent || '{}');
    const canvas = document.getElementById('rolesPie');

    if(window.charts.rolesPie) window.charts.rolesPie.destroy();

    const colors = ['#0c2a57','#13386f','#c7cdd6','#8aa1c7','#f59e0b','#10b981','#f43f5e','#f97316'];

    window.charts.rolesPie = new Chart(canvas, {
      type: 'pie',
      data: {
        labels: Object.keys(data),
        datasets: [{ data: Object.values(data), backgroundColor: colors.slice(0, Object.keys(data).length) }]
      },
      options: {
        plugins: { legend: { position: 'bottom', labels: { usePointStyle: true } } },
        responsive: true,
        maintainAspectRatio: false
      }
    });
  })();

})();

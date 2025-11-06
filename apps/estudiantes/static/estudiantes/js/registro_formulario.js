document.addEventListener('DOMContentLoaded', () => {
  // ======= FECHA =======
  const inFecha = document.getElementById('id_fecha');
  const selDia  = document.getElementById('dia_select');
  const mesLbl  = document.getElementById('mes_label');

  if (inFecha && selDia && mesLbl) {
    const minStr = inFecha.getAttribute('min');
    const maxStr = inFecha.getAttribute('max');
    let y, m;
    if (minStr) { const p = minStr.split('-'); y = +p[0]; m = +p[1]; }
    else { const now = new Date(); y = now.getFullYear(); m = now.getMonth()+1; }

    const meses = ['enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'];
    mesLbl.textContent = `${meses[m-1]} ${y}`;

    const lastDay = maxStr ? +maxStr.slice(8,10) : new Date(y, m, 0).getDate();
    const firstDay = 1;

    const hoy = new Date();
    const esMismoMes = (hoy.getFullYear() === y && (hoy.getMonth()+1) === m);
    const diaDefault = esMismoMes ? hoy.getDate() : firstDay;

    selDia.innerHTML = '';
    for (let d = firstDay; d <= lastDay; d++) {
      const op = document.createElement('option');
      op.value = String(d).padStart(2,'0');
      op.textContent = d;
      if (d === diaDefault) op.selected = true;
      selDia.appendChild(op);
    }

    function syncFecha() {
      const day = selDia.value;
      const iso = `${y}-${String(m).padStart(2,'0')}-${day}`;
      inFecha.value = iso;
    }
    syncFecha();
    selDia.addEventListener('change', syncFecha);
  }

  // ======= HORA =======
  const inHora = document.getElementById('id_hora');
  const selHora = document.getElementById('hora_select');

  if (inHora && selHora) {
    const pasoMin = 30;     
    const startH  = 7, startM = 0;
    const endH    = 14, endM  = 0;

    function toHM(h, m){ return String(h).padStart(2,'0') + ':' + String(m).padStart(2,'0'); }

    selHora.innerHTML = '';
    for (let h = startH; h <= endH; h++) {
      for (let mm = (h===startH?startM:0); mm < 60; mm += pasoMin) {
        if (h === endH && mm > endM) break;
        const val = toHM(h, mm);
        const op = document.createElement('option');
        op.value = val; op.textContent = val;
        selHora.appendChild(op);
      }
    }

    const preset = (inHora.value && selHora.querySelector(`option[value="${inHora.value}"]`))
                    ? inHora.value : toHM(startH,startM);
    selHora.value = preset;
    inHora.value  = preset;

    selHora.addEventListener('change', () => { inHora.value = selHora.value; });
  }

  // ======= VALIDACIÓN EN TIEMPO REAL =======
  const form = inFecha.closest('form');
  if (form) {
    const kardexItem = document.getElementById('id_kardex_item');
    const observacion = document.getElementById('id_observacion');

    // Crear spans de error debajo de los inputs
    let kardexError = document.createElement('span');
    kardexError.style.color = '#dc3545';
    kardexError.style.fontSize = '0.85rem';
    kardexError.style.display = 'none';
    kardexItem.parentNode.appendChild(kardexError);

    let observacionError = document.createElement('span');
    observacionError.style.color = '#dc3545';
    observacionError.style.fontSize = '0.85rem';
    observacionError.style.display = 'none';
    observacion.parentNode.appendChild(observacionError);

    // ===== Validación en tiempo real =====
    kardexItem.addEventListener('change', () => {
      if (!kardexItem.value || kardexItem.value === "---------") {
        kardexError.textContent = "Este campo es obligatorio.";
        kardexError.style.display = 'block';
        kardexItem.style.borderColor = '#dc3545';
      } else {
        kardexError.style.display = 'none';
        kardexItem.style.borderColor = '#28a745';
      }
    });

    observacion.addEventListener('input', () => {
      const len = observacion.value.trim().length;
      if (len < 10) {
        observacionError.textContent = "Mínimo 10 caracteres.";
        observacionError.style.display = 'block';
        observacion.style.borderColor = '#dc3545';
      } else if (len > 500) {
        observacion.value = observacion.value.slice(0,500); // cortar exceso
        observacionError.textContent = "Máximo 500 caracteres.";
        observacionError.style.display = 'block';
        observacion.style.borderColor = '#dc3545';
      } else {
        observacionError.style.display = 'none';
        observacion.style.borderColor = '#28a745';
      }
    });

    // ===== Validación al enviar =====
    form.addEventListener('submit', (e) => {
      let valido = true;

      if (!kardexItem.value || kardexItem.value === "---------") {
        kardexError.textContent = "Este campo es obligatorio.";
        kardexError.style.display = 'block';
        kardexItem.style.borderColor = '#dc3545';
        valido = false;
      }

      const obsLen = observacion.value.trim().length;
      if (obsLen < 10) {
        observacionError.textContent = "Mínimo 10 caracteres.";
        observacionError.style.display = 'block';
        observacion.style.borderColor = '#dc3545';
        valido = false;
      } else if (obsLen > 500) {
        observacionError.textContent = "Máximo 500 caracteres.";
        observacionError.style.display = 'block';
        observacion.style.borderColor = '#dc3545';
        valido = false;
      }

      if (!valido) e.preventDefault();
    });
  }
});

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.form-usuario');
  if (!form) return;

  // ===== CAMPOS =====
  const areaSelect = document.getElementById('id_area');
  const descripcionInput = document.getElementById('id_descripcion');

  // ===== CREAR SPANS DE ERROR =====
  const crearError = (input, id) => {
    let span = document.getElementById(id);
    if (!span) {
      span = document.createElement('span');
      span.id = id;
      span.className = 'error-message';
      span.style.color = '#dc3545';
      span.style.fontSize = '0.85rem';
      span.style.display = 'block';
      input.parentNode.appendChild(span);
    }
    return span;
  }

  const areaError = crearError(areaSelect, 'area-error');
  const descripcionError = crearError(descripcionInput, 'descripcion-error');

  // ===== VALIDACIÓN EN TIEMPO REAL =====

  // Área
  areaSelect.addEventListener('change', () => {
    const valor = areaSelect.value.trim();
    if (!valor || valor === "---------") {
      areaError.textContent = "Este campo es obligatorio.";
      areaSelect.style.borderColor = '#dc3545';
    } else {
      areaError.textContent = "";
      areaSelect.style.borderColor = '#28a745';
    }
  });

  // Descripción
  descripcionInput.addEventListener('input', () => {
    const valor = descripcionInput.value.trim();
    if (!valor) {
      descripcionError.textContent = "Este campo es obligatorio.";
      descripcionInput.style.borderColor = '#dc3545';
    } else if (valor.length > 30) {
      descripcionError.textContent = "Máximo 30 caracteres permitidos.";
      descripcionInput.value = valor.slice(0,30);
      descripcionInput.style.borderColor = '#dc3545';
    } else {
      descripcionError.textContent = "";
      descripcionInput.style.borderColor = '#28a745';
    }
  });

  // ===== VALIDACIÓN AL ENVIAR =====
  form.addEventListener('submit', (e) => {
    let valido = true;

    // Área
    const areaValor = areaSelect.value.trim();
    if (!areaValor || areaValor === "---------") {
      areaError.textContent = "Este campo es obligatorio.";
      areaSelect.style.borderColor = '#dc3545';
      valido = false;
    } else {
      areaError.textContent = "";
      areaSelect.style.borderColor = '#28a745';
    }

    // Descripción
    const descValor = descripcionInput.value.trim();
    if (!descValor) {
      descripcionError.textContent = "Este campo es obligatorio.";
      descripcionInput.style.borderColor = '#dc3545';
      valido = false;
    } else if (descValor.length > 30) {
      descripcionError.textContent = "Máximo 30 caracteres permitidos.";
      descripcionInput.value = descValor.slice(0,30);
      descripcionInput.style.borderColor = '#dc3545';
      valido = false;
    } else {
      descripcionError.textContent = "";
      descripcionInput.style.borderColor = '#28a745';
    }

    if (!valido) {
      e.preventDefault();
      alert("Corrige los campos obligatorios antes de guardar.");
    }
  });
});

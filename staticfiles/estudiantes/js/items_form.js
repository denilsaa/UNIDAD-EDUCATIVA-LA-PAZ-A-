document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.form-usuario');
  if (!form) return;

  const areaSelect = document.getElementById('id_area');
  const descripcionInput = document.getElementById('id_descripcion');

  const CHECK_URL = window.KARDEX_ITEM_CHECK_URL || null;
  const EXCLUDE_ID = (window.KARDEX_ITEM_EXCLUDE_ID || '').toString().trim();

  const crearError = (input, id) => {
    let span = document.getElementById(id);
    if (!span) {
      span = document.createElement('span');
      span.id = id;
      span.className = 'error-message';
      span.style.color = '#dc3545';
      span.style.fontSize = '0.85rem';
      span.style.display = 'block';
      span.style.marginTop = '6px';
      input.parentNode.appendChild(span);
    }
    return span;
  };

  const areaError = crearError(areaSelect, 'area-error');
  const descripcionError = crearError(descripcionInput, 'descripcion-error');
  const duplicadoError = crearError(descripcionInput, 'duplicado-error');

  const setOk = (el) => (el.style.borderColor = '#28a745');
  const setBad = (el) => (el.style.borderColor = '#dc3545');

  const normalizar = (s) => (s || '').replace(/\s+/g, ' ').trim();

  const validarAreaLocal = () => {
    const valor = (areaSelect.value || '').trim();
    if (!valor || valor === "---------") {
      areaError.textContent = "Este campo es obligatorio.";
      setBad(areaSelect);
      return false;
    }
    areaError.textContent = "";
    setOk(areaSelect);
    return true;
  };

  const validarDescripcionLocal = () => {
    const valor = normalizar(descripcionInput.value);
    descripcionInput.value = valor;

    if (!valor) {
      descripcionError.textContent = "Este campo es obligatorio.";
      setBad(descripcionInput);
      return false;
    }
    if (valor.length > 160) {
      descripcionError.textContent = "Máximo 160 caracteres permitidos.";
      descripcionInput.value = valor.slice(0, 160);
      setBad(descripcionInput);
      return false;
    }

    descripcionError.textContent = "";
    // ojo: no ponemos verde final si está duplicado (eso lo define validarDuplicado)
    return true;
  };

  let lastRequestId = 0;
  let isDuplicado = false;

  const validarDuplicado = async () => {
    isDuplicado = false;
    duplicadoError.textContent = "";

    if (!CHECK_URL) {
      // sin endpoint, no podemos validar duplicados
      if (validarDescripcionLocal()) setOk(descripcionInput);
      return true;
    }

    if (!validarAreaLocal() || !validarDescripcionLocal()) return false;

    const area = (areaSelect.value || '').trim();
    const descripcion = normalizar(descripcionInput.value);

    const requestId = ++lastRequestId;

    const params = new URLSearchParams({ area, descripcion });
    if (EXCLUDE_ID) params.set('exclude_id', EXCLUDE_ID);

    try {
      const res = await fetch(`${CHECK_URL}?${params.toString()}`, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });

      // Ignora respuestas viejas (si el usuario siguió escribiendo)
      if (requestId !== lastRequestId) return true;

      if (!res.ok) {
        // si falla, no bloqueamos
        if (validarDescripcionLocal()) setOk(descripcionInput);
        return true;
      }

      const data = await res.json();
      isDuplicado = !!data.exists;

      if (isDuplicado) {
        duplicadoError.textContent = "Ya existe un ítem con esta Área y Descripción.";
        setBad(descripcionInput);
        return false;
      }

      duplicadoError.textContent = "";
      setOk(descripcionInput);
      return true;
    } catch (e) {
      // error red: no bloqueamos
      if (validarDescripcionLocal()) setOk(descripcionInput);
      return true;
    }
  };

  const debounce = (fn, ms = 350) => {
    let t;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  };

  const validarDuplicadoDebounced = debounce(validarDuplicado, 350);

  areaSelect.addEventListener('change', () => {
    validarAreaLocal();
    validarDuplicadoDebounced();
  });

  descripcionInput.addEventListener('input', () => {
    validarDescripcionLocal();
    validarDuplicadoDebounced();
  });

  form.addEventListener('submit', async (e) => {
    let valido = true;

    if (!validarAreaLocal()) valido = false;
    if (!validarDescripcionLocal()) valido = false;

    const okDup = await validarDuplicado();
    if (!okDup) valido = false;

    if (!valido) {
      e.preventDefault();
      alert("Corrige los campos antes de guardar.");
    }
  });
});

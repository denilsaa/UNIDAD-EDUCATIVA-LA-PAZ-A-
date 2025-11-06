document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.form-curso');
  const nivel = document.getElementById('nivel');
  const paralelo = document.getElementById('paralelo');
  const regente = document.querySelector('[name="regente"]');

  const crearError = (input) => {
    const span = document.createElement('span');
    span.style.color = '#dc3545';
    span.style.fontSize = '0.85rem';
    span.classList.add('error-msg');
    input.parentNode.appendChild(span);
    return span;
  };

  const nivelError = crearError(nivel);
  const paraleloError = crearError(paralelo);
  const regenteError = crearError(regente);

  // 🔹 Verifica si el curso ya existe
  const cursoExiste = (nivelVal, paraleloVal) => {
    return cursosExistentes.some(curso =>
      curso.nivel === nivelVal && curso.paralelo === paraleloVal
    );
  };

  // 🔹 Valida campo vacío
  const validar = (input, errorMsg) => {
    if (!input.value) {
      errorMsg.textContent = 'Este campo es obligatorio.';
      input.style.borderColor = '#dc3545';
      return false;
    } else {
      errorMsg.textContent = '';
      input.style.borderColor = '#28a745';
      return true;
    }
  };

  // 🔹 Validación en tiempo real
  nivel.addEventListener('change', () => {
    validar(nivel, nivelError);
  });

  paralelo.addEventListener('change', () => {
    validar(paralelo, paraleloError);

    if (nivel.value && paralelo.value && cursoExiste(nivel.value, paralelo.value)) {
      paraleloError.textContent = '⚠️ Ya existe un curso con este Nivel y Paralelo.';
      paralelo.style.borderColor = '#dc3545';
    }
  });

  regente.addEventListener('change', () => validar(regente, regenteError));

  // 🔹 Validación al enviar
  form.addEventListener('submit', (e) => {
    const nivelValido = validar(nivel, nivelError);
    const paraleloValido = validar(paralelo, paraleloError);
    const regenteValido = validar(regente, regenteError);

    if (cursoExiste(nivel.value, paralelo.value)) {
      paraleloError.textContent = '⚠️ Este curso ya existe.';
      paralelo.style.borderColor = '#dc3545';
      e.preventDefault();
      return;
    }

    if (!nivelValido || !paraleloValido || !regenteValido) {
      e.preventDefault();
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.form-detalle');
  const nivel = document.getElementById('nivel');
  const paralelo = document.getElementById('paralelo');
  const regente = document.querySelector('[name="regente"]');

  // Crear contenedor de error
  const crearError = (input) => {
    let span = input.parentNode.querySelector('span.error-msg');
    if (!span) {
      span = document.createElement('span');
      span.classList.add('error-msg');
      span.style.color = '#dc3545';
      span.style.fontSize = '0.85rem';
      input.parentNode.appendChild(span);
    }
    return span;
  };

  const nivelError = crearError(nivel);
  const paraleloError = crearError(paralelo);
  const regenteError = crearError(regente);

  // 🔹 Verifica si ya existe otro curso con el mismo nivel y paralelo
  const cursoExiste = (nivelVal, paraleloVal) => {
    return cursosExistentes.some(curso =>
      curso.nivel === nivelVal && curso.paralelo === paraleloVal
    );
  };

  // 🔹 Valida si un campo está vacío
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

  // === Validaciones en tiempo real ===
  nivel.addEventListener('change', () => {
    validar(nivel, nivelError);
    verificarCursoExistente();
  });

  paralelo.addEventListener('change', () => {
    validar(paralelo, paraleloError);
    verificarCursoExistente();
  });

  regente.addEventListener('change', () => validar(regente, regenteError));

  // 🔹 Verificar existencia de curso duplicado
  function verificarCursoExistente() {
    if (nivel.value && paralelo.value && cursoExiste(nivel.value, paralelo.value)) {
      paraleloError.textContent = '⚠️ Ya existe un curso con este Nivel y Paralelo.';
      paralelo.style.borderColor = '#dc3545';
      return true;
    } else {
      if (paraleloError.textContent.includes('Ya existe')) paraleloError.textContent = '';
      paralelo.style.borderColor = '#28a745';
      return false;
    }
  }

  // === Validación al enviar ===
  form.addEventListener('submit', (e) => {
    const nivelValido = validar(nivel, nivelError);
    const paraleloValido = validar(paralelo, paraleloError);
    const regenteValido = validar(regente, regenteError);

    const duplicado = verificarCursoExistente();

    if (!nivelValido || !paraleloValido || !regenteValido || duplicado) {
      e.preventDefault();
    }
  });
});

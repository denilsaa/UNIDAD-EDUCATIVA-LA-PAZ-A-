document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.form-detalle'); // <-- aquí
  const nivel = document.getElementById('nivel');
  const paralelo = document.getElementById('paralelo');
  const regente = document.querySelector('[name="regente"]');

  // Crear contenedores de error si no existen
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

  // Función de validación
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

  // Validación en tiempo real
  nivel.addEventListener('change', () => validar(nivel, nivelError));
  paralelo.addEventListener('change', () => validar(paralelo, paraleloError));
  regente.addEventListener('change', () => validar(regente, regenteError));

  // Validación al enviar
  form.addEventListener('submit', (e) => {
    const nivelValido = validar(nivel, nivelError);
    const paraleloValido = validar(paralelo, paraleloError);
    const regenteValido = validar(regente, regenteError);

    if (!nivelValido || !paraleloValido || !regenteValido) {
      e.preventDefault();
    }
  });
});

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('.form-curso');
  const nivel = document.getElementById('nivel');
  const paralelo = document.getElementById('paralelo');
  
  // Detectar correctamente el id del regente generado por Django
  const regente = document.querySelector('[name="regente"]'); // funciona sin depender del id

  // Crear contenedores de error
  const crearError = (input) => {
    const span = document.createElement('span');
    span.style.color = '#dc3545';
    span.style.fontSize = '0.85rem';
    input.parentNode.appendChild(span);
    return span;
  }

  const nivelError = crearError(nivel);
  const paraleloError = crearError(paralelo);
  const regenteError = crearError(regente);

  // Funciones de validación
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
  }

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

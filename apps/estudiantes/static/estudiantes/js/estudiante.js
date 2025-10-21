document.addEventListener('DOMContentLoaded', () => {
    // ===== CI =====
    const ciInput = document.getElementById('id_ci');

    // Crear span de error si no existe
    let ciError = document.getElementById('ci-error');
    if (!ciError) {
        ciError = document.createElement('span');
        ciError.id = 'ci-error';
        ciError.className = 'error-message';
        ciError.style.display = 'none';
        ciInput.parentNode.appendChild(ciError);
    }

    // Impedir escribir letras o espacios
    ciInput.addEventListener('keypress', (e) => {
        if (!/[0-9]/.test(e.key)) {
            e.preventDefault();
            ciError.textContent = "Solo se permiten números en el CI.";
            ciError.style.display = 'block';
        } else {
            ciError.style.display = 'none';
        }
    });

    // Validar longitud y limpiar caracteres no válidos si se pegan
    ciInput.addEventListener('input', () => {
        let value = ciInput.value.replace(/[^0-9]/g, '');
        ciInput.value = value;

        if (value.length < 6) {
            ciError.textContent = "El CI debe tener al menos 6 números.";
            ciError.style.display = 'block';
        } else if (value.length > 8) {
            ciError.textContent = "El CI debe tener máximo 8 números.";
            ciError.style.display = 'block';
            ciInput.value = value.slice(0, 8);
        } else {
            ciError.style.display = 'none';
        }
    });

    // Validación AJAX (CI ya registrado)
    ciInput.addEventListener('blur', () => {
        const ci = ciInput.value.trim();
        if (ci.length >= 6 && ci.length <= 8) {
            fetch(`/cuentas/verificar-ci/?ci=${ci}`)
                .then(response => response.json())
                .then(data => {
                    if (data.existe) {
                        ciError.textContent = "⚠️ Este CI ya está registrado.";
                        ciError.style.display = 'block';
                    } else {
                        ciError.style.display = 'none';
                    }
                })
                .catch(err => console.error("Error verificando CI:", err));
        }
    });

    // ===== Nombres =====
    const nombresInput = document.getElementById('id_nombres');
    let nombresError = document.getElementById('nombres-error');
    if (!nombresError) {
        nombresError = document.createElement('span');
        nombresError.id = 'nombres-error';
        nombresError.className = 'error-message';
        nombresError.style.display = 'none';
        nombresInput.parentNode.appendChild(nombresError);
    }

    nombresInput.addEventListener('input', () => {
        let value = nombresInput.value.replace(/\s+/g, ' ').trimStart();

        if (value.length === 0) {
            nombresError.textContent = "El nombre es obligatorio.";
            nombresError.style.display = 'block';
            return;
        }

        if (/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/.test(value)) {
            nombresError.textContent = "Solo se permiten letras y espacios.";
            nombresError.style.display = 'block';
            nombresInput.value = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
            return;
        }

        const palabras = value.trim().split(' ').filter(p => p.length > 0);

        if (palabras.length > 3) {
            nombresError.textContent = "Solo se permiten hasta 3 palabras.";
            nombresError.style.display = 'block';
            nombresInput.value = palabras.slice(0, 3).join(' ');
            return;
        }

        const palabraCorta = palabras.find(p => p.length < 3);
        if (palabraCorta) {
            nombresError.textContent = "Cada palabra debe tener al menos 3 letras.";
            nombresError.style.display = 'block';
            nombresInput.value = value;
            return;
        }

        if (palabras.length === 3 && value.endsWith(' ')) {
            nombresError.textContent = "Ya no puedes añadir más palabras.";
            nombresError.style.display = 'block';
            nombresInput.value = value.trim();
            return;
        }

        nombresError.style.display = 'none';
        nombresInput.value = value;
    });

    // ===== Apellidos =====
    const apellidosInput = document.getElementById('id_apellidos');
    let apellidosError = document.getElementById('error-apellidos');
    if (!apellidosError) {
        apellidosError = document.createElement('span');
        apellidosError.id = 'error-apellidos';
        apellidosError.className = 'error-message';
        apellidosError.style.display = 'none';
        apellidosInput.parentNode.appendChild(apellidosError);
    }

    apellidosInput.addEventListener('input', () => {
        let value = apellidosInput.value.replace(/\s+/g, ' ').trimStart();

        if (value.length === 0) {
            apellidosError.textContent = "El apellido es obligatorio.";
            apellidosError.style.display = 'block';
            return;
        }

        if (/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/.test(value)) {
            apellidosError.textContent = "Solo se permiten letras y espacios.";
            apellidosError.style.display = 'block';
            apellidosInput.value = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
            return;
        }

        const palabras = value.trim().split(' ').filter(p => p.length > 0);

        if (palabras.length > 2) {
            apellidosError.textContent = "Solo se permiten hasta 2 palabras.";
            apellidosError.style.display = 'block';
            apellidosInput.value = palabras.slice(0, 2).join(' ');
            return;
        }

        const palabraCorta = palabras.find(p => p.length < 3);
        if (palabraCorta) {
            apellidosError.textContent = "Cada palabra debe tener al menos 3 letras.";
            apellidosError.style.display = 'block';
            apellidosInput.value = value;
            return;
        }

        if (palabras.length === 2 && value.endsWith(' ')) {
            apellidosError.textContent = "Ya no puedes añadir más palabras.";
            apellidosError.style.display = 'block';
            apellidosInput.value = value.trim();
            return;
        }

        apellidosError.style.display = 'none';
        apellidosInput.value = value;
    });
});
document.addEventListener('DOMContentLoaded', () => {
    const form = document.querySelector('.form-estudiante'); // tu formulario principal
    const curso = document.getElementById('id_curso');
    const padre = document.getElementById('id_padre');

    // Crear contenedores de error
    const crearError = (input) => {
        let span = document.createElement('span');
        span.className = 'error-message';
        span.style.color = '#dc3545';
        span.style.fontSize = '0.85rem';
        span.style.display = 'block';
        input.parentNode.appendChild(span);
        return span;
    }

    const cursoError = crearError(curso);
    const padreError = crearError(padre);

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
    }

    // Validación en tiempo real
    curso.addEventListener('change', () => validar(curso, cursoError));
    padre.addEventListener('change', () => validar(padre, padreError));

    // Validación al enviar
    form.addEventListener('submit', (e) => {
        const cursoValido = validar(curso, cursoError);
        const padreValido = validar(padre, padreError);

        if (!cursoValido || !padreValido) {
            e.preventDefault();
            alert("Corrige los campos obligatorios antes de guardar.");
        }
    });
});
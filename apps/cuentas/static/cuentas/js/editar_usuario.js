document.addEventListener('DOMContentLoaded', () => {
    // =====================
    // CI: solo lectura (no modificar)
    // =====================
    const ciInput = document.getElementById('id_ci');
    const ciError = document.getElementById('ci-error');
    ciInput.readOnly = true;

    // =====================
    // Nombres
    // =====================
    const nombresInput = document.getElementById('id_nombres');
    const nombresError = document.getElementById('nombres-error');

    const validarNombres = (input, error, maxPalabras) => {
        let value = input.value.replace(/\s+/g, ' ').trimStart();
        if (value.length === 0) {
            error.textContent = `El ${input.placeholder.toLowerCase()} es obligatorio.`;
            error.style.display = 'block';
            return;
        }
        if (/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/.test(value)) {
            error.textContent = "Solo se permiten letras y espacios.";
            input.value = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
            error.style.display = 'block';
            return;
        }

        const palabras = value.trim().split(' ').filter(p => p.length > 0);
        if (palabras.length > maxPalabras) {
            error.textContent = `Solo se permiten hasta ${maxPalabras} palabras.`;
            input.value = palabras.slice(0, maxPalabras).join(' ');
            error.style.display = 'block';
            return;
        }

        if (palabras.some(p => p.length < 3)) {
            error.textContent = "Cada palabra debe tener al menos 3 letras.";
            error.style.display = 'block';
            return;
        }

        if (palabras.length === maxPalabras && value.endsWith(' ')) {
            error.textContent = "Ya no puedes añadir más palabras.";
            input.value = value.trim();
            error.style.display = 'block';
            return;
        }

        error.style.display = 'none';
        input.value = value;
    };

    nombresInput.addEventListener('input', () => validarNombres(nombresInput, nombresError, 3));
    nombresInput.addEventListener('blur', () => nombresInput.value = nombresInput.value.trim());

    // =====================
    // Apellidos
    // =====================
    const apellidosInput = document.getElementById('id_apellidos');
    const apellidosError = document.getElementById('error-apellidos');

    apellidosInput.addEventListener('input', () => validarNombres(apellidosInput, apellidosError, 2));
    apellidosInput.addEventListener('blur', () => apellidosInput.value = apellidosInput.value.trim());

    // =====================
    // Gmail
    // =====================
    const emailInput = document.getElementById('id_email');
    const emailError = document.getElementById('error-email');

    emailInput.addEventListener('input', () => {
        let value = emailInput.value;
        const partes = value.split('@');
        if (partes.length > 1) partes[0] = partes[0].replace(/[^a-zA-Z0-9._-]/g, '');
        else value = value.replace(/[^a-zA-Z0-9._-]/g, '');
        value = partes.join('@');
        emailInput.value = value;

        if (value === '') return emailError.style.display = 'none';

        const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        emailError.style.display = emailRegex.test(value) ? 'none' : 'block';
        if (!emailRegex.test(value)) emailError.textContent = 'Correo inválido. Debe tener formato ejemplo@gmail.com';
    });

    // =====================
    // Teléfono
    // =====================
    const telefonoInput = document.getElementById('id_telefono');
    const telefonoError = document.getElementById('error-telefono');

    telefonoInput.addEventListener('input', () => {
        let value = telefonoInput.value.replace(/[^0-9]/g, ''); // Solo números
        telefonoInput.value = value;

        // Reiniciar error
        telefonoError.textContent = '';
        telefonoError.style.display = 'none';

        if (value.length === 0) {
            telefonoError.textContent = "El teléfono es obligatorio.";
        } else if (value.length < 8) {
            telefonoError.textContent = "El teléfono debe tener exactamente 8 números.";
        } else if (value.length > 8) {
            telefonoError.textContent = "El teléfono debe tener exactamente 8 números.";
            telefonoInput.value = value.slice(0, 8); // Limitar a 8 dígitos
        } else if (!["6", "7"].includes(value[0])) {
            telefonoError.textContent = "El teléfono debe empezar con 6 o 7.";
        }

        // Mostrar error si hay texto
        if (telefonoError.textContent) {
            telefonoError.style.display = 'block';
        }
    });

    // =====================
    // Rol
    // =====================
    const rolSelect = document.getElementById('id_rol');
    const rolError = document.getElementById('error-rol');

    // Variables pasadas desde el template (inyectadas con Django)
    const usuarioLogueadoId = window.usuarioContext.logueadoId;
    const usuarioEditadoId = window.usuarioContext.editadoId;
    const rolEditado = window.usuarioContext.rolEditado;

    // ✅ Si el usuario que se edita es Director y es el mismo usuario logueado
    if (rolEditado === "Director" && usuarioLogueadoId === usuarioEditadoId) {
        rolSelect.disabled = true;
        rolError.textContent = "No puedes cambiar tu propio rol si eres Director.";
        rolError.style.display = 'block';

        // opcional, mejora visual
        rolSelect.title = "No puedes editar tu propio rol siendo Director";
        rolSelect.classList.add('disabled-field');
    } else {
        // 🔁 Validación normal
        rolSelect.addEventListener('change', () => {
            if (!rolSelect.value) {
                rolError.textContent = "Debes seleccionar un rol.";
                rolError.style.display = 'block';
            } else {
                rolError.textContent = '';
                rolError.style.display = 'none';
            }
        });
    }
    // =====================
    // Activo
    // =====================
    const activoInput = document.getElementById('id_is_activo');
    const estadoTexto = document.getElementById('estado-texto');
    estadoTexto.textContent = activoInput.checked ? "Activo" : "Inactivo";

    activoInput.addEventListener('change', () => {
        estadoTexto.textContent = activoInput.checked ? "Activo" : "Inactivo";
    });
});

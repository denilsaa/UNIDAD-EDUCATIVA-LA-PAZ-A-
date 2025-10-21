document.addEventListener('DOMContentLoaded', () => {
    // =====================
    // CI: solo lectura
    // =====================
    const ciInput = document.getElementById('id_ci');
    ciInput.readOnly = true;

    // =====================
    // Nombres
    // =====================
    const nombresInput = document.getElementById('id_nombres');
    const nombresError = document.getElementById('nombres-error');

    nombresInput.addEventListener('input', () => {
        let value = nombresInput.value;
        if (value.length === 0) {
            nombresError.textContent = "El nombre es obligatorio.";
            nombresError.style.display = 'block';
            return;
        }
        value = value.replace(/\s+/g, ' ').trimStart();
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
        if (palabras.some(p => p.length < 3)) {
            nombresError.textContent = "Cada palabra debe tener al menos 3 letras.";
            nombresError.style.display = 'block';
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

    // =====================
    // Apellidos
    // =====================
    const apellidosInput = document.getElementById('id_apellidos');
    const apellidosError = document.getElementById('error-apellidos');

    apellidosInput.addEventListener('input', () => {
        let value = apellidosInput.value;
        if (value.length === 0) {
            apellidosError.textContent = "El apellido es obligatorio.";
            apellidosError.style.display = 'block';
            return;
        }
        value = value.replace(/\s+/g, ' ').trimStart();
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
        if (palabras.some(p => p.length < 3)) {
            apellidosError.textContent = "Cada palabra debe tener al menos 3 letras.";
            apellidosError.style.display = 'block';
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

    // =====================
    // Gmail
    // =====================
    const emailInput = document.getElementById('id_email');
    const emailError = document.getElementById('error-email');

    emailInput.addEventListener('input', () => {
        let value = emailInput.value;
        const partes = value.split('@');
        if (partes.length > 1) {
            partes[0] = partes[0].replace(/[^a-zA-Z0-9._-]/g, '');
            value = partes.join('@');
        } else {
            value = value.replace(/[^a-zA-Z0-9._-]/g, '');
        }
        emailInput.value = value;
        if (value === '') {
            emailError.style.display = 'none';
            return;
        }
        const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailRegex.test(value)) {
            emailError.textContent = 'Correo inválido. Debe tener formato ejemplo@gmail.com';
            emailError.style.display = 'block';
        } else {
            emailError.style.display = 'none';
        }
    });

    // =====================
    // Teléfono
    // =====================
    const telefonoInput = document.getElementById('id_telefono');
    const telefonoError = document.getElementById('error-telefono');

    telefonoInput.addEventListener('input', () => {
        let value = telefonoInput.value.replace(/[^0-9]/g, '');
        telefonoInput.value = value;
        if (value.length === 0) {
            telefonoError.textContent = "El teléfono es obligatorio.";
            telefonoError.style.display = 'block';
            return;
        }
        if (value.length > 8) {
            telefonoError.textContent = "El teléfono debe tener exactamente 8 números.";
            telefonoInput.value = value.slice(0, 8);
            return;
        }
        if (value.length === 8 && !["6", "7"].includes(value[0])) {
            telefonoError.textContent = "El teléfono debe empezar con 6 o 7.";
            telefonoError.style.display = 'block';
            return;
        }
        if (value.length < 8) {
            telefonoError.textContent = "El teléfono debe tener exactamente 8 números.";
            telefonoError.style.display = 'block';
            return;
        }
        telefonoError.style.display = 'none';
    });

    // =====================
    // Rol
    // =====================
    const rolSelect = document.getElementById('id_rol');
    const rolError = document.getElementById('error-rol');

    rolSelect.addEventListener('change', () => {
        if (!rolSelect.value) {
            rolError.textContent = "Debes seleccionar un rol.";
            rolError.style.display = 'block';
        } else {
            rolError.style.display = 'none';
        }
    });

    // =====================
    // Activo
    // =====================
    const activoInput = document.getElementById('id_is_activo');
    activoInput.checked = true;
    // =====================
    // Validación de Contraseña (funcional y probada)
    // =====================
    const newPassInput = document.getElementById('new_password1');

    // Crear el bloque de requisitos dinámicamente
    const passMsg = document.createElement('div');
    passMsg.id = 'pass-msg';
    passMsg.style.marginTop = '8px';
    passMsg.style.fontSize = '0.9rem';
    passMsg.style.display = 'none'; // oculto hasta que escriba algo

    passMsg.innerHTML = `
    <p id="req-length" class="pass-req">• Al menos 9 caracteres</p>
    <p id="req-uppercase" class="pass-req">• Una letra mayúscula</p>
    <p id="req-lowercase" class="pass-req">• Una letra minúscula</p>
    <p id="req-number" class="pass-req">• Un número</p>
    <p id="req-special" class="pass-req">• Un carácter especial</p>
    <p id="req-space" class="pass-req">• No puede contener espacios</p>
    `;

    // Insertar justo debajo del campo de contraseña
    newPassInput.insertAdjacentElement('afterend', passMsg);

    newPassInput.addEventListener('input', () => {
    const value = newPassInput.value;

    // Si está vacío, ocultamos el bloque
    if (value.trim() === '') {
        passMsg.style.display = 'none';
        return;
    }

    // Mostrar los requisitos
    passMsg.style.display = 'block';

    // Requisitos individuales
    const reqLength = document.getElementById('req-length');
    const reqUpper = document.getElementById('req-uppercase');
    const reqLower = document.getElementById('req-lowercase');
    const reqNumber = document.getElementById('req-number');
    const reqSpecial = document.getElementById('req-special');
    const reqSpace = document.getElementById('req-space');

    // Cambiar colores según los requisitos
    reqLength.style.color = value.length >= 9 ? 'green' : '#dc3545';
    reqUpper.style.color = /[A-Z]/.test(value) ? 'green' : '#dc3545';
    reqLower.style.color = /[a-z]/.test(value) ? 'green' : '#dc3545';
    reqNumber.style.color = /\d/.test(value) ? 'green' : '#dc3545';
    reqSpecial.style.color = /[^A-Za-z0-9]/.test(value) ? 'green' : '#dc3545';
    reqSpace.style.color = /\s/.test(value) ? '#dc3545' : 'green';
    });

});


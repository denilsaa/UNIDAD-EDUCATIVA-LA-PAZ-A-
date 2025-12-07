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
    // =====================
    // Cambio de contraseña + Reglas + Checklist
    // =====================
    const form = document.getElementById('editar-usuario-form');
    const pass1 = document.getElementById('new_password1');
    const pass2 = document.getElementById('new_password2');
    const passMsg = document.getElementById('pass-msg');

    const PASSWORD_RULES = {
    min: 8,
    max: 64,
    requireUpper: true,
    requireLower: true,
    requireNumber: true,
    requireSymbol: true
    };

    const setPassMessage = (html, ok = false) => {
    if (!passMsg) return;
    passMsg.innerHTML = html || '';
    passMsg.style.display = html ? 'block' : 'none';
    passMsg.style.color = ok ? '#14804A' : '#B42318';
    };

    const hasUpper = (s) => /[A-ZÁÉÍÓÚÑ]/.test(s);
    const hasLower = (s) => /[a-záéíóúñ]/.test(s);
    const hasNumber = (s) => /\d/.test(s);
    const hasSymbol = (s) => /[^A-Za-zÁÉÍÓÚÑáéíóúñ0-9\s]/.test(s);

    const validatePassword = () => {
    const p1 = pass1 ? pass1.value : '';
    const p2 = pass2 ? pass2.value : '';

    // opcional: si no llenan nada, OK
    if (!p1 && !p2) {
        setPassMessage('');
        pass1 && pass1.setCustomValidity('');
        pass2 && pass2.setCustomValidity('');
        return true;
    }

    if (p1 && !p2) {
        const msg = 'Confirma la contraseña en el segundo campo.';
        setPassMessage(msg);
        pass2.setCustomValidity(msg);
        return false;
    }

    if (!p1 && p2) {
        const msg = 'Escribe la nueva contraseña en el primer campo.';
        setPassMessage(msg);
        pass1.setCustomValidity(msg);
        return false;
    }

    if (p1.length < PASSWORD_RULES.min) {
        const msg = `La contraseña debe tener al menos ${PASSWORD_RULES.min} caracteres.`;
        setPassMessage(msg);
        pass1.setCustomValidity(msg);
        return false;
    }

    if (p1.length > PASSWORD_RULES.max) {
        const msg = `La contraseña no debe superar ${PASSWORD_RULES.max} caracteres.`;
        setPassMessage(msg);
        pass1.setCustomValidity(msg);
        return false;
    }

    if (/\s/.test(p1)) {
        const msg = 'La contraseña no debe contener espacios.';
        setPassMessage(msg);
        pass1.setCustomValidity(msg);
        return false;
    }

    const missing = [];
    if (PASSWORD_RULES.requireUpper && !hasUpper(p1)) missing.push('1 mayúscula');
    if (PASSWORD_RULES.requireLower && !hasLower(p1)) missing.push('1 minúscula');
    if (PASSWORD_RULES.requireNumber && !hasNumber(p1)) missing.push('1 número');
    if (PASSWORD_RULES.requireSymbol && !hasSymbol(p1)) missing.push('1 símbolo');

    if (missing.length) {
        const msg = `Falta: <b>${missing.join(', ')}</b>.`;
        setPassMessage(msg);
        pass1.setCustomValidity('No cumple las reglas de seguridad.');
        return false;
    }

    if (p1 !== p2) {
        const msg = 'Las contraseñas no coinciden.';
        setPassMessage(msg);
        pass2.setCustomValidity(msg);
        return false;
    }

    setPassMessage('Contraseña segura ✅', true);
    pass1 && pass1.setCustomValidity('');
    pass2 && pass2.setCustomValidity('');
    return true;
    };

    // ===== Checklist debajo =====
    const passRulesBox = document.getElementById('pass-rules');

    const renderRules = () => {
    if (!passRulesBox) return;
    passRulesBox.innerHTML = `
        <ul class="rules-list">
        <li data-rule="len">✖ Mínimo ${PASSWORD_RULES.min} caracteres</li>
        <li data-rule="upper">✖ Al menos 1 mayúscula</li>
        <li data-rule="lower">✖ Al menos 1 minúscula</li>
        <li data-rule="number">✖ Al menos 1 número</li>
        <li data-rule="symbol">✖ Al menos 1 símbolo</li>
        <li data-rule="match">✖ Coinciden ambas contraseñas</li>
        </ul>
    `;
    };

    const setRuleState = (rule, ok) => {
    if (!passRulesBox) return;
    const el = passRulesBox.querySelector(`[data-rule="${rule}"]`);
    if (!el) return;

    // Importante: reconstruye el texto sin depender del replace
    const texts = {
        len: `Mínimo ${PASSWORD_RULES.min} caracteres`,
        upper: 'Al menos 1 mayúscula',
        lower: 'Al menos 1 minúscula',
        number: 'Al menos 1 número',
        symbol: 'Al menos 1 símbolo',
        match: 'Coinciden ambas contraseñas'
    };

    el.textContent = `${ok ? '✔' : '✖'} ${texts[rule] || ''}`;
    el.classList.toggle('ok', ok);
    el.classList.toggle('bad', !ok);
    };

    const updateRulesLive = () => {
    const p1 = pass1 ? pass1.value : '';
    const p2 = pass2 ? pass2.value : '';

    // si está vacío, todo en ✖
    setRuleState('len', p1.length >= PASSWORD_RULES.min && p1.length <= PASSWORD_RULES.max);
    setRuleState('upper', hasUpper(p1));
    setRuleState('lower', hasLower(p1));
    setRuleState('number', hasNumber(p1));
    setRuleState('symbol', hasSymbol(p1));
    setRuleState('match', !!p1 && !!p2 && p1 === p2);
    };

    renderRules();
    updateRulesLive();

    // Eventos
    if (pass1) pass1.addEventListener('input', () => { updateRulesLive(); validatePassword(); });
    if (pass2) pass2.addEventListener('input', () => { updateRulesLive(); validatePassword(); });

    if (form) {
    form.addEventListener('submit', (e) => {
        const ok = validatePassword();
        if (!ok) {
        e.preventDefault();
        pass1 && pass1.reportValidity();
        pass2 && pass2.reportValidity();
        }
    });
    }
});

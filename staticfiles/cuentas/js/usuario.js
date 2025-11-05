document.addEventListener('DOMContentLoaded', () => {
    const ciInput = document.getElementById('id_ci');
    const ciError = document.getElementById('ci-error');

    // Impedir escribir letras o espacios directamente
    ciInput.addEventListener('keypress', (e) => {
        const char = e.key;
        if (!/[0-9]/.test(char)) {
            e.preventDefault(); // Bloquea cualquier tecla no numérica
            ciError.textContent = "Solo se permiten números en el CI.";
            ciError.style.display = 'block';
        } else {
            ciError.style.display = 'none';
        }
    });

    // Validar longitud y limpiar caracteres no válidos si se pegan
    ciInput.addEventListener('input', () => {
        let value = ciInput.value.replace(/[^0-9]/g, ''); // Elimina cualquier cosa no numérica
        ciInput.value = value;

        if (value.length < 6) {
            ciError.textContent = "El CI debe tener al menos 6 números.";
            ciError.style.display = 'block';
        } else if (value.length > 9) {
            ciError.textContent = "El CI debe tener máximo 9 números.";
            ciError.style.display = 'block';
            ciInput.value = value.slice(0, 9);
        } else {
            ciError.style.display = 'none';
        }
    });

    // Validación AJAX (CI ya registrado)
    ciInput.addEventListener('blur', () => {
        const ci = ciInput.value.trim();

        if (ci.length >= 6 && ci.length <= 9) {
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
                .catch(err => {
                    console.error("Error verificando CI:", err);
                });
        }
    });
});

// ============================
// VALIDACIÓN EN TIEMPO REAL: NOMBRES
// ============================
const nombresInput = document.getElementById('id_nombres');
const nombresError = document.getElementById('nombres-error');

nombresInput.addEventListener('input', () => {
    let value = nombresInput.value;
    if (value.length === 0) {
        nombresError.textContent = "El nombre es obligatorio.";
        nombresError.style.display = 'block';
        return;
    }
    // Eliminar espacios múltiples o al inicio/final (solo inicio aquí)
    value = value.replace(/\s+/g, ' ').trimStart();
    
    // Solo permitir letras y espacios
    if (/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/.test(value)) {
        nombresError.textContent = "Solo se permiten letras y espacios.";
        nombresError.style.display = 'block';
        nombresInput.value = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
        return;
    }

    // Separar palabras
    const palabras = value.trim().split(' ').filter(p => p.length > 0);

    // Máximo 3 palabras
    if (palabras.length > 3) {
        nombresError.textContent = "Solo se permiten hasta 3 palabras.";
        nombresError.style.display = 'block';
        nombresInput.value = palabras.slice(0, 3).join(' ');
        return;
    }

    // Verificar longitud mínima de cada palabra
    const palabraCorta = palabras.find(p => p.length < 3);
    if (palabraCorta) {
        nombresError.textContent = "Cada palabra debe tener al menos 3 letras.";
        nombresError.style.display = 'block';
        nombresInput.value = value;
        return;
    }

    // Bloquear espacio adicional si ya tiene 3 palabras
    if (palabras.length === 3 && value.endsWith(' ')) {
        nombresError.textContent = "Ya no puedes añadir más palabras.";
        nombresError.style.display = 'block';
        nombresInput.value = value.trim();
        return;
    }

    // Sin errores
    nombresError.style.display = 'none';
    nombresInput.value = value;
});

// ============================
// ELIMINAR ESPACIOS AL INICIO/FINAL AL SALIR DEL CAMPO
// ============================
nombresInput.addEventListener('blur', () => {
    nombresInput.value = nombresInput.value.trim();
});

// =====================
// Validación: Apellidos
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
    // Eliminar espacios múltiples o al inicio/final (solo inicio aquí)
    value = value.replace(/\s+/g, ' ').trimStart();
    
    // Solo permitir letras y espacios
    if (/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/.test(value)) {
        apellidosError.textContent = "Solo se permiten letras y espacios.";
        apellidosError.style.display = 'block';
        apellidosInput.value = value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
        return;
    }

    // Separar palabras
    const palabras = value.trim().split(' ').filter(p => p.length > 0);

    // Máximo 2 palabras
    if (palabras.length > 2) {
        apellidosError.textContent = "Solo se permiten hasta 2 palabras.";
        apellidosError.style.display = 'block';
        apellidosInput.value = palabras.slice(0, 2).join(' ');
        return;
    }

    // Verificar longitud mínima de cada palabra
    const palabraCorta = palabras.find(p => p.length < 3);
    if (palabraCorta) {
        apellidosError.textContent = "Cada palabra debe tener al menos 3 letras.";
        apellidosError.style.display = 'block';
        apellidosInput.value = value;
        return;
    }

    // Bloquear espacio adicional si ya tiene 2 palabras
    if (palabras.length === 2 && value.endsWith(' ')) {
        apellidosError.textContent = "Ya no puedes añadir más palabras.";
        apellidosError.style.display = 'block';
        apellidosInput.value = value.trim();
        return;
    }

    // Sin errores
    apellidosError.style.display = 'none';
    apellidosInput.value = value;
});

// ============================
// ELIMINAR ESPACIOS AL INICIO/FINAL AL SALIR DEL CAMPO
// ============================
apellidosInput.addEventListener('blur', () => {
    apellidosInput.value = apellidosInput.value.trim();
});

// =====================
// Validación: Gmail
// =====================
const emailInput = document.getElementById('id_email');
const emailError = document.getElementById('error-email');

emailInput.addEventListener('input', () => {
    let value = emailInput.value;
    
    // Limpiar caracteres no permitidos (solo letras, números, guiones y guion bajo antes de @)
    const partes = value.split('@');
    if (partes.length > 1) {
        // Solo limpiar la parte antes de @
        partes[0] = partes[0].replace(/[^a-zA-Z0-9._-]/g, '');
        value = partes.join('@');
    } else {
        // Sin @ todavía
        value = value.replace(/[^a-zA-Z0-9._-]/g, '');
    }

    emailInput.value = value;

    // Si está vacío, no mostrar error (campo opcional)
    if (value === '') {
        emailError.style.display = 'none';
        return;
    }

    // Regex simple para validar Gmail u otros correos comunes
    const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    if (!emailRegex.test(value)) {
        emailError.textContent = 'Correo inválido. Debe tener formato ejemplo@gmail.com';
        emailError.style.display = 'block';
    } else {
        emailError.style.display = 'none';
    }
});
// =====================
// Validación: Teléfono
// =====================
document.addEventListener('DOMContentLoaded', () => {
    const telefonoInput = document.getElementById('id_telefono');
    const telefonoError = document.getElementById('error-telefono');

    telefonoInput.addEventListener('input', () => {
        let value = telefonoInput.value.replace(/[^0-9]/g, ''); // Solo números
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

        // Todo correcto
        telefonoError.style.display = 'none';
    });
});
// =====================
// Validación: Rol
// =====================
document.addEventListener('DOMContentLoaded', () => {
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
});

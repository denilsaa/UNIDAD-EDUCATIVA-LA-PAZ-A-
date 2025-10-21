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

    // Eliminar espacios múltiples o al inicio/final
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

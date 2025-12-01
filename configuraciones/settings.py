"""
Django settings for configuraciones project.
"""

from pathlib import Path
import os

# === BASE ===
BASE_DIR = Path(__file__).resolve().parent.parent

# === SEGURIDAD / LOGIN ===

DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    os.environ.get("RENDER_EXTERNAL_HOSTNAME", ""),
]

# 👇 AÑADE ESTO DEBAJO
CSRF_TRUSTED_ORIGINS = [
    f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')}",
]


SECRET_KEY = "django-insecure-if^n0ab85w_-8nsbz5!o^t=dk4%+ml^v&72vpez383d_ohdncf"

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/director/"
LOGOUT_REDIRECT_URL = "/login/"

# === USUARIO PERSONALIZADO ===
AUTH_USER_MODEL = "cuentas.Usuario"

# === APPS ===
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels", 
    # Apps del proyecto
    "apps.cuentas.apps.CuentasConfig",
    "apps.cursos.apps.CursosConfig",
    "apps.estudiantes.apps.EstudiantesConfig",
    "apps.citaciones.apps.CitacionesConfig",
    "apps.notificaciones.apps.NotificacionesConfig",
    "apps.auditoria.apps.AuditoriaConfig",
    "django_extensions",
]

ASGI_APPLICATION = "configuraciones.asgi.application"


AUTHENTICATION_BACKENDS = [
    "apps.cuentas.backends.CustomBackend",
    "django.contrib.auth.backends.ModelBackend",
]

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# === MIDDLEWARE ===
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise debe ir justo después de SecurityMiddleware
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # El throttle puede ir temprano (después de seguridad y estáticos)
    "apps.cuentas.middleware.ThrottleLoginMiddleware",
    "apps.cuentas.middleware.CloseDBConnectionsMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "apps.cuentas.middleware.DisableClientCacheMiddleware",
    "apps.cuentas.middleware.AuthRequiredMiddleware",
    "apps.cuentas.middleware.LastOKURLMiddleware",
    "apps.auditoria.middleware.CurrentRequestMiddleware",
]

ROOT_URLCONF = "configuraciones.urls"

# === TEMPLATES ===
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Si tienes una carpeta /templates global, descomenta la siguiente línea:
        # "DIRS": [BASE_DIR / "templates"],
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.notificaciones.context_processors.notificaciones_panel",

            ],
        },
    },
]

WSGI_APPLICATION = "configuraciones.wsgi.application"

# === BASE DE DATOS ===
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DB_NAME", "beu0hpduvweswzq20pvc"),
        "USER": os.environ.get("DB_USER", "uffjaj6pssk7gxuz"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "SNMfzxXMBbtDLKmHT5Y1"),
        "HOST": os.environ.get("DB_HOST", "beu0hpduvweswzq20pvc-mysql.services.clever-cloud.com"),
        "PORT": os.environ.get("DB_PORT", "3306"),

        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": True,

        "OPTIONS": {
            "charset": "utf8mb4",
            "use_unicode": True,
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# === VALIDADORES DE PASSWORD ===
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# settings.py
LANGUAGE_CODE = "es"
USE_I18N = True

# Si estás en Bolivia:
TIME_ZONE = "America/La_Paz"
USE_TZ = True


# === STATIC (WhiteNoise) ===
STATIC_URL = "/static/"

# Si tienes una carpeta global /static con (css/estilos.css, img/logo.png, etc.), déjala aquí.
# Si NO existe esa carpeta, comenta STATICFILES_DIRS para evitar errores.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Carpeta a la que collectstatic copiará todos los archivos para producción
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Al usar DEBUG=False, sirve estáticos vía WhiteNoise con compresión y hash
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# === PRIMARY KEY POR DEFECTO ===
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

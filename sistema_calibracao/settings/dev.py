from .base import *

# Configurações específicas de desenvolvimento
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            'options': f'-c search_path={env("SCHEMA_DB_NAME")}',
        },
    }
}

LOGIN_URL = "/home"

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# Configurações adicionais para desenvolvimento (opcional)
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

from .base import *

import os

# Configurações específicas de produção
DEBUG = False
ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = []

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}

# Banco de dados para produção
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            'options': '-c search_path=sistema_calibracao',
        },
    }
}

# Configurações para servir arquivos estáticos
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Middleware adicional para produção
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Configurações de segurança para produção (certifique-se de ajustar essas conforme necessário)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

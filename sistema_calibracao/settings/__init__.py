from pathlib import Path
import os
import environ

# Caminho absoluto para o diretório do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

environment = env('DJANGO_ENV')

print(environment)

if environment == 'prod':
    from .prod import *
else:
    from .dev import *
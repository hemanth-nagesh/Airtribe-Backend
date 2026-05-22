import django
import os

# load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    # load .env from project root (or current working dir)
    load_dotenv()
except Exception:
    pass

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# Use local SQLite or override with local PostgreSQL/MySQL via environment variables
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DATABASES_ENGINE'),
        'NAME': os.getenv('DATABASES_NAME'),
        'USER': os.getenv('DATABASES_USER'),
        'PASSWORD': os.getenv('DATABASES_PASSWORD'),
        'HOST': os.getenv('DATABASES_HOST'),
        'PORT': os.getenv('DATABASES_PORT'),
    }
}

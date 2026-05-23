import os

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pulsenotify.settings.local')

app = Celery('pulsenotify')

# Read CELERY_* settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Ensure our task module is imported/registered
app.conf.imports = ('pulsenotify.task',)

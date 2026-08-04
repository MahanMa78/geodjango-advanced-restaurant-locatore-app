import os
from celery import Celery

# Configuring Django settings for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

app = Celery('backend')

# Reading settings from settings.py with the CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Automatic task detection in Django applications
app.autodiscover_tasks()
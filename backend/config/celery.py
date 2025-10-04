import os
from celery import Celery
from celery.schedules import crontab

# Configurar Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Crear instancia de Celery
app = Celery('video_education_system')

# Configurar Celery desde Django settings con namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descubrir tareas en todas las apps instaladas
app.autodiscover_tasks()

# Configurar tareas periódicas
app.conf.beat_schedule = {
    'limpiar-archivos-temporales-diario': {
        'task': 'apps.videos.tasks.limpiar_archivos_temporales_task',
        'schedule': crontab(hour=3, minute=0),  # Diario a las 3:00 AM
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Tarea de debug para verificar que Celery funciona"""
    print(f'Request: {self.request!r}')
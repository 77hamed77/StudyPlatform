import os
from celery import Celery

# استخدام المتغير البيئي REDIS_URL
redis_url = os.environ.get('REDIS_URL', 'redis://red-d1l4fh15pdvs73bgm3cg.render.com:6379/0')

app = Celery('study_platform', broker=redis_url, backend=redis_url)

app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
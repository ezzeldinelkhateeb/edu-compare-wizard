"""
Celery Worker للمعالجة المتوازية
Celery Worker for Parallel Processing
"""

from celery import Celery
import os
import sys
from loguru import logger

# إضافة المسار للاستيراد
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings

settings = get_settings()

# إنشاء تطبيق Celery
celery_app = Celery(
    "educompare_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "celery_app.tasks"
    ]
)

# إعدادات Celery
celery_app.conf.update(
    # المنطقة الزمنية
    timezone='Asia/Riyadh',
    enable_utc=True,
    
    # إعدادات المهام
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,  # ساعة واحدة
    
    # إعدادات Worker
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression='gzip',
    result_compression='gzip',
    
    # إعدادات Route
    task_routes={
        'celery_app.tasks.process_file_comparison': {'queue': 'comparison'},
        'celery_app.tasks.extract_text_from_image': {'queue': 'ocr'},
        'celery_app.tasks.compare_images_visually': {'queue': 'visual'},
        'celery_app.tasks.compare_texts_ai': {'queue': 'ai'},
        'celery_app.tasks.generate_report': {'queue': 'reports'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# تسجيل الـ logging
@celery_app.task(bind=True)
def debug_task(self):
    """مهمة تجريبية للتأكد من عمل Celery"""
    logger.info(f'Request: {self.request!r}')
    return {"status": "success", "message": "Celery is working!"}


if __name__ == '__main__':
    celery_app.start() 
"""
Celery configuration for UnifiedMediaAssetManager.

This module sets up the Celery application for asynchronous task processing,
including agent job processing, video generation, and other background tasks.
"""
import os
from celery import Celery

# Get configuration from environment variables
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Create Celery application
celery_app = Celery(
    'umam',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # Process one task at a time for long-running tasks
    broker_connection_retry_on_startup=True,
)

# Auto-discover tasks from all registered modules
celery_app.autodiscover_tasks(['app.agents'], force=True)

if __name__ == '__main__':
    celery_app.start()

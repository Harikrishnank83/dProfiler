"""
Task queue configuration for dProfiler.

This module configures Celery for distributed task processing
and provides utilities for task queue management.
"""

import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

# Celery configuration
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "dprofiler",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["workers.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "workers.tasks.profile_algorithm_task": {"queue": "profiling"},
        "workers.tasks.register_worker_task": {"queue": "system"},
        "workers.tasks.health_check_task": {"queue": "system"},
        "workers.tasks.cleanup_old_metrics_task": {"queue": "maintenance"},
    },
    
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_always_eager=False,
    
    # Result backend
    result_expires=3600,  # 1 hour
    
    # Worker configuration
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "health-check": {
            "task": "workers.tasks.health_check_task",
            "schedule": 30.0,  # Every 30 seconds
        },
        "cleanup-old-metrics": {
            "task": "workers.tasks.cleanup_old_metrics_task",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
            "args": (7,),  # Keep 7 days of metrics
        },
    },
    
    # Logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
)


class TaskQueue:
    """Task queue manager for dProfiler."""
    
    def __init__(self):
        self.celery_app = celery_app
    
    async def initialize(self):
        """Initialize the task queue."""
        try:
            # Test connection to broker
            self.celery_app.control.inspect().active()
            logger.info("Task queue initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize task queue: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the task queue."""
        try:
            # Close connections
            self.celery_app.control.shutdown()
            logger.info("Task queue shutdown complete")
        except Exception as e:
            logger.error(f"Error during task queue shutdown: {e}")
    
    async def add_job(self, job_id: str, job_data: dict):
        """Add a profiling job to the queue."""
        try:
            # Submit profiling task
            task = self.celery_app.send_task(
                "workers.tasks.profile_algorithm_task",
                args=[
                    job_id,
                    job_data["algorithm_name"],
                    job_data["input_size"],
                    job_data.get("parameters", {})
                ],
                queue="profiling"
            )
            
            logger.info(f"Added job {job_id} to queue with task ID {task.id}")
            return task.id
            
        except Exception as e:
            logger.error(f"Error adding job {job_id} to queue: {e}")
            raise
    
    async def get_task_status(self, task_id: str):
        """Get the status of a task."""
        try:
            task_result = self.celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": task_result.status,
                "result": task_result.result if task_result.ready() else None,
                "info": task_result.info if task_result.ready() else None,
            }
        except Exception as e:
            logger.error(f"Error getting task status for {task_id}: {e}")
            return {"task_id": task_id, "status": "unknown", "error": str(e)}
    
    async def cancel_task(self, task_id: str):
        """Cancel a running task."""
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    async def get_queue_stats(self):
        """Get statistics about the task queues."""
        try:
            inspect = self.celery_app.control.inspect()
            
            stats = {
                "active": inspect.active(),
                "reserved": inspect.reserved(),
                "scheduled": inspect.scheduled(),
                "registered": inspect.registered(),
                "workers": inspect.stats(),
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {"error": str(e)}


# Global task queue instance
task_queue = TaskQueue() 
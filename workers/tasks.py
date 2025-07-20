"""
Celery tasks for dProfiler.

This module defines the Celery tasks for processing profiling jobs
and managing worker nodes.
"""

import os
import logging
import time
import random
from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from workers.task_queue import celery_app
from core.database import get_db_session
from core.models import Job, ProfilingResult, WorkerNode, SystemMetrics
from core.profiler import AlgorithmProfiler

logger = logging.getLogger(__name__)

# Initialize profiler
profiler = AlgorithmProfiler()


@celery_app.task(bind=True)
def profile_algorithm_task(self, job_id: str, algorithm_name: str, 
                          input_size: int, parameters: Dict[str, Any] = None):
    """Task to profile an algorithm."""
    try:
        logger.info(f"Starting profiling task for job {job_id}")
        
        # Update job status to running
        with get_db_session() as db:
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            job.status = "running"
            job.started_at = datetime.now()
            job.worker_id = self.request.id
            db.commit()
        
        # Generate test data
        test_data = list(range(input_size))
        random.shuffle(test_data)
        
        # Profile the algorithm
        if algorithm_name == "bubble_sort":
            from core.profiler import bubble_sort
            result = profiler.profile_function(bubble_sort, algorithm_name, test_data, parameters)
        elif algorithm_name == "quick_sort":
            from core.profiler import quick_sort
            result = profiler.profile_function(quick_sort, algorithm_name, test_data, parameters)
        elif algorithm_name == "merge_sort":
            from core.profiler import merge_sort
            result = profiler.profile_function(merge_sort, algorithm_name, test_data, parameters)
        else:
            # Default to bubble sort for unknown algorithms
            from core.profiler import bubble_sort
            result = profiler.profile_function(bubble_sort, algorithm_name, test_data, parameters)
        
        # Save result to database
        with get_db_session() as db:
            job = db.query(Job).filter(Job.job_id == job_id).first()
            
            profiling_result = ProfilingResult(
                job_id=job.id,
                algorithm_name=result.algorithm_name,
                input_size=result.input_size,
                execution_time=result.execution_time,
                memory_usage=result.memory_usage,
                cpu_usage=result.cpu_usage,
                iterations=result.iterations,
                parameters=result.parameters,
                result_metadata=result.metadata
            )
            
            db.add(profiling_result)
            
            # Update job status
            job.status = "completed"
            job.completed_at = datetime.now()
            
            db.commit()
        
        logger.info(f"Profiling task completed for job {job_id}")
        return {"status": "success", "job_id": job_id}
        
    except Exception as e:
        logger.error(f"Error in profiling task for job {job_id}: {e}")
        
        # Update job status to failed
        try:
            with get_db_session() as db:
                job = db.query(Job).filter(Job.job_id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    job.completed_at = datetime.now()
                    db.commit()
        except Exception as db_error:
            logger.error(f"Error updating job status: {db_error}")
        
        raise


@celery_app.task
def register_worker_task(worker_info: Dict[str, Any]):
    """Task to register a worker node."""
    try:
        with get_db_session() as db:
            # Check if worker already exists
            existing_worker = db.query(WorkerNode).filter(
                WorkerNode.worker_id == worker_info["worker_id"]
            ).first()
            
            if existing_worker:
                # Update existing worker
                existing_worker.hostname = worker_info["hostname"]
                existing_worker.ip_address = worker_info["ip_address"]
                existing_worker.cpu_count = worker_info["cpu_count"]
                existing_worker.memory_total = worker_info["memory_total"]
                existing_worker.status = "active"
                existing_worker.last_heartbeat = datetime.now()
                existing_worker.worker_metadata = worker_info.get("metadata", {})
            else:
                # Create new worker
                worker = WorkerNode(
                    worker_id=worker_info["worker_id"],
                    hostname=worker_info["hostname"],
                    ip_address=worker_info["ip_address"],
                    cpu_count=worker_info["cpu_count"],
                    memory_total=worker_info["memory_total"],
                    status="active",
                    worker_metadata=worker_info.get("metadata", {})
                )
                db.add(worker)
            
            db.commit()
        
        return {"status": "success", "worker_id": worker_info["worker_id"]}
        
    except Exception as e:
        logger.error(f"Error registering worker: {e}")
        raise


@celery_app.task
def health_check_task():
    """Task to perform health check."""
    try:
        import psutil
        
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # Get network stats
        network = psutil.net_io_counters()
        network_in = network.bytes_recv / 1024 / 1024  # MB
        network_out = network.bytes_sent / 1024 / 1024  # MB
        
        # Save metrics to database
        with get_db_session() as db:
            metrics = SystemMetrics(
                worker_id=os.getenv("WORKER_ID", "unknown"),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_in=network_in,
                network_out=network_out,
                active_jobs=0  # TODO: Implement active job counting
            )
            db.add(metrics)
            db.commit()
        
        return {
            "status": "healthy",
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "network_in": network_in,
            "network_out": network_out
        }
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@celery_app.task
def cleanup_old_metrics_task(days: int = 7):
    """Task to cleanup old system metrics."""
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with get_db_session() as db:
            deleted_count = db.query(SystemMetrics).filter(
                SystemMetrics.timestamp < cutoff_date
            ).delete()
            db.commit()
        
        logger.info(f"Cleaned up {deleted_count} old metrics records")
        return {"status": "success", "deleted_count": deleted_count}
        
    except Exception as e:
        logger.error(f"Error cleaning up old metrics: {e}")
        raise 
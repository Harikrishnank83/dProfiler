"""
Main FastAPI application for dProfiler.

This module provides the REST API for job management, result retrieval,
and system monitoring.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import REGISTRY

from core.database import get_db, db_manager, health_check
from core.models import (
    Job, ProfilingResult, WorkerNode, SystemMetrics, AlgorithmRegistry,
    JobCreate, JobResponse, ProfilingResultResponse, WorkerNodeResponse,
    SystemMetricsResponse, JobListResponse, AlgorithmComparisonResponse
)
from core.profiler import AlgorithmProfiler
from workers.task_queue import TaskQueue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
JOB_CREATED = Counter('jobs_created_total', 'Total jobs created')
JOB_COMPLETED = Counter('jobs_completed_total', 'Total jobs completed', ['status'])

# Global instances
profiler = AlgorithmProfiler()
task_queue = TaskQueue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting dProfiler API server...")
    
    # Initialize database
    try:
        db_manager.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize task queue
    try:
        await task_queue.initialize()
        logger.info("Task queue initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize task queue: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down dProfiler API server...")
    await task_queue.shutdown()


# Create FastAPI app
app = FastAPI(
    title="dProfiler API",
    description="Distributed Algorithm Profiling Tool API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware for collecting metrics."""
    start_time = datetime.now()
    
    response = await call_next(request)
    
    # Record metrics
    duration = (datetime.now() - start_time).total_seconds()
    REQUEST_DURATION.observe(duration)
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    return response


@app.get("/health")
async def health():
    """Health check endpoint."""
    return health_check()


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST
    )


@app.post("/api/v1/jobs", response_model=JobResponse)
async def create_job(
    job_data: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Create a new profiling job."""
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create job record
        job = Job(
            job_id=job_id,
            algorithm_name=job_data.algorithm_name,
            input_size=job_data.input_size,
            parameters=job_data.parameters,
            priority=job_data.priority or 0,
            status="pending"
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Add job to task queue
        background_tasks.add_task(task_queue.add_job, job_id, job_data.dict())
        
        # Record metric
        JOB_CREATED.inc()
        
        logger.info(f"Created job {job_id} for algorithm {job_data.algorithm_name}")
        
        return JobResponse.from_orm(job)
        
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    algorithm_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List profiling jobs with pagination and filtering."""
    try:
        query = db.query(Job)
        
        # Apply filters
        if status:
            query = query.filter(Job.status == status)
        if algorithm_name:
            query = query.filter(Job.algorithm_name == algorithm_name)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        jobs = query.offset((page - 1) * per_page).limit(per_page).all()
        
        total_pages = (total + per_page - 1) // per_page
        
        return JobListResponse(
            jobs=[JobResponse.from_orm(job) for job in jobs],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get a specific job by ID."""
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobResponse.from_orm(job)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}/results", response_model=List[ProfilingResultResponse])
async def get_job_results(job_id: str, db: Session = Depends(get_db)):
    """Get results for a specific job."""
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        results = db.query(ProfilingResult).filter(ProfilingResult.job_id == job.id).all()
        return [ProfilingResultResponse.from_orm(result) for result in results]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting results for job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/jobs/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and its results."""
    try:
        job = db.query(Job).filter(Job.job_id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Delete job (cascade will delete results)
        db.delete(job)
        db.commit()
        
        logger.info(f"Deleted job {job_id}")
        return {"message": "Job deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workers", response_model=List[WorkerNodeResponse])
async def list_workers(db: Session = Depends(get_db)):
    """List all worker nodes."""
    try:
        workers = db.query(WorkerNode).all()
        return [WorkerNodeResponse.from_orm(worker) for worker in workers]
        
    except Exception as e:
        logger.error(f"Error listing workers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/workers/{worker_id}", response_model=WorkerNodeResponse)
async def get_worker(worker_id: str, db: Session = Depends(get_db)):
    """Get a specific worker node."""
    try:
        worker = db.query(WorkerNode).filter(WorkerNode.worker_id == worker_id).first()
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")
        
        return WorkerNodeResponse.from_orm(worker)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting worker {worker_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/metrics", response_model=List[SystemMetricsResponse])
async def get_system_metrics(
    worker_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get system metrics."""
    try:
        query = db.query(SystemMetrics)
        
        if worker_id:
            query = query.filter(SystemMetrics.worker_id == worker_id)
        
        metrics = query.order_by(SystemMetrics.timestamp.desc()).limit(limit).all()
        return [SystemMetricsResponse.from_orm(metric) for metric in metrics]
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/compare")
async def compare_algorithms(
    algorithms: List[str],
    input_size: int,
    parameters_list: Optional[List[dict]] = None,
    iterations: int = 1,
    db: Session = Depends(get_db)
):
    """Compare multiple algorithms."""
    try:
        # Generate comparison ID
        comparison_id = str(uuid.uuid4())
        
        # Create jobs for each algorithm
        jobs = []
        for i, algorithm in enumerate(algorithms):
            parameters = parameters_list[i] if parameters_list and i < len(parameters_list) else {}
            
            job = Job(
                job_id=f"{comparison_id}_{algorithm}",
                algorithm_name=algorithm,
                input_size=input_size,
                parameters=parameters,
                status="pending"
            )
            db.add(job)
            jobs.append(job)
        
        db.commit()
        
        # TODO: Implement actual algorithm comparison logic
        # This would involve running the algorithms and collecting results
        
        logger.info(f"Created comparison {comparison_id} for {len(algorithms)} algorithms")
        
        return {
            "comparison_id": comparison_id,
            "algorithms": algorithms,
            "input_size": input_size,
            "status": "pending"
        }
        
    except Exception as e:
        logger.error(f"Error creating algorithm comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/algorithms", response_model=List[dict])
async def list_algorithms():
    """List available algorithms."""
    try:
        # Return built-in algorithms
        algorithms = [
            {
                "name": "bubble_sort",
                "description": "Bubble sort algorithm",
                "category": "sorting",
                "parameters": {}
            },
            {
                "name": "quick_sort",
                "description": "Quick sort algorithm",
                "category": "sorting",
                "parameters": {}
            },
            {
                "name": "merge_sort",
                "description": "Merge sort algorithm",
                "category": "sorting",
                "parameters": {}
            }
        ]
        
        return algorithms
        
    except Exception as e:
        logger.error(f"Error listing algorithms: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 
"""
API endpoints for Machine Learning algorithm profiling.

This module provides REST API endpoints for profiling ML algorithms
using distributed computing frameworks like Dask, Spark, and Ray.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime

from core.database import get_db
from core.ml_profiler import MLProfiler, MLProfilingResult
from core.models import Job, ProfilingResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ml", tags=["Machine Learning Profiling"])

# Global ML profiler instance
ml_profiler = MLProfiler()


class FeatureSelectionRequest:
    """Request model for feature selection profiling."""
    
    def __init__(self, 
                 method: str = "filter",
                 framework: str = "sklearn",
                 dataset_size: int = 10000,
                 n_features: int = 100,
                 n_select: int = 20,
                 iterations: int = 1):
        self.method = method
        self.framework = framework
        self.dataset_size = dataset_size
        self.n_features = n_features
        self.n_select = n_select
        self.iterations = iterations


class HyperparameterTuningRequest:
    """Request model for hyperparameter tuning profiling."""
    
    def __init__(self,
                 algorithm: str = "random_forest",
                 framework: str = "sklearn",
                 dataset_size: int = 5000,
                 n_features: int = 50,
                 iterations: int = 1):
        self.algorithm = algorithm
        self.framework = framework
        self.dataset_size = dataset_size
        self.n_features = n_features
        self.iterations = iterations


class DistributedTrainingRequest:
    """Request model for distributed training profiling."""
    
    def __init__(self,
                 algorithm: str = "random_forest",
                 framework: str = "dask",
                 dataset_size: int = 100000,
                 n_features: int = 100,
                 iterations: int = 1):
        self.algorithm = algorithm
        self.framework = framework
        self.dataset_size = dataset_size
        self.n_features = n_features
        self.iterations = iterations


class FrameworkComparisonRequest:
    """Request model for framework comparison."""
    
    def __init__(self,
                 algorithm: str = "feature_selection",
                 dataset_size: int = 10000,
                 n_features: int = 100):
        self.algorithm = algorithm
        self.dataset_size = dataset_size
        self.n_features = n_features


@router.post("/feature-selection")
async def profile_feature_selection(
    request: FeatureSelectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Profile feature selection algorithms."""
    try:
        # Initialize framework if needed
        if request.framework == "dask":
            ml_profiler.initialize_dask()
        elif request.framework == "spark":
            ml_profiler.initialize_spark()
        elif request.framework == "ray":
            ml_profiler.initialize_ray()
        
        # Run profiling
        result = ml_profiler.profile_feature_selection(
            method=request.method,
            framework=request.framework,
            dataset_size=request.dataset_size,
            n_features=request.n_features,
            n_select=request.n_select,
            iterations=request.iterations
        )
        
        # Store result in database
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            algorithm_name=result.algorithm_name,
            input_size=request.dataset_size,
            parameters={
                "method": request.method,
                "framework": request.framework,
                "n_features": request.n_features,
                "n_select": request.n_select,
                "iterations": request.iterations
            },
            status="completed"
        )
        db.add(job)
        
        # Store profiling result
        profiling_result = ProfilingResult(
            job_id=job.id,
            algorithm_name=result.algorithm_name,
            input_size=request.dataset_size,
            execution_time=result.execution_time,
            memory_usage=result.memory_usage,
            cpu_usage=result.cpu_usage,
            iterations=result.iterations,
            parameters=result.parameters,
            result_metadata={
                "framework": result.framework,
                "selected_features": result.selected_features,
                "feature_count": result.feature_count
            }
        )
        db.add(profiling_result)
        db.commit()
        
        return {
            "job_id": job_id,
            "algorithm_name": result.algorithm_name,
            "framework": result.framework,
            "execution_time": result.execution_time,
            "memory_usage": result.memory_usage,
            "cpu_usage": result.cpu_usage,
            "selected_features_count": len(result.selected_features) if result.selected_features else 0,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error profiling feature selection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hyperparameter-tuning")
async def profile_hyperparameter_tuning(
    request: HyperparameterTuningRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Profile hyperparameter tuning algorithms."""
    try:
        # Initialize framework if needed
        if request.framework == "dask":
            ml_profiler.initialize_dask()
        elif request.framework == "spark":
            ml_profiler.initialize_spark()
        elif request.framework == "ray":
            ml_profiler.initialize_ray()
        
        # Run profiling
        result = ml_profiler.profile_hyperparameter_tuning(
            algorithm=request.algorithm,
            framework=request.framework,
            dataset_size=request.dataset_size,
            n_features=request.n_features,
            iterations=request.iterations
        )
        
        # Store result in database
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            algorithm_name=result.algorithm_name,
            input_size=request.dataset_size,
            parameters={
                "algorithm": request.algorithm,
                "framework": request.framework,
                "n_features": request.n_features,
                "iterations": request.iterations
            },
            status="completed"
        )
        db.add(job)
        
        # Store profiling result
        profiling_result = ProfilingResult(
            job_id=job.id,
            algorithm_name=result.algorithm_name,
            input_size=request.dataset_size,
            execution_time=result.execution_time,
            memory_usage=result.memory_usage,
            cpu_usage=result.cpu_usage,
            iterations=result.iterations,
            parameters=result.parameters,
            result_metadata={
                "framework": result.framework,
                "accuracy": result.accuracy,
                "best_params": result.best_params,
                "feature_count": result.feature_count
            }
        )
        db.add(profiling_result)
        db.commit()
        
        return {
            "job_id": job_id,
            "algorithm_name": result.algorithm_name,
            "framework": result.framework,
            "execution_time": result.execution_time,
            "memory_usage": result.memory_usage,
            "cpu_usage": result.cpu_usage,
            "accuracy": result.accuracy,
            "best_params": result.best_params,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error profiling hyperparameter tuning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/distributed-training")
async def profile_distributed_training(
    request: DistributedTrainingRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Profile distributed model training."""
    try:
        # Initialize framework if needed
        if request.framework == "dask":
            ml_profiler.initialize_dask()
        elif request.framework == "spark":
            ml_profiler.initialize_spark()
        elif request.framework == "ray":
            ml_profiler.initialize_ray()
        
        # Run profiling
        result = ml_profiler.profile_distributed_training(
            algorithm=request.algorithm,
            framework=request.framework,
            dataset_size=request.dataset_size,
            n_features=request.n_features,
            iterations=request.iterations
        )
        
        # Store result in database
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            algorithm_name=result.algorithm_name,
            input_size=request.dataset_size,
            parameters={
                "algorithm": request.algorithm,
                "framework": request.framework,
                "n_features": request.n_features,
                "iterations": request.iterations
            },
            status="completed"
        )
        db.add(job)
        
        # Store profiling result
        profiling_result = ProfilingResult(
            job_id=job.id,
            algorithm_name=result.algorithm_name,
            input_size=request.dataset_size,
            execution_time=result.execution_time,
            memory_usage=result.memory_usage,
            cpu_usage=result.cpu_usage,
            iterations=result.iterations,
            parameters=result.parameters,
            result_metadata={
                "framework": result.framework,
                "accuracy": result.accuracy,
                "feature_count": result.feature_count
            }
        )
        db.add(profiling_result)
        db.commit()
        
        return {
            "job_id": job_id,
            "algorithm_name": result.algorithm_name,
            "framework": result.framework,
            "execution_time": result.execution_time,
            "memory_usage": result.memory_usage,
            "cpu_usage": result.cpu_usage,
            "accuracy": result.accuracy,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error profiling distributed training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare-frameworks")
async def compare_frameworks(
    request: FrameworkComparisonRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Compare performance across different frameworks."""
    try:
        # Initialize all available frameworks
        try:
            ml_profiler.initialize_dask()
        except:
            pass
        
        try:
            ml_profiler.initialize_spark()
        except:
            pass
        
        try:
            ml_profiler.initialize_ray()
        except:
            pass
        
        # Run comparison
        results = ml_profiler.compare_frameworks(
            algorithm=request.algorithm,
            dataset_size=request.dataset_size,
            n_features=request.n_features
        )
        
        # Store results in database
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            algorithm_name=f"{request.algorithm}_framework_comparison",
            input_size=request.dataset_size,
            parameters={
                "algorithm": request.algorithm,
                "dataset_size": request.dataset_size,
                "n_features": request.n_features
            },
            status="completed"
        )
        db.add(job)
        
        # Store all profiling results
        for result in results:
            profiling_result = ProfilingResult(
                job_id=job.id,
                algorithm_name=result.algorithm_name,
                input_size=request.dataset_size,
                execution_time=result.execution_time,
                memory_usage=result.memory_usage,
                cpu_usage=result.cpu_usage,
                iterations=result.iterations,
                parameters=result.parameters,
                result_metadata={
                    "framework": result.framework,
                    "accuracy": result.accuracy,
                    "selected_features": result.selected_features,
                    "best_params": result.best_params,
                    "feature_count": result.feature_count
                }
            )
            db.add(profiling_result)
        
        db.commit()
        
        # Prepare comparison summary
        comparison_results = []
        for result in results:
            comparison_results.append({
                "framework": result.framework,
                "algorithm_name": result.algorithm_name,
                "execution_time": result.execution_time,
                "memory_usage": result.memory_usage,
                "cpu_usage": result.cpu_usage,
                "accuracy": result.accuracy,
                "selected_features_count": len(result.selected_features) if result.selected_features else None,
                "best_params": result.best_params
            })
        
        return {
            "job_id": job_id,
            "comparison_id": str(uuid.uuid4()),
            "algorithm": request.algorithm,
            "dataset_size": request.dataset_size,
            "n_features": request.n_features,
            "results": comparison_results,
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error comparing frameworks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_ml_profiling_summary(db: Session = Depends(get_db)):
    """Get summary of ML profiling results."""
    try:
        summary = ml_profiler.get_summary()
        return summary
    except Exception as e:
        logger.error(f"Error getting ML profiling summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/frameworks/available")
async def get_available_frameworks():
    """Get list of available distributed computing frameworks."""
    from core.ml_profiler import DASK_AVAILABLE, SPARK_AVAILABLE, RAY_AVAILABLE, SKLEARN_AVAILABLE
    
    frameworks = {
        "sklearn": SKLEARN_AVAILABLE,
        "dask": DASK_AVAILABLE,
        "spark": SPARK_AVAILABLE,
        "ray": RAY_AVAILABLE
    }
    
    return {
        "available_frameworks": [k for k, v in frameworks.items() if v],
        "all_frameworks": frameworks
    }


@router.get("/algorithms/supported")
async def get_supported_algorithms():
    """Get list of supported ML algorithms."""
    return {
        "feature_selection": {
            "methods": ["filter", "wrapper", "embedded"],
            "frameworks": ["sklearn", "dask", "spark"]
        },
        "hyperparameter_tuning": {
            "algorithms": ["random_forest", "logistic_regression"],
            "frameworks": ["sklearn", "ray"]
        },
        "distributed_training": {
            "algorithms": ["random_forest"],
            "frameworks": ["dask", "spark"]
        }
    }


@router.post("/cleanup")
async def cleanup_resources():
    """Clean up distributed computing resources."""
    try:
        ml_profiler.cleanup()
        return {"message": "Resources cleaned up successfully"}
    except Exception as e:
        logger.error(f"Error cleaning up resources: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 
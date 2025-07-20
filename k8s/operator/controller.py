#!/usr/bin/env python3
"""
dProfiler Kubernetes Operator Controller

This module implements a Kubernetes operator that manages AlgorithmProfiling
and AlgorithmComparison custom resources. It integrates with the dProfiler
API to execute profiling jobs and update resource status.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
import kubernetes
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# dProfiler API configuration
DPROFILER_API_URL = "http://dprofiler-api-service:8000"
API_TIMEOUT = 30


class DProfilerOperator:
    """Kubernetes Operator for dProfiler Custom Resources."""
    
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.api_client = None
        self.core_v1_api = None
        self.custom_objects_api = None
        self.dprofiler_api_client = None
        
        # Initialize Kubernetes client
        try:
            config.load_incluster_config()  # In-cluster config
        except config.ConfigException:
            config.load_kube_config()  # Local development
        
        self.api_client = client.ApiClient()
        self.core_v1_api = client.CoreV1Api(self.api_client)
        self.custom_objects_api = client.CustomObjectsApi(self.api_client)
        
        # Initialize dProfiler API client
        self.dprofiler_api_client = httpx.AsyncClient(
            base_url=DPROFILER_API_URL,
            timeout=API_TIMEOUT
        )
    
    async def start(self):
        """Start the operator controller."""
        logger.info(f"Starting dProfiler Operator in namespace: {self.namespace}")
        
        # Start watching for custom resources
        await asyncio.gather(
            self.watch_algorithm_profilings(),
            self.watch_algorithm_comparisons()
        )
    
    async def watch_algorithm_profilings(self):
        """Watch for AlgorithmProfiling custom resources."""
        logger.info("Starting to watch AlgorithmProfiling resources")
        
        while True:
            try:
                w = watch.Watch()
                for event in w.stream(
                    self.custom_objects_api.list_namespaced_custom_object,
                    group="dprofiler.io",
                    version="v1alpha1",
                    namespace=self.namespace,
                    plural="algorithmprofilings"
                ):
                    await self.handle_algorithm_profiling_event(event)
            except Exception as e:
                logger.error(f"Error watching AlgorithmProfiling: {e}")
                await asyncio.sleep(5)
    
    async def watch_algorithm_comparisons(self):
        """Watch for AlgorithmComparison custom resources."""
        logger.info("Starting to watch AlgorithmComparison resources")
        
        while True:
            try:
                w = watch.Watch()
                for event in w.stream(
                    self.custom_objects_api.list_namespaced_custom_object,
                    group="dprofiler.io",
                    version="v1alpha1",
                    namespace=self.namespace,
                    plural="algorithmcomparisons"
                ):
                    await self.handle_algorithm_comparison_event(event)
            except Exception as e:
                logger.error(f"Error watching AlgorithmComparison: {e}")
                await asyncio.sleep(5)
    
    async def handle_algorithm_profiling_event(self, event):
        """Handle AlgorithmProfiling events."""
        event_type = event['type']
        obj = event['object']
        name = obj['metadata']['name']
        
        logger.info(f"AlgorithmProfiling {event_type}: {name}")
        
        if event_type == 'ADDED':
            await self.create_algorithm_profiling_job(obj)
        elif event_type == 'MODIFIED':
            await self.update_algorithm_profiling_status(obj)
        elif event_type == 'DELETED':
            await self.cleanup_algorithm_profiling_job(obj)
    
    async def handle_algorithm_comparison_event(self, event):
        """Handle AlgorithmComparison events."""
        event_type = event['type']
        obj = event['object']
        name = obj['metadata']['name']
        
        logger.info(f"AlgorithmComparison {event_type}: {name}")
        
        if event_type == 'ADDED':
            await self.create_algorithm_comparison_job(obj)
        elif event_type == 'MODIFIED':
            await self.update_algorithm_comparison_status(obj)
        elif event_type == 'DELETED':
            await self.cleanup_algorithm_comparison_job(obj)
    
    async def create_algorithm_profiling_job(self, obj):
        """Create a profiling job for AlgorithmProfiling resource."""
        name = obj['metadata']['name']
        spec = obj['spec']
        
        try:
            # Update status to Running
            await self.update_algorithm_profiling_phase(obj, 'Running')
            
            # Determine job type and create appropriate job
            algorithm_type = spec.get('algorithmType', 'sorting')
            
            if algorithm_type == 'ml':
                await self.create_ml_profiling_job(obj)
            elif algorithm_type == 'custom':
                await self.create_custom_profiling_job(obj)
            else:
                await self.create_sorting_profiling_job(obj)
                
        except Exception as e:
            logger.error(f"Error creating profiling job for {name}: {e}")
            await self.update_algorithm_profiling_phase(obj, 'Failed', str(e))
    
    async def create_sorting_profiling_job(self, obj):
        """Create a sorting algorithm profiling job."""
        name = obj['metadata']['name']
        spec = obj['spec']
        
        job_data = {
            "algorithm_name": spec['algorithmName'],
            "input_size": spec['inputSize'],
            "parameters": spec.get('parameters', {}),
            "priority": spec.get('priority', 5)
        }
        
        try:
            response = await self.dprofiler_api_client.post(
                "/api/v1/jobs",
                json=job_data
            )
            response.raise_for_status()
            
            job_result = response.json()
            job_id = job_result['job_id']
            
            # Update status with job ID
            await self.update_algorithm_profiling_job_id(obj, job_id)
            
            # Monitor job completion
            await self.monitor_profiling_job(obj, job_id)
            
        except Exception as e:
            logger.error(f"Error creating sorting job for {name}: {e}")
            raise
    
    async def create_ml_profiling_job(self, obj):
        """Create an ML algorithm profiling job."""
        name = obj['metadata']['name']
        spec = obj['spec']
        ml_config = spec.get('mlConfig', {})
        
        task = ml_config.get('task', 'feature_selection')
        framework = ml_config.get('framework', 'sklearn')
        
        if task == 'feature_selection':
            job_data = {
                "method": "filter",
                "framework": framework,
                "dataset_size": ml_config.get('datasetSize', 10000),
                "n_features": ml_config.get('nFeatures', 100),
                "n_select": ml_config.get('nSelect', 20),
                "iterations": spec.get('iterations', 1)
            }
            
            response = await self.dprofiler_api_client.post(
                "/api/v1/ml/feature-selection",
                json=job_data
            )
            
        elif task == 'hyperparameter_tuning':
            job_data = {
                "algorithm": ml_config.get('algorithm', 'random_forest'),
                "framework": framework,
                "dataset_size": ml_config.get('datasetSize', 5000),
                "n_features": ml_config.get('nFeatures', 50),
                "iterations": spec.get('iterations', 1)
            }
            
            response = await self.dprofiler_api_client.post(
                "/api/v1/ml/hyperparameter-tuning",
                json=job_data
            )
            
        elif task == 'distributed_training':
            job_data = {
                "algorithm": ml_config.get('algorithm', 'random_forest'),
                "framework": framework,
                "dataset_size": ml_config.get('datasetSize', 100000),
                "n_features": ml_config.get('nFeatures', 100),
                "iterations": spec.get('iterations', 1)
            }
            
            response = await self.dprofiler_api_client.post(
                "/api/v1/ml/distributed-training",
                json=job_data
            )
        
        response.raise_for_status()
        job_result = response.json()
        job_id = job_result['job_id']
        
        # Update status with job ID
        await self.update_algorithm_profiling_job_id(obj, job_id)
        
        # For ML jobs, results are immediate
        await self.update_algorithm_profiling_results(obj, job_result)
    
    async def create_custom_profiling_job(self, obj):
        """Create a custom algorithm profiling job using Kubernetes Job."""
        name = obj['metadata']['name']
        spec = obj['spec']
        custom_config = spec.get('customConfig', {})
        
        # Create Kubernetes Job for custom algorithm
        job = client.V1Job(
            metadata=client.V1ObjectMeta(
                name=f"dprofiler-{name}",
                namespace=self.namespace,
                labels={
                    "app": "dprofiler",
                    "type": "custom-algorithm",
                    "algorithm": name
                }
            ),
            spec=client.V1JobSpec(
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={
                            "app": "dprofiler",
                            "type": "custom-algorithm",
                            "algorithm": name
                        }
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name="algorithm",
                                image=custom_config.get('image', 'alpine:latest'),
                                command=custom_config.get('command', ['echo']),
                                args=custom_config.get('args', ['Hello World']),
                                env=[
                                    client.V1EnvVar(
                                        name=env['name'],
                                        value=env['value']
                                    ) for env in custom_config.get('env', [])
                                ],
                                resources=client.V1ResourceRequirements(
                                    requests=spec.get('resources', {}).get('requests', {}),
                                    limits=spec.get('resources', {}).get('limits', {})
                                )
                            )
                        ],
                        restart_policy="Never"
                    )
                )
            )
        )
        
        try:
            batch_v1_api = client.BatchV1Api(self.api_client)
            created_job = batch_v1_api.create_namespaced_job(
                namespace=self.namespace,
                body=job
            )
            
            # Update status with job ID
            await self.update_algorithm_profiling_job_id(obj, created_job.metadata.name)
            
            # Monitor custom job completion
            await self.monitor_custom_job(obj, created_job.metadata.name)
            
        except Exception as e:
            logger.error(f"Error creating custom job for {name}: {e}")
            raise
    
    async def create_algorithm_comparison_job(self, obj):
        """Create a comparison job for AlgorithmComparison resource."""
        name = obj['metadata']['name']
        spec = obj['spec']
        
        try:
            # Update status to Running
            await self.update_algorithm_comparison_phase(obj, 'Running')
            
            # Create comparison job
            comparison_data = {
                "algorithm": "feature_selection",  # Default, can be made configurable
                "dataset_size": spec['inputSize'],
                "n_features": 100  # Default, can be made configurable
            }
            
            response = await self.dprofiler_api_client.post(
                "/api/v1/ml/compare-frameworks",
                json=comparison_data
            )
            response.raise_for_status()
            
            comparison_result = response.json()
            comparison_id = comparison_result['comparison_id']
            
            # Update status with comparison ID
            await self.update_algorithm_comparison_id(obj, comparison_id)
            
            # Update results
            await self.update_algorithm_comparison_results(obj, comparison_result)
            
        except Exception as e:
            logger.error(f"Error creating comparison job for {name}: {e}")
            await self.update_algorithm_comparison_phase(obj, 'Failed', str(e))
    
    async def monitor_profiling_job(self, obj, job_id: str):
        """Monitor a profiling job until completion."""
        name = obj['metadata']['name']
        
        while True:
            try:
                response = await self.dprofiler_api_client.get(f"/api/v1/jobs/{job_id}")
                response.raise_for_status()
                
                job_status = response.json()
                status = job_status['status']
                
                if status == 'completed':
                    # Get results
                    results_response = await self.dprofiler_api_client.get(f"/api/v1/jobs/{job_id}/results")
                    results_response.raise_for_status()
                    results = results_response.json()
                    
                    await self.update_algorithm_profiling_results(obj, results[0] if results else {})
                    break
                    
                elif status == 'failed':
                    await self.update_algorithm_profiling_phase(obj, 'Failed', 'Job failed')
                    break
                
                await asyncio.sleep(10)  # Poll every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring job {job_id}: {e}")
                await asyncio.sleep(30)
    
    async def monitor_custom_job(self, obj, job_name: str):
        """Monitor a custom Kubernetes job until completion."""
        name = obj['metadata']['name']
        
        while True:
            try:
                batch_v1_api = client.BatchV1Api(self.api_client)
                job = batch_v1_api.read_namespaced_job(
                    name=job_name,
                    namespace=self.namespace
                )
                
                if job.status.succeeded:
                    # Job completed successfully
                    await self.update_algorithm_profiling_phase(obj, 'Completed')
                    break
                    
                elif job.status.failed:
                    # Job failed
                    await self.update_algorithm_profiling_phase(obj, 'Failed', 'Custom job failed')
                    break
                
                await asyncio.sleep(10)  # Poll every 10 seconds
                
            except Exception as e:
                logger.error(f"Error monitoring custom job {job_name}: {e}")
                await asyncio.sleep(30)
    
    async def update_algorithm_profiling_phase(self, obj, phase: str, message: str = None):
        """Update AlgorithmProfiling phase."""
        name = obj['metadata']['name']
        
        patch = {
            "status": {
                "phase": phase,
                "conditions": [
                    {
                        "type": "Ready",
                        "status": "True" if phase == "Completed" else "False",
                        "lastTransitionTime": datetime.utcnow().isoformat() + "Z",
                        "reason": phase,
                        "message": message or f"Algorithm profiling {phase.lower()}"
                    }
                ]
            }
        }
        
        if phase == "Running":
            patch["status"]["startTime"] = datetime.utcnow().isoformat() + "Z"
        elif phase in ["Completed", "Failed"]:
            patch["status"]["completionTime"] = datetime.utcnow().isoformat() + "Z"
        
        try:
            self.custom_objects_api.patch_namespaced_custom_object_status(
                group="dprofiler.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="algorithmprofilings",
                name=name,
                body=patch
            )
        except Exception as e:
            logger.error(f"Error updating phase for {name}: {e}")
    
    async def update_algorithm_profiling_job_id(self, obj, job_id: str):
        """Update AlgorithmProfiling with job ID."""
        name = obj['metadata']['name']
        
        patch = {
            "status": {
                "jobId": job_id
            }
        }
        
        try:
            self.custom_objects_api.patch_namespaced_custom_object_status(
                group="dprofiler.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="algorithmprofilings",
                name=name,
                body=patch
            )
        except Exception as e:
            logger.error(f"Error updating job ID for {name}: {e}")
    
    async def update_algorithm_profiling_results(self, obj, results: Dict[str, Any]):
        """Update AlgorithmProfiling with results."""
        name = obj['metadata']['name']
        
        patch = {
            "status": {
                "results": {
                    "executionTime": results.get('execution_time', 0),
                    "memoryUsage": results.get('memory_usage', 0),
                    "cpuUsage": results.get('cpu_usage', 0),
                    "iterations": results.get('iterations', 1),
                    "metrics": results.get('result_metadata', {}),
                    "mlResults": {
                        "accuracy": results.get('accuracy'),
                        "selectedFeatures": results.get('selected_features'),
                        "bestParams": results.get('best_params'),
                        "framework": results.get('framework')
                    }
                }
            }
        }
        
        try:
            self.custom_objects_api.patch_namespaced_custom_object_status(
                group="dprofiler.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="algorithmprofilings",
                name=name,
                body=patch
            )
        except Exception as e:
            logger.error(f"Error updating results for {name}: {e}")
    
    async def update_algorithm_comparison_phase(self, obj, phase: str, message: str = None):
        """Update AlgorithmComparison phase."""
        name = obj['metadata']['name']
        
        patch = {
            "status": {
                "phase": phase,
                "conditions": [
                    {
                        "type": "Ready",
                        "status": "True" if phase == "Completed" else "False",
                        "lastTransitionTime": datetime.utcnow().isoformat() + "Z",
                        "reason": phase,
                        "message": message or f"Algorithm comparison {phase.lower()}"
                    }
                ]
            }
        }
        
        if phase == "Running":
            patch["status"]["startTime"] = datetime.utcnow().isoformat() + "Z"
        elif phase in ["Completed", "Failed"]:
            patch["status"]["completionTime"] = datetime.utcnow().isoformat() + "Z"
        
        try:
            self.custom_objects_api.patch_namespaced_custom_object_status(
                group="dprofiler.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="algorithmcomparisons",
                name=name,
                body=patch
            )
        except Exception as e:
            logger.error(f"Error updating comparison phase for {name}: {e}")
    
    async def update_algorithm_comparison_id(self, obj, comparison_id: str):
        """Update AlgorithmComparison with comparison ID."""
        name = obj['metadata']['name']
        
        patch = {
            "status": {
                "comparisonId": comparison_id
            }
        }
        
        try:
            self.custom_objects_api.patch_namespaced_custom_object_status(
                group="dprofiler.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="algorithmcomparisons",
                name=name,
                body=patch
            )
        except Exception as e:
            logger.error(f"Error updating comparison ID for {name}: {e}")
    
    async def update_algorithm_comparison_results(self, obj, results: Dict[str, Any]):
        """Update AlgorithmComparison with results."""
        name = obj['metadata']['name']
        
        patch = {
            "status": {
                "results": results.get('results', [])
            }
        }
        
        try:
            self.custom_objects_api.patch_namespaced_custom_object_status(
                group="dprofiler.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="algorithmcomparisons",
                name=name,
                body=patch
            )
        except Exception as e:
            logger.error(f"Error updating comparison results for {name}: {e}")
    
    async def cleanup_algorithm_profiling_job(self, obj):
        """Clean up resources when AlgorithmProfiling is deleted."""
        name = obj['metadata']['name']
        job_id = obj['status'].get('jobId')
        
        if job_id:
            try:
                # Delete the job from dProfiler API
                await self.dprofiler_api_client.delete(f"/api/v1/jobs/{job_id}")
                logger.info(f"Cleaned up profiling job {job_id} for {name}")
            except Exception as e:
                logger.error(f"Error cleaning up job {job_id}: {e}")
    
    async def cleanup_algorithm_comparison_job(self, obj):
        """Clean up resources when AlgorithmComparison is deleted."""
        name = obj['metadata']['name']
        logger.info(f"Cleaned up comparison {name}")


async def main():
    """Main entry point for the operator."""
    import os
    
    namespace = os.getenv('WATCH_NAMESPACE', 'default')
    operator = DProfilerOperator(namespace=namespace)
    
    try:
        await operator.start()
    except KeyboardInterrupt:
        logger.info("Operator stopped by user")
    except Exception as e:
        logger.error(f"Operator failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 
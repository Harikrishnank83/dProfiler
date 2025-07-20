#!/usr/bin/env python3
"""
dProfiler Kubeflow Component

This component integrates dProfiler with Kubeflow pipelines, allowing
ML practitioners to profile algorithms and compare frameworks as part
of their ML workflows.
"""

import argparse
import json
import logging
import time
from typing import Dict, Any, List, Optional
import yaml
import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DProfilerKubeflowComponent:
    """Kubeflow component for dProfiler integration."""
    
    def __init__(self, namespace: str = "default"):
        self.namespace = namespace
        self.api_client = None
        self.custom_objects_api = None
        
        # Initialize Kubernetes client
        try:
            config.load_incluster_config()  # In-cluster config
        except config.ConfigException:
            config.load_kube_config()  # Local development
        
        self.api_client = client.ApiClient()
        self.custom_objects_api = client.CustomObjectsApi(self.api_client)
    
    def create_algorithm_profiling(self, 
                                 name: str,
                                 algorithm_name: str,
                                 algorithm_type: str,
                                 input_size: int,
                                 **kwargs) -> Dict[str, Any]:
        """Create an AlgorithmProfiling custom resource."""
        
        # Build the custom resource object
        cr_object = {
            "apiVersion": "dprofiler.io/v1alpha1",
            "kind": "AlgorithmProfiling",
            "metadata": {
                "name": name,
                "namespace": self.namespace,
                "labels": {
                    "app": "dprofiler",
                    "type": algorithm_type,
                    "kubeflow-component": "true"
                }
            },
            "spec": {
                "algorithmName": algorithm_name,
                "algorithmType": algorithm_type,
                "inputSize": input_size,
                "iterations": kwargs.get('iterations', 1),
                "priority": kwargs.get('priority', 5),
                "timeout": kwargs.get('timeout', '1h'),
                "parameters": kwargs.get('parameters', {}),
                "resources": kwargs.get('resources', {})
            }
        }
        
        # Add ML-specific configuration
        if algorithm_type == 'ml':
            cr_object["spec"]["mlConfig"] = {
                "framework": kwargs.get('framework', 'sklearn'),
                "task": kwargs.get('task', 'feature_selection'),
                "datasetSize": kwargs.get('dataset_size', input_size),
                "nFeatures": kwargs.get('n_features', 100),
                "nSelect": kwargs.get('n_select', 20),
                "algorithm": kwargs.get('ml_algorithm', 'random_forest')
            }
        
        # Add custom algorithm configuration
        elif algorithm_type == 'custom':
            cr_object["spec"]["customConfig"] = {
                "image": kwargs.get('image', 'alpine:latest'),
                "command": kwargs.get('command', ['echo']),
                "args": kwargs.get('args', ['Hello World']),
                "env": kwargs.get('env', []),
                "volumes": kwargs.get('volumes', [])
            }
        
        try:
            # Create the custom resource
            result = self.custom_objects_api.create_namespaced_custom_object(
                group="dprofiler.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="algorithmprofilings",
                body=cr_object
            )
            
            logger.info(f"Created AlgorithmProfiling: {name}")
            return result
            
        except ApiException as e:
            logger.error(f"Error creating AlgorithmProfiling {name}: {e}")
            raise
    
    def create_algorithm_comparison(self,
                                  name: str,
                                  algorithms: List[Dict[str, Any]],
                                  input_size: int,
                                  **kwargs) -> Dict[str, Any]:
        """Create an AlgorithmComparison custom resource."""
        
        # Build the custom resource object
        cr_object = {
            "apiVersion": "dprofiler.io/v1alpha1",
            "kind": "AlgorithmComparison",
            "metadata": {
                "name": name,
                "namespace": self.namespace,
                "labels": {
                    "app": "dprofiler",
                    "type": "comparison",
                    "kubeflow-component": "true"
                }
            },
            "spec": {
                "algorithms": algorithms,
                "inputSize": input_size,
                "iterations": kwargs.get('iterations', 1),
                "timeout": kwargs.get('timeout', '2h'),
                "parallel": kwargs.get('parallel', False)
            }
        }
        
        try:
            # Create the custom resource
            result = self.custom_objects_api.create_namespaced_custom_object(
                group="dprofiler.io",
                version="v1alpha1",
                namespace=self.namespace,
                plural="algorithmcomparisons",
                name=name,
                body=cr_object
            )
            
            logger.info(f"Created AlgorithmComparison: {name}")
            return result
            
        except ApiException as e:
            logger.error(f"Error creating AlgorithmComparison {name}: {e}")
            raise
    
    def wait_for_completion(self, resource_type: str, name: str, timeout: int = 3600) -> Dict[str, Any]:
        """Wait for a custom resource to complete."""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if resource_type == 'AlgorithmProfiling':
                    result = self.custom_objects_api.get_namespaced_custom_object(
                        group="dprofiler.io",
                        version="v1alpha1",
                        namespace=self.namespace,
                        plural="algorithmprofilings",
                        name=name
                    )
                elif resource_type == 'AlgorithmComparison':
                    result = self.custom_objects_api.get_namespaced_custom_object(
                        group="dprofiler.io",
                        version="v1alpha1",
                        namespace=self.namespace,
                        plural="algorithmcomparisons",
                        name=name
                    )
                else:
                    raise ValueError(f"Unknown resource type: {resource_type}")
                
                status = result.get('status', {})
                phase = status.get('phase', 'Pending')
                
                logger.info(f"{resource_type} {name} status: {phase}")
                
                if phase in ['Completed', 'Failed']:
                    return result
                
                time.sleep(10)  # Poll every 10 seconds
                
            except ApiException as e:
                logger.error(f"Error checking status of {resource_type} {name}: {e}")
                time.sleep(30)
        
        raise TimeoutError(f"Timeout waiting for {resource_type} {name} to complete")
    
    def get_results(self, resource_type: str, name: str) -> Dict[str, Any]:
        """Get results from a completed custom resource."""
        
        try:
            if resource_type == 'AlgorithmProfiling':
                result = self.custom_objects_api.get_namespaced_custom_object(
                    group="dprofiler.io",
                    version="v1alpha1",
                    namespace=self.namespace,
                    plural="algorithmprofilings",
                    name=name
                )
            elif resource_type == 'AlgorithmComparison':
                result = self.custom_objects_api.get_namespaced_custom_object(
                    group="dprofiler.io",
                    version="v1alpha1",
                    namespace=self.namespace,
                    plural="algorithmcomparisons",
                    name=name
                )
            else:
                raise ValueError(f"Unknown resource type: {resource_type}")
            
            return result.get('status', {}).get('results', {})
            
        except ApiException as e:
            logger.error(f"Error getting results for {resource_type} {name}: {e}")
            raise


def main():
    """Main entry point for the Kubeflow component."""
    parser = argparse.ArgumentParser(description='dProfiler Kubeflow Component')
    parser.add_argument('--action', required=True, 
                       choices=['profile', 'compare', 'wait', 'get-results'],
                       help='Action to perform')
    parser.add_argument('--name', required=True, help='Resource name')
    parser.add_argument('--namespace', default='default', help='Kubernetes namespace')
    parser.add_argument('--resource-type', choices=['AlgorithmProfiling', 'AlgorithmComparison'],
                       help='Type of resource (for wait and get-results actions)')
    
    # Profiling arguments
    parser.add_argument('--algorithm-name', help='Algorithm name')
    parser.add_argument('--algorithm-type', choices=['sorting', 'ml', 'custom'],
                       help='Algorithm type')
    parser.add_argument('--input-size', type=int, help='Input size')
    parser.add_argument('--iterations', type=int, default=1, help='Number of iterations')
    parser.add_argument('--priority', type=int, default=5, help='Job priority')
    parser.add_argument('--timeout', default='1h', help='Job timeout')
    
    # ML-specific arguments
    parser.add_argument('--framework', choices=['sklearn', 'dask', 'spark', 'ray'],
                       help='ML framework')
    parser.add_argument('--task', choices=['feature_selection', 'hyperparameter_tuning', 'distributed_training'],
                       help='ML task type')
    parser.add_argument('--dataset-size', type=int, help='Dataset size')
    parser.add_argument('--n-features', type=int, help='Number of features')
    parser.add_argument('--n-select', type=int, help='Number of features to select')
    parser.add_argument('--ml-algorithm', help='ML algorithm name')
    
    # Custom algorithm arguments
    parser.add_argument('--image', help='Docker image for custom algorithm')
    parser.add_argument('--command', nargs='+', help='Command for custom algorithm')
    parser.add_argument('--args', nargs='+', help='Arguments for custom algorithm')
    
    # Comparison arguments
    parser.add_argument('--algorithms-file', help='JSON file containing algorithms list')
    
    # Output arguments
    parser.add_argument('--output-file', help='Output file for results')
    parser.add_argument('--wait-timeout', type=int, default=3600, help='Wait timeout in seconds')
    
    args = parser.parse_args()
    
    # Initialize component
    component = DProfilerKubeflowComponent(namespace=args.namespace)
    
    try:
        if args.action == 'profile':
            # Create algorithm profiling
            kwargs = {
                'iterations': args.iterations,
                'priority': args.priority,
                'timeout': args.timeout
            }
            
            if args.algorithm_type == 'ml':
                kwargs.update({
                    'framework': args.framework,
                    'task': args.task,
                    'dataset_size': args.dataset_size,
                    'n_features': args.n_features,
                    'n_select': args.n_select,
                    'ml_algorithm': args.ml_algorithm
                })
            elif args.algorithm_type == 'custom':
                kwargs.update({
                    'image': args.image,
                    'command': args.command,
                    'args': args.args
                })
            
            result = component.create_algorithm_profiling(
                name=args.name,
                algorithm_name=args.algorithm_name,
                algorithm_type=args.algorithm_type,
                input_size=args.input_size,
                **kwargs
            )
            
            print(f"Created AlgorithmProfiling: {args.name}")
            
        elif args.action == 'compare':
            # Create algorithm comparison
            if not args.algorithms_file:
                raise ValueError("--algorithms-file is required for comparison")
            
            with open(args.algorithms_file, 'r') as f:
                algorithms = json.load(f)
            
            result = component.create_algorithm_comparison(
                name=args.name,
                algorithms=algorithms,
                input_size=args.input_size,
                iterations=args.iterations,
                timeout=args.timeout,
                parallel=True  # Default to parallel for comparisons
            )
            
            print(f"Created AlgorithmComparison: {args.name}")
            
        elif args.action == 'wait':
            # Wait for completion
            if not args.resource_type:
                raise ValueError("--resource-type is required for wait action")
            
            result = component.wait_for_completion(
                resource_type=args.resource_type,
                name=args.name,
                timeout=args.wait_timeout
            )
            
            print(f"{args.resource_type} {args.name} completed with status: {result.get('status', {}).get('phase')}")
            
        elif args.action == 'get-results':
            # Get results
            if not args.resource_type:
                raise ValueError("--resource-type is required for get-results action")
            
            results = component.get_results(
                resource_type=args.resource_type,
                name=args.name
            )
            
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"Results saved to {args.output_file}")
            else:
                print(json.dumps(results, indent=2))
        
    except Exception as e:
        logger.error(f"Error in dProfiler component: {e}")
        raise


if __name__ == "__main__":
    main() 
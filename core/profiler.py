"""
Core profiling engine for algorithm analysis.

This module provides the main profiling functionality including
performance measurement, memory usage tracking, and algorithm comparison.
"""

import time
import psutil
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from contextlib import contextmanager
import statistics

logger = logging.getLogger(__name__)


@dataclass
class ProfilingResult:
    """Result of a profiling run."""
    algorithm_name: str
    input_size: int
    execution_time: float
    memory_usage: float
    cpu_usage: float
    iterations: int
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "algorithm_name": self.algorithm_name,
            "input_size": self.input_size,
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "iterations": self.iterations,
            "parameters": self.parameters,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class PerformanceMonitor:
    """Monitor system performance during algorithm execution."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = None
        self.peak_memory = 0
        self.cpu_samples = []
        self.monitoring = False
        self._monitor_thread = None
        self._stop_monitoring = threading.Event()
    
    def start_monitoring(self):
        """Start monitoring system resources."""
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.initial_memory
        self.cpu_samples = []
        self.monitoring = True
        self._stop_monitoring.clear()
        
        # Start monitoring thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        logger.debug("Performance monitoring started")
    
    def stop_monitoring(self) -> Dict[str, float]:
        """Stop monitoring and return collected metrics."""
        if not self.monitoring:
            return {"memory_usage": 0, "cpu_usage": 0}
        
        self._stop_monitoring.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
        
        self.monitoring = False
        
        # Calculate metrics
        memory_usage = self.peak_memory - self.initial_memory
        cpu_usage = statistics.mean(self.cpu_samples) if self.cpu_samples else 0
        
        logger.debug(f"Performance monitoring stopped. Memory: {memory_usage:.2f}MB, CPU: {cpu_usage:.2f}%")
        
        return {
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage
        }
    
    def _monitor_loop(self):
        """Monitoring loop running in separate thread."""
        while not self._stop_monitoring.is_set():
            try:
                # Monitor memory
                current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
                self.peak_memory = max(self.peak_memory, current_memory)
                
                # Monitor CPU
                cpu_percent = self.process.cpu_percent()
                self.cpu_samples.append(cpu_percent)
                
                time.sleep(0.1)  # Sample every 100ms
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                break


class AlgorithmProfiler:
    """Main profiler class for algorithm analysis."""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.results_cache = {}
    
    @contextmanager
    def profile_algorithm(self, algorithm_name: str, input_size: int, 
                         parameters: Optional[Dict[str, Any]] = None):
        """Context manager for profiling an algorithm."""
        parameters = parameters or {}
        
        logger.info(f"Starting profiling for {algorithm_name} with input size {input_size}")
        
        # Start monitoring
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            yield
        finally:
            # Stop monitoring and collect metrics
            end_time = time.time()
            metrics = self.monitor.stop_monitoring()
            
            execution_time = end_time - start_time
            
            # Create result
            result = ProfilingResult(
                algorithm_name=algorithm_name,
                input_size=input_size,
                execution_time=execution_time,
                memory_usage=metrics["memory_usage"],
                cpu_usage=metrics["cpu_usage"],
                iterations=1,
                parameters=parameters
            )
            
            logger.info(f"Profiling completed for {algorithm_name}. "
                       f"Time: {execution_time:.4f}s, "
                       f"Memory: {metrics['memory_usage']:.2f}MB")
            
            # Cache result
            cache_key = f"{algorithm_name}_{input_size}_{hash(json.dumps(parameters, sort_keys=True))}"
            self.results_cache[cache_key] = result
    
    def profile_function(self, func: Callable, algorithm_name: str, 
                        input_data: Any, parameters: Optional[Dict[str, Any]] = None,
                        iterations: int = 1) -> ProfilingResult:
        """Profile a function with given input data."""
        parameters = parameters or {}
        input_size = len(input_data) if hasattr(input_data, '__len__') else 1
        
        logger.info(f"Profiling function {algorithm_name} with {iterations} iterations")
        
        # Start monitoring
        self.monitor.start_monitoring()
        start_time = time.time()
        
        try:
            # Execute function multiple times if iterations > 1
            for i in range(iterations):
                result = func(input_data, **parameters)
                if i == 0:  # Store first result
                    first_result = result
        finally:
            # Stop monitoring and collect metrics
            end_time = time.time()
            metrics = self.monitor.stop_monitoring()
            
            execution_time = (end_time - start_time) / iterations  # Average time per iteration
            
            # Create result
            profiling_result = ProfilingResult(
                algorithm_name=algorithm_name,
                input_size=input_size,
                execution_time=execution_time,
                memory_usage=metrics["memory_usage"],
                cpu_usage=metrics["cpu_usage"],
                iterations=iterations,
                parameters=parameters,
                metadata={"function_result": str(first_result) if 'first_result' in locals() else None}
            )
            
            logger.info(f"Function profiling completed for {algorithm_name}. "
                       f"Avg time: {execution_time:.4f}s, "
                       f"Memory: {metrics['memory_usage']:.2f}MB")
            
            return profiling_result
    
    def compare_algorithms(self, algorithms: List[Callable], 
                          algorithm_names: List[str],
                          input_data: Any,
                          parameters_list: Optional[List[Dict[str, Any]]] = None,
                          iterations: int = 1) -> List[ProfilingResult]:
        """Compare multiple algorithms on the same input data."""
        if len(algorithms) != len(algorithm_names):
            raise ValueError("Number of algorithms must match number of names")
        
        if parameters_list is None:
            parameters_list = [{}] * len(algorithms)
        
        if len(parameters_list) != len(algorithms):
            raise ValueError("Number of parameter sets must match number of algorithms")
        
        results = []
        
        for i, (algorithm, name, params) in enumerate(zip(algorithms, algorithm_names, parameters_list)):
            logger.info(f"Comparing algorithm {i+1}/{len(algorithms)}: {name}")
            result = self.profile_function(algorithm, name, input_data, params, iterations)
            results.append(result)
        
        # Log comparison summary
        logger.info("Algorithm comparison completed:")
        for result in results:
            logger.info(f"  {result.algorithm_name}: {result.execution_time:.4f}s "
                       f"({result.memory_usage:.2f}MB)")
        
        return results
    
    def get_cached_result(self, algorithm_name: str, input_size: int, 
                         parameters: Optional[Dict[str, Any]] = None) -> Optional[ProfilingResult]:
        """Retrieve cached profiling result."""
        parameters = parameters or {}
        cache_key = f"{algorithm_name}_{input_size}_{hash(json.dumps(parameters, sort_keys=True))}"
        return self.results_cache.get(cache_key)
    
    def clear_cache(self):
        """Clear the results cache."""
        self.results_cache.clear()
        logger.info("Profiling results cache cleared")


# Common algorithm implementations for testing
def bubble_sort(data: List[int], **kwargs) -> List[int]:
    """Bubble sort implementation for profiling."""
    arr = data.copy()
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


def quick_sort(data: List[int], **kwargs) -> List[int]:
    """Quick sort implementation for profiling."""
    if len(data) <= 1:
        return data
    
    pivot = data[len(data) // 2]
    left = [x for x in data if x < pivot]
    middle = [x for x in data if x == pivot]
    right = [x for x in data if x > pivot]
    
    return quick_sort(left) + middle + quick_sort(right)


def merge_sort(data: List[int], **kwargs) -> List[int]:
    """Merge sort implementation for profiling."""
    if len(data) <= 1:
        return data
    
    mid = len(data) // 2
    left = merge_sort(data[:mid])
    right = merge_sort(data[mid:])
    
    return merge(left, right)


def merge(left: List[int], right: List[int]) -> List[int]:
    """Helper function for merge sort."""
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result 
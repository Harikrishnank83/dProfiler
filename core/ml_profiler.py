"""
Machine Learning Algorithm Profiler for Distributed Computing.

This module extends the core profiler to support ML algorithms like:
- Feature Selection (Filter, Wrapper, Embedded methods)
- Hyperparameter Tuning (Grid Search, Random Search, Bayesian Optimization)
- Model Training and Evaluation
- Distributed Computing with Dask, Spark, and Ray
"""

import time
import psutil
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import asyncio

# ML and Distributed Computing imports
try:
    import dask.dataframe as dd
    import dask.array as da
    from dask.distributed import Client, LocalCluster
    DASK_AVAILABLE = True
except ImportError:
    DASK_AVAILABLE = False

try:
    from pyspark.sql import SparkSession
    from pyspark.ml.feature import VectorAssembler, SelectKBest, ChiSqSelector
    from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
    SPARK_AVAILABLE = True
except ImportError:
    SPARK_AVAILABLE = False

try:
    import ray
    from ray import tune
    from ray.tune.schedulers import ASHAScheduler
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False

# ML Libraries
try:
    from sklearn.feature_selection import SelectKBest, f_classif, mutual_info_classif
    from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class MLProfilingResult:
    """Result of ML algorithm profiling."""
    
    algorithm_name: str
    framework: str  # 'dask', 'spark', 'ray', 'sklearn'
    dataset_size: int
    feature_count: int
    execution_time: float
    memory_usage: float
    cpu_usage: float
    gpu_usage: Optional[float] = None
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    selected_features: Optional[List[str]] = None
    best_params: Optional[Dict[str, Any]] = None
    iterations: int = 1
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MLProfiler:
    """Machine Learning Algorithm Profiler for Distributed Computing."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.results: List[MLProfilingResult] = []
        
        # Initialize distributed computing clients
        self.dask_client = None
        self.spark_session = None
        self.ray_initialized = False
        
    def initialize_dask(self, n_workers: int = 2, threads_per_worker: int = 2):
        """Initialize Dask distributed client."""
        if not DASK_AVAILABLE:
            raise ImportError("Dask is not available. Install with: pip install dask[complete]")
        
        cluster = LocalCluster(n_workers=n_workers, threads_per_worker=threads_per_worker)
        self.dask_client = Client(cluster)
        logger.info(f"Dask client initialized with {n_workers} workers")
        
    def initialize_spark(self, app_name: str = "MLProfiler"):
        """Initialize Spark session."""
        if not SPARK_AVAILABLE:
            raise ImportError("PySpark is not available. Install with: pip install pyspark")
        
        self.spark_session = SparkSession.builder \
            .appName(app_name) \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        logger.info("Spark session initialized")
        
    def initialize_ray(self):
        """Initialize Ray for distributed computing."""
        if not RAY_AVAILABLE:
            raise ImportError("Ray is not available. Install with: pip install ray[tune]")
        
        if not self.ray_initialized:
            ray.init(ignore_reinit_error=True)
            self.ray_initialized = True
        logger.info("Ray initialized")
        
    def _monitor_resources(self) -> Dict[str, float]:
        """Monitor system resources during execution."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'memory_mb': memory_info.rss / 1024 / 1024,
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent()
        }
    
    def _create_sample_dataset(self, n_samples: int, n_features: int, 
                             framework: str = 'pandas') -> Any:
        """Create sample dataset for testing."""
        np.random.seed(42)
        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)
        feature_names = [f'feature_{i}' for i in range(n_features)]
        
        if framework == 'pandas':
            df = pd.DataFrame(X, columns=feature_names)
            df['target'] = y
            return df, feature_names
        elif framework == 'dask' and DASK_AVAILABLE:
            df = dd.from_pandas(pd.DataFrame(X, columns=feature_names), npartitions=4)
            df['target'] = y
            return df, feature_names
        elif framework == 'spark' and SPARK_AVAILABLE:
            df = self.spark_session.createDataFrame(
                pd.DataFrame(X, columns=feature_names + ['target'])
            )
            return df, feature_names
        else:
            return X, y, feature_names
    
    def profile_feature_selection(self, 
                                method: str = 'filter',
                                framework: str = 'sklearn',
                                dataset_size: int = 10000,
                                n_features: int = 100,
                                n_select: int = 20,
                                iterations: int = 1) -> MLProfilingResult:
        """Profile feature selection algorithms."""
        
        start_time = time.time()
        start_resources = self._monitor_resources()
        
        # Create dataset
        if framework == 'dask':
            data, feature_names = self._create_sample_dataset(dataset_size, n_features, 'dask')
        elif framework == 'spark':
            data, feature_names = self._create_sample_dataset(dataset_size, n_features, 'spark')
        else:
            data, feature_names = self._create_sample_dataset(dataset_size, n_features, 'pandas')
        
        # Perform feature selection
        selected_features = []
        
        if framework == 'sklearn' and SKLEARN_AVAILABLE:
            if method == 'filter':
                selector = SelectKBest(score_func=f_classif, k=n_select)
                X = data.drop('target', axis=1) if hasattr(data, 'drop') else data[:, :-1]
                y = data['target'] if hasattr(data, 'target') else data[:, -1]
                selector.fit(X, y)
                selected_features = [feature_names[i] for i in selector.get_support(indices=True)]
                
        elif framework == 'dask' and DASK_AVAILABLE:
            # Dask implementation
            X = data.drop('target', axis=1)
            y = data['target']
            
            # Compute correlation with target
            correlations = X.corrwith(y).abs()
            selected_features = correlations.nlargest(n_select).index.tolist()
            
        elif framework == 'spark' and SPARK_AVAILABLE:
            # Spark implementation
            assembler = VectorAssembler(inputCols=feature_names, outputCol="features")
            data_with_features = assembler.transform(data)
            
            selector = ChiSqSelector(numTopFeatures=n_select, featuresCol="features", outputCol="selectedFeatures")
            model = selector.fit(data_with_features)
            selected_features = [feature_names[i] for i in model.selectedFeatures]
        
        end_time = time.time()
        end_resources = self._monitor_resources()
        
        execution_time = end_time - start_time
        memory_usage = end_resources['memory_mb']
        cpu_usage = end_resources['cpu_percent']
        
        result = MLProfilingResult(
            algorithm_name=f"{method}_feature_selection",
            framework=framework,
            dataset_size=dataset_size,
            feature_count=n_features,
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            selected_features=selected_features,
            iterations=iterations,
            parameters={
                'method': method,
                'n_select': n_select,
                'framework': framework
            }
        )
        
        self.results.append(result)
        return result
    
    def profile_hyperparameter_tuning(self,
                                    algorithm: str = 'random_forest',
                                    framework: str = 'sklearn',
                                    dataset_size: int = 5000,
                                    n_features: int = 50,
                                    iterations: int = 1) -> MLProfilingResult:
        """Profile hyperparameter tuning algorithms."""
        
        start_time = time.time()
        start_resources = self._monitor_resources()
        
        # Create dataset
        if framework == 'dask':
            data, feature_names = self._create_sample_dataset(dataset_size, n_features, 'dask')
        elif framework == 'spark':
            data, feature_names = self._create_sample_dataset(dataset_size, n_features, 'spark')
        else:
            data, feature_names = self._create_sample_dataset(dataset_size, n_features, 'pandas')
        
        best_params = {}
        accuracy = 0.0
        
        if framework == 'sklearn' and SKLEARN_AVAILABLE:
            X = data.drop('target', axis=1) if hasattr(data, 'drop') else data[:, :-1]
            y = data['target'] if hasattr(data, 'target') else data[:, -1]
            
            if algorithm == 'random_forest':
                model = RandomForestClassifier(random_state=42)
                param_grid = {
                    'n_estimators': [50, 100],
                    'max_depth': [10, 20, None],
                    'min_samples_split': [2, 5]
                }
            elif algorithm == 'logistic_regression':
                model = LogisticRegression(random_state=42)
                param_grid = {
                    'C': [0.1, 1.0, 10.0],
                    'penalty': ['l1', 'l2'],
                    'solver': ['liblinear', 'saga']
                }
            
            grid_search = GridSearchCV(model, param_grid, cv=3, scoring='accuracy')
            grid_search.fit(X, y)
            
            best_params = grid_search.best_params_
            accuracy = grid_search.best_score_
            
        elif framework == 'ray' and RAY_AVAILABLE:
            # Ray Tune implementation
            def trainable(config):
                if algorithm == 'random_forest':
                    model = RandomForestClassifier(**config, random_state=42)
                else:
                    model = LogisticRegression(**config, random_state=42)
                
                X = data.drop('target', axis=1) if hasattr(data, 'drop') else data[:, :-1]
                y = data['target'] if hasattr(data, 'target') else data[:, -1]
                
                # Simple train/test split
                split_idx = len(X) // 2
                X_train, X_test = X[:split_idx], X[split_idx:]
                y_train, y_test = y[:split_idx], y[split_idx:]
                
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                
                tune.report(accuracy=accuracy)
            
            if algorithm == 'random_forest':
                config = {
                    'n_estimators': tune.choice([50, 100]),
                    'max_depth': tune.choice([10, 20, None]),
                    'min_samples_split': tune.choice([2, 5])
                }
            else:
                config = {
                    'C': tune.loguniform(0.1, 10.0),
                    'penalty': tune.choice(['l1', 'l2']),
                    'solver': tune.choice(['liblinear', 'saga'])
                }
            
            scheduler = ASHAScheduler(metric="accuracy", mode="max")
            analysis = tune.run(
                trainable,
                config=config,
                num_samples=10,
                scheduler=scheduler,
                resources_per_trial={"cpu": 1}
            )
            
            best_params = analysis.best_config
            accuracy = analysis.best_result['accuracy']
        
        end_time = time.time()
        end_resources = self._monitor_resources()
        
        execution_time = end_time - start_time
        memory_usage = end_resources['memory_mb']
        cpu_usage = end_resources['cpu_percent']
        
        result = MLProfilingResult(
            algorithm_name=f"{algorithm}_hyperparameter_tuning",
            framework=framework,
            dataset_size=dataset_size,
            feature_count=n_features,
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            accuracy=accuracy,
            best_params=best_params,
            iterations=iterations,
            parameters={
                'algorithm': algorithm,
                'framework': framework
            }
        )
        
        self.results.append(result)
        return result
    
    def profile_distributed_training(self,
                                   algorithm: str = 'random_forest',
                                   framework: str = 'dask',
                                   dataset_size: int = 100000,
                                   n_features: int = 100,
                                   iterations: int = 1) -> MLProfilingResult:
        """Profile distributed model training."""
        
        start_time = time.time()
        start_resources = self._monitor_resources()
        
        # Create large dataset
        data, feature_names = self._create_sample_dataset(dataset_size, n_features, framework)
        
        accuracy = 0.0
        
        if framework == 'dask' and DASK_AVAILABLE:
            # Dask-ML implementation
            from dask_ml.model_selection import train_test_split
            from dask_ml.ensemble import RandomForestClassifier as DaskRF
            
            X = data.drop('target', axis=1)
            y = data['target']
            
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
            
            model = DaskRF(n_estimators=100, max_depth=10)
            model.fit(X_train, y_train)
            
            y_pred = model.predict(X_test)
            accuracy = accuracy_score(y_test.compute(), y_pred.compute())
            
        elif framework == 'spark' and SPARK_AVAILABLE:
            # Spark ML implementation
            from pyspark.ml.classification import RandomForestClassifier as SparkRF
            from pyspark.ml.evaluation import MulticlassClassificationEvaluator
            
            assembler = VectorAssembler(inputCols=feature_names, outputCol="features")
            data_with_features = assembler.transform(data)
            
            train_data, test_data = data_with_features.randomSplit([0.8, 0.2], seed=42)
            
            rf = SparkRF(labelCol="target", featuresCol="features", numTrees=100, maxDepth=10)
            model = rf.fit(train_data)
            
            predictions = model.transform(test_data)
            evaluator = MulticlassClassificationEvaluator(labelCol="target", predictionCol="prediction", metricName="accuracy")
            accuracy = evaluator.evaluate(predictions)
        
        end_time = time.time()
        end_resources = self._monitor_resources()
        
        execution_time = end_time - start_time
        memory_usage = end_resources['memory_mb']
        cpu_usage = end_resources['cpu_percent']
        
        result = MLProfilingResult(
            algorithm_name=f"{algorithm}_distributed_training",
            framework=framework,
            dataset_size=dataset_size,
            feature_count=n_features,
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            accuracy=accuracy,
            iterations=iterations,
            parameters={
                'algorithm': algorithm,
                'framework': framework
            }
        )
        
        self.results.append(result)
        return result
    
    def compare_frameworks(self, 
                          algorithm: str = 'feature_selection',
                          dataset_size: int = 10000,
                          n_features: int = 100) -> List[MLProfilingResult]:
        """Compare performance across different frameworks."""
        
        frameworks = []
        if SKLEARN_AVAILABLE:
            frameworks.append('sklearn')
        if DASK_AVAILABLE:
            frameworks.append('dask')
        if SPARK_AVAILABLE:
            frameworks.append('spark')
        if RAY_AVAILABLE:
            frameworks.append('ray')
        
        results = []
        
        for framework in frameworks:
            try:
                if algorithm == 'feature_selection':
                    result = self.profile_feature_selection(
                        framework=framework,
                        dataset_size=dataset_size,
                        n_features=n_features
                    )
                elif algorithm == 'hyperparameter_tuning':
                    result = self.profile_hyperparameter_tuning(
                        framework=framework,
                        dataset_size=dataset_size,
                        n_features=n_features
                    )
                elif algorithm == 'distributed_training':
                    result = self.profile_distributed_training(
                        framework=framework,
                        dataset_size=dataset_size,
                        n_features=n_features
                    )
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error profiling {algorithm} with {framework}: {e}")
                continue
        
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all profiling results."""
        if not self.results:
            return {"message": "No profiling results available"}
        
        summary = {
            "total_runs": len(self.results),
            "frameworks_used": list(set(r.framework for r in self.results)),
            "algorithms_profiled": list(set(r.algorithm_name for r in self.results)),
            "performance_summary": {}
        }
        
        # Group by framework and algorithm
        for result in self.results:
            key = f"{result.framework}_{result.algorithm_name}"
            if key not in summary["performance_summary"]:
                summary["performance_summary"][key] = {
                    "avg_execution_time": [],
                    "avg_memory_usage": [],
                    "avg_cpu_usage": [],
                    "avg_accuracy": []
                }
            
            summary["performance_summary"][key]["avg_execution_time"].append(result.execution_time)
            summary["performance_summary"][key]["avg_memory_usage"].append(result.memory_usage)
            summary["performance_summary"][key]["avg_cpu_usage"].append(result.cpu_usage)
            if result.accuracy is not None:
                summary["performance_summary"][key]["avg_accuracy"].append(result.accuracy)
        
        # Calculate averages
        for key, metrics in summary["performance_summary"].items():
            for metric_name, values in metrics.items():
                if values:
                    metrics[metric_name] = sum(values) / len(values)
        
        return summary
    
    def cleanup(self):
        """Clean up distributed computing resources."""
        if self.dask_client:
            self.dask_client.close()
        if self.spark_session:
            self.spark_session.stop()
        if self.ray_initialized:
            ray.shutdown() 
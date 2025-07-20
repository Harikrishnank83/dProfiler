#!/usr/bin/env python3
"""
Machine Learning Algorithm Profiling Examples

This script demonstrates how to use dProfiler to monitor the performance
of machine learning algorithms using distributed computing frameworks
like Dask, Spark, and Ray.

Examples include:
1. Feature Selection with different frameworks
2. Hyperparameter Tuning with Ray Tune
3. Distributed Model Training with Dask and Spark
4. Framework Performance Comparison
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from core.ml_profiler import MLProfiler


def example_feature_selection():
    """Example: Profile feature selection with different frameworks."""
    print("🔍 Feature Selection Profiling Examples")
    print("=" * 50)
    
    profiler = MLProfiler()
    
    # Test with sklearn (single machine)
    print("\n1. Testing sklearn feature selection...")
    try:
        result_sklearn = profiler.profile_feature_selection(
            method="filter",
            framework="sklearn",
            dataset_size=10000,
            n_features=100,
            n_select=20
        )
        print(f"✅ sklearn: {result_sklearn.execution_time:.4f}s, "
              f"{result_sklearn.memory_usage:.2f}MB, "
              f"{result_sklearn.cpu_usage:.2f}%")
    except Exception as e:
        print(f"❌ sklearn failed: {e}")
    
    # Test with Dask (distributed)
    print("\n2. Testing Dask feature selection...")
    try:
        profiler.initialize_dask(n_workers=2)
        result_dask = profiler.profile_feature_selection(
            method="filter",
            framework="dask",
            dataset_size=50000,
            n_features=200,
            n_select=50
        )
        print(f"✅ Dask: {result_dask.execution_time:.4f}s, "
              f"{result_dask.memory_usage:.2f}MB, "
              f"{result_dask.cpu_usage:.2f}%")
    except Exception as e:
        print(f"❌ Dask failed: {e}")
    
    # Test with Spark (distributed)
    print("\n3. Testing Spark feature selection...")
    try:
        profiler.initialize_spark()
        result_spark = profiler.profile_feature_selection(
            method="filter",
            framework="spark",
            dataset_size=100000,
            n_features=300,
            n_select=75
        )
        print(f"✅ Spark: {result_spark.execution_time:.4f}s, "
              f"{result_spark.memory_usage:.2f}MB, "
              f"{result_spark.cpu_usage:.2f}%")
    except Exception as e:
        print(f"❌ Spark failed: {e}")
    
    profiler.cleanup()


def example_hyperparameter_tuning():
    """Example: Profile hyperparameter tuning with Ray Tune."""
    print("\n🎯 Hyperparameter Tuning Profiling Examples")
    print("=" * 50)
    
    profiler = MLProfiler()
    
    # Test sklearn GridSearchCV
    print("\n1. Testing sklearn GridSearchCV...")
    try:
        result_sklearn = profiler.profile_hyperparameter_tuning(
            algorithm="random_forest",
            framework="sklearn",
            dataset_size=5000,
            n_features=50
        )
        print(f"✅ sklearn GridSearch: {result_sklearn.execution_time:.4f}s, "
              f"Accuracy: {result_sklearn.accuracy:.4f}")
        print(f"   Best params: {result_sklearn.best_params}")
    except Exception as e:
        print(f"❌ sklearn failed: {e}")
    
    # Test Ray Tune
    print("\n2. Testing Ray Tune hyperparameter optimization...")
    try:
        profiler.initialize_ray()
        result_ray = profiler.profile_hyperparameter_tuning(
            algorithm="random_forest",
            framework="ray",
            dataset_size=5000,
            n_features=50
        )
        print(f"✅ Ray Tune: {result_ray.execution_time:.4f}s, "
              f"Accuracy: {result_ray.accuracy:.4f}")
        print(f"   Best params: {result_ray.best_params}")
    except Exception as e:
        print(f"❌ Ray failed: {e}")
    
    profiler.cleanup()


def example_distributed_training():
    """Example: Profile distributed model training."""
    print("\n🚀 Distributed Training Profiling Examples")
    print("=" * 50)
    
    profiler = MLProfiler()
    
    # Test Dask-ML distributed training
    print("\n1. Testing Dask-ML distributed training...")
    try:
        profiler.initialize_dask(n_workers=4)
        result_dask = profiler.profile_distributed_training(
            algorithm="random_forest",
            framework="dask",
            dataset_size=100000,
            n_features=100
        )
        print(f"✅ Dask-ML: {result_dask.execution_time:.4f}s, "
              f"Accuracy: {result_dask.accuracy:.4f}")
    except Exception as e:
        print(f"❌ Dask-ML failed: {e}")
    
    # Test Spark ML distributed training
    print("\n2. Testing Spark ML distributed training...")
    try:
        profiler.initialize_spark()
        result_spark = profiler.profile_distributed_training(
            algorithm="random_forest",
            framework="spark",
            dataset_size=200000,
            n_features=150
        )
        print(f"✅ Spark ML: {result_spark.execution_time:.4f}s, "
              f"Accuracy: {result_spark.accuracy:.4f}")
    except Exception as e:
        print(f"❌ Spark ML failed: {e}")
    
    profiler.cleanup()


def example_framework_comparison():
    """Example: Compare performance across different frameworks."""
    print("\n⚖️ Framework Performance Comparison")
    print("=" * 50)
    
    profiler = MLProfiler()
    
    # Compare feature selection across frameworks
    print("\nComparing feature selection performance...")
    try:
        # Initialize all frameworks
        try:
            profiler.initialize_dask()
        except:
            pass
        try:
            profiler.initialize_spark()
        except:
            pass
        try:
            profiler.initialize_ray()
        except:
            pass
        
        results = profiler.compare_frameworks(
            algorithm="feature_selection",
            dataset_size=10000,
            n_features=100
        )
        
        print("\n📊 Feature Selection Performance Comparison:")
        print("-" * 80)
        print(f"{'Framework':<12} {'Time (s)':<10} {'Memory (MB)':<12} {'CPU (%)':<10}")
        print("-" * 80)
        
        for result in results:
            print(f"{result.framework:<12} {result.execution_time:<10.4f} "
                  f"{result.memory_usage:<12.2f} {result.cpu_usage:<10.2f}")
        
        # Find best performers
        if results:
            fastest = min(results, key=lambda x: x.execution_time)
            most_efficient = min(results, key=lambda x: x.memory_usage)
            
            print(f"\n🏆 Fastest: {fastest.framework} ({fastest.execution_time:.4f}s)")
            print(f"💾 Most Memory Efficient: {most_efficient.framework} "
                  f"({most_efficient.memory_usage:.2f}MB)")
    
    except Exception as e:
        print(f"❌ Framework comparison failed: {e}")
    
    profiler.cleanup()


def example_real_world_scenario():
    """Example: Real-world ML pipeline profiling scenario."""
    print("\n🌍 Real-World ML Pipeline Profiling")
    print("=" * 50)
    
    profiler = MLProfiler()
    
    # Simulate a complete ML pipeline
    print("Simulating a complete ML pipeline with distributed computing...")
    
    pipeline_results = []
    
    try:
        # Step 1: Feature Selection with Dask
        print("\n1️⃣ Feature Selection (Dask)...")
        profiler.initialize_dask(n_workers=2)
        feature_result = profiler.profile_feature_selection(
            method="filter",
            framework="dask",
            dataset_size=50000,
            n_features=200,
            n_select=50
        )
        pipeline_results.append(feature_result)
        print(f"   ✅ Selected {len(feature_result.selected_features)} features "
              f"in {feature_result.execution_time:.4f}s")
        
        # Step 2: Hyperparameter Tuning with Ray
        print("\n2️⃣ Hyperparameter Tuning (Ray)...")
        profiler.initialize_ray()
        tuning_result = profiler.profile_hyperparameter_tuning(
            algorithm="random_forest",
            framework="ray",
            dataset_size=25000,
            n_features=50  # Using selected features
        )
        pipeline_results.append(tuning_result)
        print(f"   ✅ Best accuracy: {tuning_result.accuracy:.4f} "
              f"in {tuning_result.execution_time:.4f}s")
        
        # Step 3: Distributed Training with Spark
        print("\n3️⃣ Distributed Training (Spark)...")
        profiler.initialize_spark()
        training_result = profiler.profile_distributed_training(
            algorithm="random_forest",
            framework="spark",
            dataset_size=100000,
            n_features=50
        )
        pipeline_results.append(training_result)
        print(f"   ✅ Final accuracy: {training_result.accuracy:.4f} "
              f"in {training_result.execution_time:.4f}s")
        
        # Pipeline Summary
        total_time = sum(r.execution_time for r in pipeline_results)
        total_memory = sum(r.memory_usage for r in pipeline_results)
        avg_cpu = sum(r.cpu_usage for r in pipeline_results) / len(pipeline_results)
        
        print(f"\n📈 Pipeline Summary:")
        print(f"   Total Time: {total_time:.4f}s")
        print(f"   Peak Memory: {total_memory:.2f}MB")
        print(f"   Average CPU: {avg_cpu:.2f}%")
        print(f"   Final Model Accuracy: {training_result.accuracy:.4f}")
        
        # Save results
        with open("ml_pipeline_results.json", "w") as f:
            json.dump([{
                "step": i + 1,
                "algorithm": r.algorithm_name,
                "framework": r.framework,
                "execution_time": r.execution_time,
                "memory_usage": r.memory_usage,
                "cpu_usage": r.cpu_usage,
                "accuracy": r.accuracy,
                "selected_features": r.selected_features,
                "best_params": r.best_params
            } for i, r in enumerate(pipeline_results)], f, indent=2)
        
        print(f"\n💾 Results saved to ml_pipeline_results.json")
    
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
    
    profiler.cleanup()


def example_api_integration():
    """Example: Using the ML profiling via API endpoints."""
    print("\n🌐 API Integration Examples")
    print("=" * 50)
    
    import httpx
    
    base_url = "http://localhost:8000/api/v1/ml"
    
    # Test available frameworks
    print("\n1. Checking available frameworks...")
    try:
        response = httpx.get(f"{base_url}/frameworks/available")
        if response.status_code == 200:
            frameworks = response.json()
            print(f"✅ Available frameworks: {frameworks['available_frameworks']}")
        else:
            print(f"❌ Failed to get frameworks: {response.status_code}")
    except Exception as e:
        print(f"❌ API not available: {e}")
        return
    
    # Test feature selection via API
    print("\n2. Testing feature selection via API...")
    try:
        feature_data = {
            "method": "filter",
            "framework": "sklearn",
            "dataset_size": 10000,
            "n_features": 100,
            "n_select": 20,
            "iterations": 1
        }
        
        response = httpx.post(f"{base_url}/feature-selection", json=feature_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Feature selection completed:")
            print(f"   Job ID: {result['job_id']}")
            print(f"   Execution Time: {result['execution_time']:.4f}s")
            print(f"   Memory Usage: {result['memory_usage']:.2f}MB")
            print(f"   Selected Features: {result['selected_features_count']}")
        else:
            print(f"❌ Feature selection failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API call failed: {e}")
    
    # Test framework comparison via API
    print("\n3. Testing framework comparison via API...")
    try:
        comparison_data = {
            "algorithm": "feature_selection",
            "dataset_size": 10000,
            "n_features": 100
        }
        
        response = httpx.post(f"{base_url}/compare-frameworks", json=comparison_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Framework comparison completed:")
            print(f"   Comparison ID: {result['comparison_id']}")
            print(f"   Results: {len(result['results'])} frameworks tested")
            
            for framework_result in result['results']:
                print(f"   {framework_result['framework']}: "
                      f"{framework_result['execution_time']:.4f}s, "
                      f"{framework_result['memory_usage']:.2f}MB")
        else:
            print(f"❌ Framework comparison failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API call failed: {e}")


def main():
    """Run all ML profiling examples."""
    print("🤖 dProfiler ML Algorithm Profiling Examples")
    print("=" * 60)
    print("This script demonstrates how to use dProfiler to monitor")
    print("machine learning algorithm performance with distributed computing.")
    print()
    
    # Run examples
    example_feature_selection()
    example_hyperparameter_tuning()
    example_distributed_training()
    example_framework_comparison()
    example_real_world_scenario()
    example_api_integration()
    
    print("\n🎉 All examples completed!")
    print("\n💡 Next steps:")
    print("   1. Install additional ML dependencies: uv add dask[complete] pyspark ray[tune]")
    print("   2. Start the API server: dprofiler start")
    print("   3. Use CLI commands: dprofiler ml feature-selection --help")
    print("   4. Explore the API documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    main() 
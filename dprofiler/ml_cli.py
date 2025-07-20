"""
CLI commands for Machine Learning algorithm profiling.

This module provides command-line interface for profiling ML algorithms
using distributed computing frameworks like Dask, Spark, and Ray.
"""

import typer
import asyncio
import json
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from core.ml_profiler import MLProfiler

console = Console()
app = typer.Typer(name="ml", help="Machine Learning Algorithm Profiling")

# Global ML profiler instance
ml_profiler = MLProfiler()


@app.command()
def feature_selection(
    method: str = typer.Option("filter", "--method", "-m", help="Feature selection method"),
    framework: str = typer.Option("sklearn", "--framework", "-f", help="Computing framework"),
    dataset_size: int = typer.Option(10000, "--dataset-size", "-s", help="Dataset size"),
    n_features: int = typer.Option(100, "--n-features", "-n", help="Number of features"),
    n_select: int = typer.Option(20, "--n-select", "-k", help="Number of features to select"),
    iterations: int = typer.Option(1, "--iterations", "-i", help="Number of iterations"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
):
    """Profile feature selection algorithms."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Profiling feature selection...", total=None)
        
        try:
            # Initialize framework
            if framework == "dask":
                ml_profiler.initialize_dask()
            elif framework == "spark":
                ml_profiler.initialize_spark()
            elif framework == "ray":
                ml_profiler.initialize_ray()
            
            # Run profiling
            result = ml_profiler.profile_feature_selection(
                method=method,
                framework=framework,
                dataset_size=dataset_size,
                n_features=n_features,
                n_select=n_select,
                iterations=iterations
            )
            
            progress.update(task, description="Feature selection completed!")
            
            # Display results
            display_feature_selection_results(result, output)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def hyperparameter_tuning(
    algorithm: str = typer.Option("random_forest", "--algorithm", "-a", help="ML algorithm"),
    framework: str = typer.Option("sklearn", "--framework", "-f", help="Computing framework"),
    dataset_size: int = typer.Option(5000, "--dataset-size", "-s", help="Dataset size"),
    n_features: int = typer.Option(50, "--n-features", "-n", help="Number of features"),
    iterations: int = typer.Option(1, "--iterations", "-i", help="Number of iterations"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
):
    """Profile hyperparameter tuning algorithms."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Profiling hyperparameter tuning...", total=None)
        
        try:
            # Initialize framework
            if framework == "dask":
                ml_profiler.initialize_dask()
            elif framework == "spark":
                ml_profiler.initialize_spark()
            elif framework == "ray":
                ml_profiler.initialize_ray()
            
            # Run profiling
            result = ml_profiler.profile_hyperparameter_tuning(
                algorithm=algorithm,
                framework=framework,
                dataset_size=dataset_size,
                n_features=n_features,
                iterations=iterations
            )
            
            progress.update(task, description="Hyperparameter tuning completed!")
            
            # Display results
            display_hyperparameter_tuning_results(result, output)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def distributed_training(
    algorithm: str = typer.Option("random_forest", "--algorithm", "-a", help="ML algorithm"),
    framework: str = typer.Option("dask", "--framework", "-f", help="Computing framework"),
    dataset_size: int = typer.Option(100000, "--dataset-size", "-s", help="Dataset size"),
    n_features: int = typer.Option(100, "--n-features", "-n", help="Number of features"),
    iterations: int = typer.Option(1, "--iterations", "-i", help="Number of iterations"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
):
    """Profile distributed model training."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Profiling distributed training...", total=None)
        
        try:
            # Initialize framework
            if framework == "dask":
                ml_profiler.initialize_dask()
            elif framework == "spark":
                ml_profiler.initialize_spark()
            elif framework == "ray":
                ml_profiler.initialize_ray()
            
            # Run profiling
            result = ml_profiler.profile_distributed_training(
                algorithm=algorithm,
                framework=framework,
                dataset_size=dataset_size,
                n_features=n_features,
                iterations=iterations
            )
            
            progress.update(task, description="Distributed training completed!")
            
            # Display results
            display_distributed_training_results(result, output)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def compare_frameworks(
    algorithm: str = typer.Option("feature_selection", "--algorithm", "-a", help="ML algorithm"),
    dataset_size: int = typer.Option(10000, "--dataset-size", "-s", help="Dataset size"),
    n_features: int = typer.Option(100, "--n-features", "-n", help="Number of features"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for results"),
):
    """Compare performance across different frameworks."""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Comparing frameworks...", total=None)
        
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
                algorithm=algorithm,
                dataset_size=dataset_size,
                n_features=n_features
            )
            
            progress.update(task, description="Framework comparison completed!")
            
            # Display results
            display_framework_comparison_results(results, output)
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def summary():
    """Get summary of ML profiling results."""
    try:
        summary = ml_profiler.get_summary()
        display_summary(summary)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def available_frameworks():
    """Show available distributed computing frameworks."""
    from core.ml_profiler import DASK_AVAILABLE, SPARK_AVAILABLE, RAY_AVAILABLE, SKLEARN_AVAILABLE
    
    frameworks = {
        "sklearn": SKLEARN_AVAILABLE,
        "dask": DASK_AVAILABLE,
        "spark": SPARK_AVAILABLE,
        "ray": RAY_AVAILABLE
    }
    
    table = Table(title="Available Frameworks")
    table.add_column("Framework", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description", style="white")
    
    for framework, available in frameworks.items():
        status = "✅ Available" if available else "❌ Not Available"
        description = get_framework_description(framework)
        table.add_row(framework, status, description)
    
    console.print(table)


@app.command()
def cleanup():
    """Clean up distributed computing resources."""
    try:
        ml_profiler.cleanup()
        console.print("[green]Resources cleaned up successfully![/green]")
    except Exception as e:
        console.print(f"[red]Error cleaning up resources: {e}[/red]")
        raise typer.Exit(1)


def display_feature_selection_results(result, output_file: Optional[str] = None):
    """Display feature selection profiling results."""
    
    # Create results table
    table = Table(title=f"Feature Selection Results - {result.framework.upper()}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Algorithm", result.algorithm_name)
    table.add_row("Framework", result.framework)
    table.add_row("Dataset Size", str(result.dataset_size))
    table.add_row("Feature Count", str(result.feature_count))
    table.add_row("Execution Time", f"{result.execution_time:.4f} seconds")
    table.add_row("Memory Usage", f"{result.memory_usage:.2f} MB")
    table.add_row("CPU Usage", f"{result.cpu_usage:.2f}%")
    table.add_row("Selected Features", str(len(result.selected_features) if result.selected_features else 0))
    
    console.print(table)
    
    if result.selected_features:
        console.print("\n[bold]Selected Features:[/bold]")
        console.print(", ".join(result.selected_features[:10]))  # Show first 10
        if len(result.selected_features) > 10:
            console.print(f"... and {len(result.selected_features) - 10} more")
    
    # Save to file if requested
    if output_file:
        save_results_to_file(result, output_file)


def display_hyperparameter_tuning_results(result, output_file: Optional[str] = None):
    """Display hyperparameter tuning profiling results."""
    
    # Create results table
    table = Table(title=f"Hyperparameter Tuning Results - {result.framework.upper()}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Algorithm", result.algorithm_name)
    table.add_row("Framework", result.framework)
    table.add_row("Dataset Size", str(result.dataset_size))
    table.add_row("Feature Count", str(result.feature_count))
    table.add_row("Execution Time", f"{result.execution_time:.4f} seconds")
    table.add_row("Memory Usage", f"{result.memory_usage:.2f} MB")
    table.add_row("CPU Usage", f"{result.cpu_usage:.2f}%")
    table.add_row("Accuracy", f"{result.accuracy:.4f}" if result.accuracy else "N/A")
    
    console.print(table)
    
    if result.best_params:
        console.print("\n[bold]Best Parameters:[/bold]")
        for param, value in result.best_params.items():
            console.print(f"  {param}: {value}")
    
    # Save to file if requested
    if output_file:
        save_results_to_file(result, output_file)


def display_distributed_training_results(result, output_file: Optional[str] = None):
    """Display distributed training profiling results."""
    
    # Create results table
    table = Table(title=f"Distributed Training Results - {result.framework.upper()}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Algorithm", result.algorithm_name)
    table.add_row("Framework", result.framework)
    table.add_row("Dataset Size", str(result.dataset_size))
    table.add_row("Feature Count", str(result.feature_count))
    table.add_row("Execution Time", f"{result.execution_time:.4f} seconds")
    table.add_row("Memory Usage", f"{result.memory_usage:.2f} MB")
    table.add_row("CPU Usage", f"{result.cpu_usage:.2f}%")
    table.add_row("Accuracy", f"{result.accuracy:.4f}" if result.accuracy else "N/A")
    
    console.print(table)
    
    # Save to file if requested
    if output_file:
        save_results_to_file(result, output_file)


def display_framework_comparison_results(results: List, output_file: Optional[str] = None):
    """Display framework comparison results."""
    
    if not results:
        console.print("[yellow]No results to display[/yellow]")
        return
    
    # Create comparison table
    table = Table(title="Framework Comparison Results")
    table.add_column("Framework", style="cyan")
    table.add_column("Algorithm", style="blue")
    table.add_column("Execution Time (s)", style="green")
    table.add_column("Memory (MB)", style="yellow")
    table.add_column("CPU (%)", style="red")
    table.add_column("Accuracy", style="magenta")
    
    for result in results:
        table.add_row(
            result.framework,
            result.algorithm_name,
            f"{result.execution_time:.4f}",
            f"{result.memory_usage:.2f}",
            f"{result.cpu_usage:.2f}",
            f"{result.accuracy:.4f}" if result.accuracy else "N/A"
        )
    
    console.print(table)
    
    # Find best performing framework
    if results:
        best_time = min(results, key=lambda x: x.execution_time)
        best_memory = min(results, key=lambda x: x.memory_usage)
        best_accuracy = max(results, key=lambda x: x.accuracy or 0)
        
        console.print("\n[bold]Performance Summary:[/bold]")
        console.print(f"Fastest: {best_time.framework} ({best_time.execution_time:.4f}s)")
        console.print(f"Most Memory Efficient: {best_memory.framework} ({best_memory.memory_usage:.2f}MB)")
        if best_accuracy.accuracy:
            console.print(f"Best Accuracy: {best_accuracy.framework} ({best_accuracy.accuracy:.4f})")
    
    # Save to file if requested
    if output_file:
        save_results_to_file(results, output_file)


def display_summary(summary: dict):
    """Display ML profiling summary."""
    
    if "message" in summary:
        console.print(f"[yellow]{summary['message']}[/yellow]")
        return
    
    # Create summary table
    table = Table(title="ML Profiling Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Runs", str(summary["total_runs"]))
    table.add_row("Frameworks Used", ", ".join(summary["frameworks_used"]))
    table.add_row("Algorithms Profiled", ", ".join(summary["algorithms_profiled"]))
    
    console.print(table)
    
    # Performance summary
    if summary["performance_summary"]:
        console.print("\n[bold]Performance Summary by Framework/Algorithm:[/bold]")
        
        perf_table = Table()
        perf_table.add_column("Framework/Algorithm", style="cyan")
        perf_table.add_column("Avg Execution Time (s)", style="green")
        perf_table.add_column("Avg Memory (MB)", style="yellow")
        perf_table.add_column("Avg CPU (%)", style="red")
        perf_table.add_column("Avg Accuracy", style="magenta")
        
        for key, metrics in summary["performance_summary"].items():
            perf_table.add_row(
                key,
                f"{metrics['avg_execution_time']:.4f}",
                f"{metrics['avg_memory_usage']:.2f}",
                f"{metrics['avg_cpu_usage']:.2f}",
                f"{metrics['avg_accuracy']:.4f}" if metrics['avg_accuracy'] else "N/A"
            )
        
        console.print(perf_table)


def get_framework_description(framework: str) -> str:
    """Get description for a framework."""
    descriptions = {
        "sklearn": "Traditional ML library for single-machine processing",
        "dask": "Parallel computing library for analytics",
        "spark": "Distributed computing system for big data",
        "ray": "Distributed computing framework for ML and AI"
    }
    return descriptions.get(framework, "Unknown framework")


def save_results_to_file(results, filename: str):
    """Save results to JSON file."""
    try:
        if isinstance(results, list):
            # Convert list of results to serializable format
            data = []
            for result in results:
                data.append({
                    "algorithm_name": result.algorithm_name,
                    "framework": result.framework,
                    "dataset_size": result.dataset_size,
                    "feature_count": result.feature_count,
                    "execution_time": result.execution_time,
                    "memory_usage": result.memory_usage,
                    "cpu_usage": result.cpu_usage,
                    "accuracy": result.accuracy,
                    "selected_features": result.selected_features,
                    "best_params": result.best_params,
                    "parameters": result.parameters,
                    "timestamp": result.timestamp.isoformat() if result.timestamp else None
                })
        else:
            # Single result
            data = {
                "algorithm_name": results.algorithm_name,
                "framework": results.framework,
                "dataset_size": results.dataset_size,
                "feature_count": results.feature_count,
                "execution_time": results.execution_time,
                "memory_usage": results.memory_usage,
                "cpu_usage": results.cpu_usage,
                "accuracy": results.accuracy,
                "selected_features": results.selected_features,
                "best_params": results.best_params,
                "parameters": results.parameters,
                "timestamp": results.timestamp.isoformat() if results.timestamp else None
            }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        console.print(f"[green]Results saved to {filename}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error saving results: {e}[/red]")


if __name__ == "__main__":
    app() 
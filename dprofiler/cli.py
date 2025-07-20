#!/usr/bin/env python3
"""
dProfiler Main Command Line Interface
"""

import subprocess
import sys

from typer import Argument, Option, Typer

app = Typer(
    name="dprofiler",
    help="Distributed Algorithm Profiling Tool",
    add_completion=False,
)


@app.command()
def start(
    api: bool = Option(True, "--api/--no-api", help="Start API server"),
    worker: bool = Option(True, "--worker/--no-worker", help="Start worker"),
    host: str = Option("0.0.0.0", "--host", "-h", help="API host"),
    port: int = Option(8000, "--port", "-p", help="API port"),
    reload: bool = Option(False, "--reload", "-r", help="Enable auto-reload"),
) -> None:
    """Start dProfiler services"""
    if api:
        print("🚀 Starting dProfiler API server...")
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "api.main:app",
                    "--host",
                    host,
                    "--port",
                    str(port),
                    "--reload" if reload else "",
                ],
                check=True,
            )
        except KeyboardInterrupt:
            print("\n🛑 API server stopped")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start API server: {e}")
            sys.exit(1)


@app.command()
def worker(
    concurrency: int = Option(
        1, "--concurrency", "-c", help="Number of worker processes"
    ),
    log_level: str = Option("info", "--log-level", "-l", help="Log level"),
) -> None:
    """Start dProfiler worker"""
    print(f"⚙️ Starting dProfiler worker with {concurrency} processes...")
    try:
        subprocess.run(
            [
                "celery",
                "-A",
                "workers.task_queue.celery_app",
                "worker",
                "--loglevel",
                log_level,
                "--concurrency",
                str(concurrency),
            ],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n🛑 Worker stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start worker: {e}")
        sys.exit(1)


@app.command()
def health() -> None:
    """Check system health"""
    print("🏥 Checking dProfiler system health...")

    # Check API health
    try:
        import httpx

        response = httpx.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is healthy")
        else:
            print(f"❌ API health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API health check failed: {e}")

    # Check worker health
    try:
        result = subprocess.run(
            ["celery", "-A", "workers.task_queue.celery_app", "inspect", "active"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("✅ Worker is healthy")
        else:
            print("❌ Worker health check failed")
    except Exception as e:
        print(f"❌ Worker health check failed: {e}")


@app.command()
def test() -> None:
    """Run tests"""
    print("🧪 Running dProfiler tests...")
    try:
        subprocess.run(["pytest", "-v"], check=True)
        print("✅ All tests passed")
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        sys.exit(1)


@app.command()
def install() -> None:
    """Install dProfiler dependencies"""
    print("📦 Installing dProfiler dependencies...")
    try:
        subprocess.run(["uv", "pip", "install", "-e", "."], check=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)


@app.command()
def init() -> None:
    """Initialize dProfiler database"""
    print("🗄️ Initializing dProfiler database...")
    try:
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from core.database import db_manager; db_manager.init_db(); print('Database initialized successfully')",
            ],
            check=True,
        )
        print("✅ Database initialized successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)


@app.command()
def job(
    algorithm: str = Argument(..., help="Algorithm name"),
    input_size: int = Argument(..., help="Input size"),
    parameters: str | None = Option(
        None, "--parameters", "-p", help="Algorithm parameters (JSON)"
    ),
) -> None:
    """Create a profiling job"""
    import json

    import httpx

    payload = {"algorithm_name": algorithm, "input_size": input_size}

    if parameters:
        try:
            payload["parameters"] = json.loads(parameters)
        except json.JSONDecodeError:
            print("❌ Invalid JSON parameters")
            sys.exit(1)

    print(f"📋 Creating job for {algorithm} with input size {input_size}...")

    try:
        response = httpx.post(
            "http://localhost:8000/api/v1/jobs", json=payload, timeout=30
        )
        response.raise_for_status()
        job_data = response.json()
        print(f"✅ Job created with ID: {job_data['job_id']}")
        print(f"Status: {job_data['status']}")
    except Exception as e:
        print(f"❌ Failed to create job: {e}")
        sys.exit(1)


@app.command()
def status() -> None:
    """Show system status"""
    print("📊 dProfiler System Status")
    print("=" * 40)

    # API status
    try:
        import httpx

        response = httpx.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API: Running")
        else:
            print("❌ API: Not responding")
    except:
        print("❌ API: Not available")

    # Worker status
    try:
        result = subprocess.run(
            ["celery", "-A", "workers.task_queue.celery_app", "inspect", "active"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("✅ Worker: Running")
        else:
            print("❌ Worker: Not responding")
    except:
        print("❌ Worker: Not available")

    # Job status
    try:
        response = httpx.get("http://localhost:8000/api/v1/jobs", timeout=5)
        if response.status_code == 200:
            jobs = response.json().get("jobs", [])
            pending = len([j for j in jobs if j["status"] == "pending"])
            running = len([j for j in jobs if j["status"] == "running"])
            completed = len([j for j in jobs if j["status"] == "completed"])
            print(
                f"📋 Jobs: {pending} pending, {running} running, {completed} completed"
            )
        else:
            print("📋 Jobs: Unable to fetch")
    except:
        print("📋 Jobs: Unable to fetch")


def main() -> None:
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()

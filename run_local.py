#!/usr/bin/env python3
"""
Local development script for dProfiler.

This script sets up and runs the dProfiler application locally
for development and testing purposes.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def run_command(cmd, name, cwd=None):
    """Run a command and log output."""
    print(f"Starting {name}...")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        cwd=cwd
    )
    
    # Print output in real-time
    for line in process.stdout:
        print(f"[{name}] {line.rstrip()}")
    
    return process

def check_service(url, name, timeout=30):
    """Check if a service is running."""
    import requests
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {name} is running at {url}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
    
    print(f"❌ {name} failed to start within {timeout} seconds")
    return False

def main():
    """Main function to run the application locally."""
    print("🚀 Starting dProfiler locally...")
    
    # Set environment variables
    os.environ.setdefault("DATABASE_URL", "postgresql://dprofiler:password@localhost:5432/dprofiler")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ.setdefault("SQL_ECHO", "false")
    
    # Check if Docker is running
    try:
        subprocess.run(["docker", "version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running or not installed")
        print("Please install Docker and start it before running this script")
        sys.exit(1)
    
    # Start PostgreSQL and Redis with Docker
    print("📦 Starting PostgreSQL and Redis...")
    docker_cmd = [
        "docker", "run", "--rm", "-d",
        "--name", "dprofiler-postgres",
        "-e", "POSTGRES_DB=dprofiler",
        "-e", "POSTGRES_USER=dprofiler", 
        "-e", "POSTGRES_PASSWORD=password",
        "-p", "5432:5432",
        "postgres:15"
    ]
    
    postgres_process = run_command(docker_cmd, "PostgreSQL")
    
    redis_cmd = [
        "docker", "run", "--rm", "-d",
        "--name", "dprofiler-redis",
        "-p", "6379:6379",
        "redis:7-alpine"
    ]
    
    redis_process = run_command(redis_cmd, "Redis")
    
    # Wait for services to start
    print("⏳ Waiting for services to start...")
    time.sleep(5)
    
    # Check if services are running
    if not check_service("http://localhost:6379", "Redis", timeout=30):
        print("❌ Failed to start Redis")
        sys.exit(1)
    
    # Wait a bit more for PostgreSQL
    time.sleep(5)
    if not check_service("http://localhost:5432", "PostgreSQL", timeout=30):
        print("❌ Failed to start PostgreSQL")
        sys.exit(1)
    
    # Install dependencies
    print("📦 Installing Python dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    
    # Initialize database
    print("🗄️  Initializing database...")
    try:
        from core.database import db_manager
        db_manager.init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)
    
    # Start Celery worker in background
    print("👷 Starting Celery worker...")
    worker_cmd = [sys.executable, "-m", "celery", "-A", "workers.task_queue.celery_app", "worker", "--loglevel=info"]
    worker_process = run_command(worker_cmd, "Celery Worker")
    
    # Start Celery beat for scheduled tasks
    print("⏰ Starting Celery beat...")
    beat_cmd = [sys.executable, "-m", "celery", "-A", "workers.task_queue.celery_app", "beat", "--loglevel=info"]
    beat_process = run_command(beat_cmd, "Celery Beat")
    
    # Wait a bit for workers to start
    time.sleep(3)
    
    # Start API server
    print("🌐 Starting API server...")
    api_cmd = [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    api_process = run_command(api_cmd, "API Server")
    
    # Wait for API to start
    time.sleep(3)
    if not check_service("http://localhost:8000/health", "API Server", timeout=30):
        print("❌ Failed to start API server")
        sys.exit(1)
    
    print("\n🎉 dProfiler is running!")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    print("📈 Metrics: http://localhost:8000/metrics")
    print("\nPress Ctrl+C to stop all services...")
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        
        # Stop all processes
        for process, name in [(api_process, "API Server"), (beat_process, "Celery Beat"), 
                             (worker_process, "Celery Worker"), (redis_process, "Redis"), 
                             (postgres_process, "PostgreSQL")]:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"⚠️  {name} force killed")
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
        
        # Stop Docker containers
        try:
            subprocess.run(["docker", "stop", "dprofiler-redis"], check=True, capture_output=True)
            subprocess.run(["docker", "stop", "dprofiler-postgres"], check=True, capture_output=True)
            print("✅ Docker containers stopped")
        except subprocess.CalledProcessError:
            print("⚠️  Could not stop Docker containers")
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main() 
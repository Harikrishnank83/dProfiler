#!/usr/bin/env python3
"""
dProfiler API Command Line Interface
"""


import uvicorn
from typer import Option, Typer

app = Typer(
    name="dprofiler-api",
    help="dProfiler API Server",
    add_completion=False,
)


@app.command()
def serve(
    host: str = Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = Option(False, "--reload", "-r", help="Enable auto-reload"),
    workers: int = Option(1, "--workers", "-w", help="Number of worker processes"),
    log_level: str = Option("info", "--log-level", "-l", help="Log level"),
) -> None:
    """Start the dProfiler API server"""
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )


@app.command()
def health() -> None:
    """Check API health"""
    import sys

    import httpx

    try:
        response = httpx.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API is healthy")
            print(response.json())
        else:
            print(f"❌ API health check failed: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        sys.exit(1)


@app.command()
def test() -> None:
    """Run API tests"""
    import subprocess
    import sys

    try:
        result = subprocess.run(["pytest", "tests/test_api.py", "-v"], check=True)
        print("✅ API tests passed")
    except subprocess.CalledProcessError:
        print("❌ API tests failed")
        sys.exit(1)


if __name__ == "__main__":
    app()

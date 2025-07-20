#!/usr/bin/env python3
"""
Worker node for dProfiler.

This script runs a Celery worker node that processes profiling jobs
from the distributed task queue.
"""

import logging
import os
import signal
import socket
import sys
from datetime import datetime
from typing import Any

import psutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db_manager
from workers.tasks import health_check_task, register_worker_task

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class WorkerNode:
    """Worker node for distributed processing."""

    def __init__(self, worker_id: str = None):
        self.worker_id = worker_id or f"worker_{socket.gethostname()}_{os.getpid()}"
        self.hostname = socket.gethostname()
        self.ip_address = self._get_ip_address()
        self.running = False
        self.health_check_interval = 30  # seconds

    def _get_ip_address(self) -> str:
        """Get the primary IP address of the worker."""
        try:
            # Get the primary IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def get_system_info(self) -> dict[str, Any]:
        """Get system information for worker registration."""
        try:
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)

            return {
                "worker_id": self.worker_id,
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "cpu_count": cpu_count,
                "memory_total": memory_total_gb,
                "metadata": {
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "pid": os.getpid(),
                    "start_time": datetime.now().isoformat(),
                },
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                "worker_id": self.worker_id,
                "hostname": self.hostname,
                "ip_address": self.ip_address,
                "cpu_count": 1,
                "memory_total": 1.0,
                "metadata": {"error": str(e)},
            }

    async def register_worker(self):
        """Register this worker node."""
        try:
            system_info = self.get_system_info()

            # Register with the task queue
            result = register_worker_task.delay(system_info)
            result.get(timeout=10)  # Wait for registration to complete

            logger.info(f"Worker {self.worker_id} registered successfully")

        except Exception as e:
            logger.error(f"Failed to register worker: {e}")
            raise

    async def start_health_monitoring(self):
        """Start health monitoring loop."""
        logger.info("Starting health monitoring...")

        while self.running:
            try:
                # Send health check
                result = health_check_task.delay()
                health_info = result.get(timeout=5)

                if health_info.get("status") == "healthy":
                    logger.debug(
                        f"Health check passed: CPU {health_info.get('cpu_usage', 0):.1f}%"
                    )
                else:
                    logger.warning(
                        f"Health check failed: {health_info.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                logger.error(f"Health check error: {e}")

            # Wait for next health check
            await asyncio.sleep(self.health_check_interval)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down worker...")
        self.running = False

    async def run(self):
        """Run the worker node."""
        try:
            # Set up signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)
            signal.signal(signal.SIGTERM, self.signal_handler)

            # Initialize database connection
            db_manager.init_db()

            # Start worker
            self.running = True
            logger.info(f"Starting worker {self.worker_id} on {self.hostname}")

            # Start Celery worker using subprocess
            import subprocess

            worker_cmd = [
                "celery",
                "-A",
                "workers.task_queue.celery_app",
                "worker",
                "--loglevel=INFO",
                "--concurrency=1",
                "--hostname=" + self.worker_id,
                "--queues=profiling,default",
            ]

            # Start worker process
            process = subprocess.Popen(worker_cmd)
            process.wait()

        except KeyboardInterrupt:
            logger.info("Worker interrupted by user")
        except Exception as e:
            logger.error(f"Worker error: {e}")
            raise
        finally:
            self.running = False
            logger.info("Worker shutdown complete")


def main():
    """Main entry point for the worker."""
    import argparse

    parser = argparse.ArgumentParser(description="dProfiler Worker Node")
    parser.add_argument(
        "--worker-id", help="Custom worker ID (default: auto-generated)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)",
    )
    parser.add_argument(
        "--queues",
        default="default",
        help="Comma-separated list of queues to process (default: default)",
    )
    parser.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.loglevel))

    # Create and run worker
    worker = WorkerNode(args.worker_id)

    try:
        import asyncio

        asyncio.run(worker.run())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

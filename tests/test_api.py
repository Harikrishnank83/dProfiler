"""
Tests for the dProfiler API endpoints.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from core.database import get_db
from core.models import Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealthCheck:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test that health check returns 200."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestJobs:
    """Test job management endpoints."""

    def test_create_job(self):
        """Test creating a new job."""
        job_data = {
            "algorithm_name": "bubble_sort",
            "input_size": 1000,
            "parameters": {"method": "standard"},
            "priority": 1,
        }

        response = client.post("/api/v1/jobs", json=job_data)
        assert response.status_code == 200

        data = response.json()
        assert data["algorithm_name"] == "bubble_sort"
        assert data["input_size"] == 1000
        assert data["status"] == "pending"
        assert "job_id" in data

    def test_list_jobs(self):
        """Test listing jobs."""
        response = client.get("/api/v1/jobs")
        assert response.status_code == 200

        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert "page" in data

    def test_get_job(self):
        """Test getting a specific job."""
        # First create a job
        job_data = {"algorithm_name": "quick_sort", "input_size": 500, "parameters": {}}

        create_response = client.post("/api/v1/jobs", json=job_data)
        job_id = create_response.json()["job_id"]

        # Then get the job
        response = client.get(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == job_id
        assert data["algorithm_name"] == "quick_sort"

    def test_get_nonexistent_job(self):
        """Test getting a job that doesn't exist."""
        response = client.get("/api/v1/jobs/nonexistent-id")
        assert response.status_code == 404

    def test_delete_job(self):
        """Test deleting a job."""
        # First create a job
        job_data = {"algorithm_name": "merge_sort", "input_size": 200, "parameters": {}}

        create_response = client.post("/api/v1/jobs", json=job_data)
        job_id = create_response.json()["job_id"]

        # Then delete the job
        response = client.delete(f"/api/v1/jobs/{job_id}")
        assert response.status_code == 200

        # Verify job is deleted
        get_response = client.get(f"/api/v1/jobs/{job_id}")
        assert get_response.status_code == 404


class TestWorkers:
    """Test worker management endpoints."""

    def test_list_workers(self):
        """Test listing workers."""
        response = client.get("/api/v1/workers")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)


class TestMetrics:
    """Test metrics endpoints."""

    def test_get_system_metrics(self):
        """Test getting system metrics."""
        response = client.get("/api/v1/metrics")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)


class TestAlgorithms:
    """Test algorithm endpoints."""

    def test_list_algorithms(self):
        """Test listing available algorithms."""
        response = client.get("/api/v1/algorithms")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Should include the built-in sorting algorithms
        algorithm_names = [alg["name"] for alg in data]
        assert "bubble_sort" in algorithm_names
        assert "quick_sort" in algorithm_names
        assert "merge_sort" in algorithm_names


class TestAlgorithmComparison:
    """Test algorithm comparison endpoint."""

    def test_compare_algorithms(self):
        """Test comparing multiple algorithms."""
        comparison_data = {
            "algorithms": ["bubble_sort", "quick_sort"],
            "input_size": 1000,
            "iterations": 1,
        }

        response = client.post("/api/v1/compare", json=comparison_data)
        assert response.status_code == 200

        data = response.json()
        assert "comparison_id" in data
        assert "results" in data
        assert len(data["results"]) == 2


# Cleanup after tests
def teardown_module(module):
    """Clean up test database."""
    import os

    if os.path.exists("./test.db"):
        os.remove("./test.db")

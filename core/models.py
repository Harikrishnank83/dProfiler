"""
Database models for the dProfiler application.

This module defines the SQLAlchemy models for storing profiling jobs,
results, and related metadata.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Job(Base):
    """Model for profiling jobs."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)
    algorithm_name = Column(String(255), nullable=False)
    input_size = Column(Integer, nullable=False)
    parameters = Column(JSON, nullable=True)
    status = Column(
        String(50), default="pending"
    )  # pending, running, completed, failed
    priority = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    worker_id = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    results = relationship(
        "ProfilingResult", back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Job(id={self.id}, job_id='{self.job_id}', algorithm='{self.algorithm_name}', status='{self.status}')>"


class ProfilingResult(Base):
    """Model for profiling results."""

    __tablename__ = "profiling_results"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    algorithm_name = Column(String(255), nullable=False)
    input_size = Column(Integer, nullable=False)
    execution_time = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)  # MB
    cpu_usage = Column(Float, nullable=False)  # Percentage
    iterations = Column(Integer, default=1)
    parameters = Column(JSON, nullable=True)
    result_metadata = Column(JSON, nullable=True)  # Renamed from metadata
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("Job", back_populates="results")

    def __repr__(self):
        return f"<ProfilingResult(id={self.id}, algorithm='{self.algorithm_name}', time={self.execution_time:.4f}s)>"


class WorkerNode(Base):
    """Model for worker node registration."""

    __tablename__ = "worker_nodes"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(255), unique=True, index=True, nullable=False)
    hostname = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=False)  # IPv6 compatible
    cpu_count = Column(Integer, nullable=False)
    memory_total = Column(Float, nullable=False)  # GB
    status = Column(String(50), default="active")  # active, inactive, offline
    last_heartbeat = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    worker_metadata = Column(JSON, nullable=True)  # Renamed from metadata

    def __repr__(self):
        return f"<WorkerNode(id={self.id}, worker_id='{self.worker_id}', status='{self.status}')>"


class AlgorithmRegistry(Base):
    """Model for registered algorithms."""

    __tablename__ = "algorithm_registry"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    parameters_schema = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<AlgorithmRegistry(id={self.id}, name='{self.name}', category='{self.category}')>"


class SystemMetrics(Base):
    """Model for system-level metrics."""

    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    cpu_usage = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    disk_usage = Column(Float, nullable=True)
    network_in = Column(Float, nullable=True)
    network_out = Column(Float, nullable=True)
    active_jobs = Column(Integer, default=0)

    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, worker_id='{self.worker_id}', cpu={self.cpu_usage:.2f}%)>"



# Pydantic models for API requests/responses
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Request model for creating a new job."""

    algorithm_name: str = Field(..., description="Name of the algorithm to profile")
    input_size: int = Field(..., gt=0, description="Size of input data")
    parameters: dict[str, Any] | None = Field(
        default=None, description="Algorithm parameters"
    )
    priority: int | None = Field(
        default=0, description="Job priority (higher = more important)"
    )


class JobResponse(BaseModel):
    """Response model for job information."""

    id: int
    job_id: str
    algorithm_name: str
    input_size: int
    parameters: dict[str, Any] | None
    status: str
    priority: int
    created_at: datetime
    updated_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    worker_id: str | None
    error_message: str | None

    class Config:
        from_attributes = True


class ProfilingResultResponse(BaseModel):
    """Response model for profiling results."""

    id: int
    job_id: int
    algorithm_name: str
    input_size: int
    execution_time: float
    memory_usage: float
    cpu_usage: float
    iterations: int
    parameters: dict[str, Any] | None
    result_metadata: dict[str, Any] | None  # Renamed from metadata
    timestamp: datetime

    class Config:
        from_attributes = True


class WorkerNodeResponse(BaseModel):
    """Response model for worker node information."""

    id: int
    worker_id: str
    hostname: str
    ip_address: str
    cpu_count: int
    memory_total: float
    status: str
    last_heartbeat: datetime
    created_at: datetime
    worker_metadata: dict[str, Any] | None  # Renamed from metadata

    class Config:
        from_attributes = True


class SystemMetricsResponse(BaseModel):
    """Response model for system metrics."""

    id: int
    worker_id: str | None
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float | None
    network_in: float | None
    network_out: float | None
    active_jobs: int

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response model for job list with pagination."""

    jobs: list[JobResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class AlgorithmComparisonResponse(BaseModel):
    """Response model for algorithm comparison results."""

    comparison_id: str
    algorithms: list[str]
    input_size: int
    results: list[ProfilingResultResponse]
    created_at: datetime
    summary: dict[str, Any]


class AlgorithmComparisonRequest(BaseModel):
    """Request model for algorithm comparison."""

    algorithms: list[str] = Field(..., description="List of algorithm names to compare")
    input_size: int = Field(..., gt=0, description="Size of input data")
    parameters_list: list[dict[str, Any]] | None = Field(
        default=None, description="List of parameters for each algorithm"
    )
    iterations: int = Field(default=1, ge=1, le=100, description="Number of iterations")

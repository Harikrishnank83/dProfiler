# dProfiler Architecture Documentation

## System Overview

dProfiler is a distributed algorithm profiling system designed to analyze and optimize algorithms across multiple compute nodes. The system provides real-time monitoring, comprehensive logging, and scalable job processing capabilities.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              dProfiler System Architecture                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web API       │    │   Message Queue │    │   Worker Nodes  │    │   Task Scheduler │
│   (FastAPI)     │◄──►│   (Redis)       │◄──►│   (Celery)      │◄──►│   (Celery Beat)  │
│   Port: 8000    │    │   Port: 6379    │    │   Multiple      │    │   Scheduled      │
│                 │    │                 │    │   Instances     │    │   Tasks          │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Monitoring    │    │   Logging       │    │   Health Checks │
│   (PostgreSQL)  │    │   (Prometheus)  │    │   (Structured)  │    │   (System)      │
│   Port: 5432    │    │   Port: 8000    │    │   (JSON)        │    │   (30s)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Data Flow                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 1. Client → API: Submit profiling job                                           │
│ 2. API → Database: Store job metadata                                           │
│ 3. API → Redis: Queue job for processing                                        │
│ 4. Worker ← Redis: Pick up job from queue                                       │
│ 5. Worker → Database: Update job status to "running"                            │
│ 6. Worker: Execute algorithm profiling                                          │
│ 7. Worker → Database: Store profiling results                                   │
│ 8. Worker → Database: Update job status to "completed"                          │
│ 9. API ← Database: Retrieve results for client                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Web API (FastAPI)

**Purpose**: RESTful API for job management and system monitoring

**Technology**: FastAPI with Uvicorn ASGI server

**Key Features**:
- RESTful endpoints for job CRUD operations
- OpenAPI/Swagger documentation
- Prometheus metrics integration
- Health check endpoints
- CORS middleware for cross-origin requests
- Request/response logging middleware

**Endpoints**:
- `GET /health` - System health check
- `GET /metrics` - Prometheus metrics
- `GET /docs` - Interactive API documentation
- `POST /api/v1/jobs` - Create profiling job
- `GET /api/v1/jobs` - List jobs with pagination
- `GET /api/v1/jobs/{job_id}` - Get specific job
- `GET /api/v1/jobs/{job_id}/results` - Get job results
- `DELETE /api/v1/jobs/{job_id}` - Delete job
- `POST /api/v1/compare` - Compare algorithms
- `GET /api/v1/algorithms` - List available algorithms
- `GET /api/v1/workers` - List worker nodes
- `GET /api/v1/metrics` - Get system metrics

**Configuration**:
- Database connection pooling
- Redis connection for task queue
- Prometheus metrics collection
- Structured logging

### 2. Message Queue (Redis)

**Purpose**: Distributed task queue for job processing

**Technology**: Redis with Celery backend

**Key Features**:
- Persistent message storage
- Task routing and prioritization
- Result backend for task results
- Pub/sub for worker communication
- Scheduled task support

**Queues**:
- `profiling` - Algorithm profiling tasks
- `system` - System maintenance tasks
- `maintenance` - Cleanup and maintenance tasks

**Configuration**:
- Connection pooling
- Task serialization (JSON)
- Result expiration (1 hour)
- Worker prefetch settings

### 3. Worker Nodes (Celery)

**Purpose**: Distributed job processing and algorithm execution

**Technology**: Celery workers with psutil monitoring

**Key Features**:
- Algorithm profiling with performance metrics
- System resource monitoring
- Task execution and result storage
- Worker health monitoring
- Automatic task retry on failure

**Capabilities**:
- CPU usage monitoring
- Memory usage tracking
- Execution time measurement
- Built-in algorithm support
- Custom algorithm integration

**Built-in Algorithms**:
- Bubble Sort
- Quick Sort
- Merge Sort

**Monitoring**:
- Real-time system metrics
- Task execution statistics
- Worker health checks
- Resource utilization tracking

### 4. Task Scheduler (Celery Beat)

**Purpose**: Scheduled task execution and maintenance

**Technology**: Celery Beat with cron-like scheduling

**Scheduled Tasks**:
- Health checks (every 30 seconds)
- Metrics cleanup (daily at 2 AM)
- System maintenance tasks
- Periodic health monitoring

### 5. Database (PostgreSQL)

**Purpose**: Persistent storage for jobs, results, and system data

**Technology**: PostgreSQL with SQLAlchemy ORM

**Schema**:
- `jobs` - Profiling job metadata
- `profiling_results` - Algorithm execution results
- `worker_nodes` - Worker registration and status
- `system_metrics` - System performance metrics
- `algorithm_registry` - Available algorithms

**Features**:
- Connection pooling
- Transaction management
- Data integrity constraints
- Indexing for performance
- Backup and recovery

### 6. Monitoring (Prometheus)

**Purpose**: System metrics collection and monitoring

**Technology**: Prometheus client library

**Metrics**:
- HTTP request duration and count
- Job creation and completion rates
- System resource utilization
- Worker node statistics
- Database connection metrics

**Integration**:
- FastAPI middleware for request metrics
- Custom metrics for business logic
- System metrics from psutil
- Prometheus format export

### 7. Logging (Structured)

**Purpose**: Comprehensive system logging and debugging

**Technology**: Python logging with JSON formatting

**Features**:
- Structured JSON logging
- Correlation IDs for request tracking
- Log levels (DEBUG, INFO, WARNING, ERROR)
- Centralized log collection
- Performance monitoring

**Log Sources**:
- API request/response logging
- Worker task execution logs
- Database operation logs
- System health check logs
- Error and exception logging

### 8. Health Checks

**Purpose**: System health monitoring and alerting

**Technology**: Custom health check endpoints

**Checks**:
- Database connectivity
- Redis connectivity
- Worker node status
- API responsiveness
- System resource availability

**Features**:
- Automated health monitoring
- Health status reporting
- Dependency checking
- Alerting integration

## Data Models

### Job Model
```python
class Job:
    id: int
    job_id: str (UUID)
    algorithm_name: str
    input_size: int
    parameters: JSON
    status: str (pending, running, completed, failed)
    priority: int
    created_at: datetime
    updated_at: datetime
    started_at: datetime
    completed_at: datetime
    worker_id: str
    error_message: str
```

### ProfilingResult Model
```python
class ProfilingResult:
    id: int
    job_id: int (FK to Job)
    algorithm_name: str
    input_size: int
    execution_time: float
    memory_usage: float (MB)
    cpu_usage: float (%)
    iterations: int
    parameters: JSON
    result_metadata: JSON
    timestamp: datetime
```

### WorkerNode Model
```python
class WorkerNode:
    id: int
    worker_id: str
    hostname: str
    ip_address: str
    cpu_count: int
    memory_total: float (GB)
    status: str (active, inactive, offline)
    last_heartbeat: datetime
    created_at: datetime
    worker_metadata: JSON
```

### SystemMetrics Model
```python
class SystemMetrics:
    id: int
    worker_id: str
    timestamp: datetime
    cpu_usage: float (%)
    memory_usage: float (%)
    disk_usage: float (%)
    network_in: float (MB)
    network_out: float (MB)
    active_jobs: int
```

## Deployment Architectures

### 1. Docker Compose (Development)

**Use Case**: Local development and testing

**Components**:
- Single PostgreSQL instance
- Single Redis instance
- Single API instance
- Single Worker instance
- Shared network

**Benefits**:
- Easy setup and teardown
- Consistent development environment
- Quick iteration and testing

### 2. Kubernetes (Production)

**Use Case**: Production deployment and scaling

**Components**:
- PostgreSQL with persistent storage
- Redis cluster for high availability
- Multiple API replicas with load balancing
- Multiple worker replicas with auto-scaling
- Ingress controller for external access
- Horizontal Pod Autoscaler for workers

**Benefits**:
- High availability and fault tolerance
- Automatic scaling based on load
- Resource isolation and management
- Rolling updates and rollbacks
- Monitoring and logging integration

### 3. Hybrid Deployment

**Use Case**: Mixed development and production environments

**Components**:
- Shared database and Redis infrastructure
- Isolated API and worker deployments
- Environment-specific configurations
- Shared monitoring and logging

## Security Considerations

### 1. Network Security
- Service-to-service communication over internal networks
- External access through load balancers
- Network policies for pod-to-pod communication
- TLS/SSL encryption for external traffic

### 2. Data Security
- Database connection encryption
- Sensitive data encryption at rest
- Secure credential management
- Access control and authentication

### 3. Application Security
- Input validation and sanitization
- SQL injection prevention
- Rate limiting and DDoS protection
- Security headers and CORS configuration

## Performance Characteristics

### 1. Scalability
- **Horizontal Scaling**: Add more worker nodes
- **Vertical Scaling**: Increase CPU/memory limits
- **Database Scaling**: Read replicas and connection pooling
- **Cache Scaling**: Redis cluster for high availability

### 2. Performance Metrics
- **API Response Time**: < 100ms for most endpoints
- **Job Processing**: Depends on algorithm complexity
- **Database Queries**: Optimized with indexes
- **Memory Usage**: Efficient resource utilization

### 3. Monitoring and Alerting
- **Prometheus Metrics**: Real-time system monitoring
- **Grafana Dashboards**: Visualization and alerting
- **Log Aggregation**: Centralized logging with ELK stack
- **Health Checks**: Automated health monitoring

## Integration Points

### 1. External Systems
- **CI/CD Pipelines**: Automated testing and deployment
- **Monitoring Systems**: Prometheus, Grafana, AlertManager
- **Logging Systems**: ELK stack, Fluentd, Logstash
- **Authentication**: OAuth2, JWT, LDAP integration

### 2. API Integrations
- **RESTful API**: Standard HTTP endpoints
- **OpenAPI Specification**: Auto-generated documentation
- **Webhook Support**: Event-driven integrations
- **GraphQL Support**: Future enhancement

### 3. Data Export
- **CSV Export**: Job and result data
- **JSON Export**: API responses
- **Prometheus Export**: Metrics data
- **Database Backup**: Automated backup procedures

## Future Enhancements

### 1. Advanced Features
- **Real-time Streaming**: WebSocket support for live updates
- **Algorithm Registry**: Dynamic algorithm registration
- **Result Visualization**: Charts and graphs for results
- **Machine Learning**: Automated algorithm optimization

### 2. Infrastructure Improvements
- **Service Mesh**: Istio for advanced networking
- **Multi-cluster**: Cross-cluster deployment
- **Edge Computing**: Distributed worker deployment
- **Serverless**: Function-based processing

### 3. Monitoring Enhancements
- **Distributed Tracing**: Jaeger integration
- **Advanced Metrics**: Custom business metrics
- **Predictive Analytics**: Performance prediction
- **Automated Remediation**: Self-healing systems 
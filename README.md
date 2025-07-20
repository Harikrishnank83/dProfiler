# dProfiler - Distributed Algorithm Profiling Tool

A distributed profiling tool designed to analyze and optimize algorithms across multiple compute nodes with comprehensive monitoring and logging capabilities.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              dProfiler Architecture                              │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web API       │    │   Message Queue │    │   Worker Nodes  │    │   Task Scheduler │
│   (FastAPI)     │◄──►│   (Redis)       │◄──►│   (Celery)      │◄──►│   (Celery Beat)  │
│   Port: 8000    │    │   Port: 6379    │    │   Multiple      │    │   Scheduled      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │    │   Monitoring    │    │   Logging       │    │   Health Checks │
│   (PostgreSQL)  │    │   (Prometheus)  │    │   (Structured)  │    │   (System)      │
│   Port: 5432    │    │   Port: 8000    │    │   (JSON)        │    │   (30s)         │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Core Components                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│ • Algorithm Profiler: Performance monitoring with psutil                        │
│ • Task Queue: Celery with Redis backend                                        │
│ • Database Models: Jobs, Results, Workers, Metrics                             │
│ • API Endpoints: RESTful with OpenAPI documentation                            │
│ • Built-in Algorithms: Bubble Sort, Quick Sort, Merge Sort                     │
│ • Metrics Collection: Prometheus format                                        │
│ • Health Monitoring: Database and service health checks                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Features

- **Distributed Execution**: Scale profiling tasks across multiple worker nodes
- **Real-time Monitoring**: Live metrics and performance tracking via Prometheus
- **Comprehensive Logging**: Structured logging with correlation IDs
- **RESTful API**: Easy integration with existing systems
- **Containerized Deployment**: Docker-based deployment for consistency
- **Algorithm Comparison**: Compare multiple algorithms on same input data
- **Job Management**: Create, monitor, and manage profiling jobs
- **System Metrics**: CPU, memory, disk, and network monitoring
- **Health Checks**: Automated health monitoring and reporting
- **API Documentation**: Interactive Swagger UI and ReDoc

## Quick Start

### Prerequisites

- **Docker and Docker Compose** (for containerized deployment)
- **Python 3.9+** (for local development)
- **Git**

### Option 1: Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd dProfiler
   ```

2. **Start all services:**
   ```bash
   docker compose up -d
   ```

3. **Initialize the database:**
   ```bash
   docker compose exec api python -c "from core.database import db_manager; db_manager.init_db(); print('Database initialized successfully')"
   ```

4. **Verify services are running:**
   ```bash
   docker compose ps
   ```

5. **Test the application:**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Create a profiling job
   curl -X POST http://localhost:8000/api/v1/jobs \
     -H "Content-Type: application/json" \
     -d '{"algorithm_name": "bubble_sort", "input_size": 1000}'
   ```

### Option 2: Local Development

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd dProfiler
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start infrastructure services:**
   ```bash
   # Start PostgreSQL
   docker run -d --name dprofiler-postgres \
     -e POSTGRES_DB=dprofiler \
     -e POSTGRES_USER=dprofiler \
     -e POSTGRES_PASSWORD=password \
     -p 5432:5432 postgres:15
   
   # Start Redis
   docker run -d --name dprofiler-redis \
     -p 6379:6379 redis:7-alpine
   ```

3. **Set environment variables:**
   ```bash
   export DATABASE_URL="postgresql://dprofiler:password@localhost:5432/dprofiler"
   export REDIS_URL="redis://localhost:6379/0"
   ```

4. **Initialize database:**
   ```bash
   python -c "from core.database import db_manager; db_manager.init_db()"
   ```

5. **Start services:**
   ```bash
   # Terminal 1: Start API server
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   
   # Terminal 2: Start Celery worker
   celery -A workers.task_queue.celery_app worker --loglevel=info
   
   # Terminal 3: Start Celery beat (optional)
   celery -A workers.task_queue.celery_app beat --loglevel=info
   ```

### Option 3: Kubernetes Deployment

1. **Create namespace:**
   ```bash
   kubectl create namespace dprofiler
   kubectl config set-context --current --namespace=dprofiler
   ```

2. **Create ConfigMap for configuration:**
   ```yaml
   # configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: dprofiler-config
   data:
     DATABASE_URL: "postgresql://dprofiler:password@postgres-service:5432/dprofiler"
     REDIS_URL: "redis://redis-service:6379/0"
     SQL_ECHO: "false"
   ```

3. **Create PostgreSQL deployment:**
   ```yaml
   # postgres.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: postgres
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: postgres
     template:
       metadata:
         labels:
           app: postgres
       spec:
         containers:
         - name: postgres
           image: postgres:15
           env:
           - name: POSTGRES_DB
             value: dprofiler
           - name: POSTGRES_USER
             value: dprofiler
           - name: POSTGRES_PASSWORD
             value: password
           ports:
           - containerPort: 5432
           volumeMounts:
           - name: postgres-storage
             mountPath: /var/lib/postgresql/data
         volumes:
         - name: postgres-storage
           persistentVolumeClaim:
             claimName: postgres-pvc
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: postgres-service
   spec:
     selector:
       app: postgres
     ports:
     - port: 5432
       targetPort: 5432
   ---
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: postgres-pvc
   spec:
     accessModes:
       - ReadWriteOnce
     resources:
       requests:
         storage: 10Gi
   ```

4. **Create Redis deployment:**
   ```yaml
   # redis.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: redis
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: redis
     template:
       metadata:
         labels:
           app: redis
       spec:
         containers:
         - name: redis
           image: redis:7-alpine
           ports:
           - containerPort: 6379
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: redis-service
   spec:
     selector:
       app: redis
     ports:
     - port: 6379
       targetPort: 6379
   ```

5. **Create API deployment:**
   ```yaml
   # api.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: dprofiler-api
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: dprofiler-api
     template:
       metadata:
         labels:
           app: dprofiler-api
       spec:
         containers:
         - name: api
           image: dprofiler-api:latest
           ports:
           - containerPort: 8000
           envFrom:
           - configMapRef:
               name: dprofiler-config
           resources:
             requests:
               memory: "256Mi"
               cpu: "250m"
             limits:
               memory: "512Mi"
               cpu: "500m"
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: dprofiler-api-service
   spec:
     selector:
       app: dprofiler-api
     ports:
     - port: 80
       targetPort: 8000
     type: LoadBalancer
   ```

6. **Create Worker deployment:**
   ```yaml
   # worker.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: dprofiler-worker
   spec:
     replicas: 2  # Scale workers as needed
     selector:
       matchLabels:
         app: dprofiler-worker
     template:
       metadata:
         labels:
           app: dprofiler-worker
       spec:
         containers:
         - name: worker
           image: dprofiler-worker:latest
           envFrom:
           - configMapRef:
               name: dprofiler-config
           resources:
             requests:
               memory: "512Mi"
               cpu: "500m"
             limits:
               memory: "1Gi"
               cpu: "1000m"
   ```

7. **Deploy to Kubernetes:**
   ```bash
   # Apply all configurations
   kubectl apply -f configmap.yaml
   kubectl apply -f postgres.yaml
   kubectl apply -f redis.yaml
   kubectl apply -f api.yaml
   kubectl apply -f worker.yaml
   
   # Wait for deployments to be ready
   kubectl wait --for=condition=available --timeout=300s deployment/postgres
   kubectl wait --for=condition=available --timeout=300s deployment/redis
   kubectl wait --for=condition=available --timeout=300s deployment/dprofiler-api
   kubectl wait --for=condition=available --timeout=300s deployment/dprofiler-worker
   
   # Initialize database
   kubectl exec deployment/dprofiler-api -- python -c "from core.database import db_manager; db_manager.init_db()"
   
   # Get service URL
   kubectl get service dprofiler-api-service
   ```

## API Usage Examples

### Create a Profiling Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm_name": "quick_sort",
    "input_size": 10000,
    "parameters": {"pivot_strategy": "median"},
    "priority": 1
  }'
```

### Check Job Status
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### Get Profiling Results
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}/results
```

### Compare Algorithms
```bash
curl -X POST "http://localhost:8000/api/v1/compare?input_size=1000&iterations=3" \
  -H "Content-Type: application/json" \
  -d '{"algorithms": ["bubble_sort", "quick_sort", "merge_sort"]}'
```

### List Available Algorithms
```bash
curl http://localhost:8000/api/v1/algorithms
```

### View System Metrics
```bash
curl http://localhost:8000/metrics
```

## Monitoring and Observability

### Health Checks
- **API Health**: `GET /health`
- **Database Health**: Included in API health check
- **Worker Health**: Monitored via Celery

### Metrics
- **Prometheus Metrics**: `GET /metrics`
- **Custom Metrics**: Job creation, completion, request duration
- **System Metrics**: CPU, memory, disk usage

### Logging
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Log Sources**: API, Workers, Database operations

## Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_api.py
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Adding New Algorithms
1. Add algorithm function to `core/profiler.py`
2. Register in `workers/tasks.py`
3. Add to algorithm list in `api/main.py`
4. Update tests

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check if PostgreSQL is running
   docker compose ps postgres
   
   # Check logs
   docker compose logs postgres
   
   # Restart service
   docker compose restart postgres
   ```

2. **Redis Connection Failed**
   ```bash
   # Check if Redis is running
   docker compose ps redis
   
   # Check logs
   docker compose logs redis
   
   # Restart service
   docker compose restart redis
   ```

3. **Worker Not Processing Jobs**
   ```bash
   # Check worker logs
   docker compose logs worker
   
   # Restart worker
   docker compose restart worker
   
   # Check Celery status
   docker compose exec api celery -A workers.task_queue.celery_app inspect active
   ```

4. **API Server Not Responding**
   ```bash
   # Check API logs
   docker compose logs api
   
   # Restart API
   docker compose restart api
   
   # Check health
   curl http://localhost:8000/health
   ```

### Debug Mode
```bash
# Set debug environment variables
export LOG_LEVEL=DEBUG
export SQL_ECHO=true

# Restart services
docker compose down
docker compose up -d
```

## Production Deployment

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:password@host:port/db
REDIS_URL=redis://host:port/db

# Optional
LOG_LEVEL=INFO
SQL_ECHO=false
WORKER_CONCURRENCY=4
```

### Security Considerations
- Use strong passwords for database
- Enable SSL/TLS for database connections
- Implement authentication/authorization
- Use secrets management for sensitive data
- Configure network policies in Kubernetes

### Scaling
- **Horizontal Scaling**: Add more worker replicas
- **Vertical Scaling**: Increase CPU/memory limits
- **Database Scaling**: Use read replicas for queries
- **Cache Scaling**: Use Redis cluster for high availability

## Project Structure

```
dProfiler/
├── api/                    # FastAPI web service
│   ├── main.py            # Main API application
│   └── __init__.py
├── workers/                # Distributed worker nodes
│   ├── worker.py          # Worker node implementation
│   ├── tasks.py           # Celery task definitions
│   ├── task_queue.py      # Task queue configuration
│   └── __init__.py
├── core/                   # Core profiling logic
│   ├── profiler.py        # Algorithm profiling engine
│   ├── database.py        # Database configuration
│   ├── models.py          # Data models
│   └── __init__.py
├── tests/                  # Test suite
│   ├── test_api.py        # API endpoint tests
│   └── __init__.py
├── k8s/                    # Kubernetes deployment
│   ├── namespace.yaml     # Namespace definition
│   ├── configmap.yaml     # Configuration
│   ├── postgres.yaml      # PostgreSQL deployment
│   ├── redis.yaml         # Redis deployment
│   ├── api.yaml           # API deployment
│   ├── worker.yaml        # Worker deployment
│   └── deploy.sh          # Deployment script
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile             # Application containerization
├── requirements.txt       # Python dependencies
├── run_local.py          # Local development script
├── TESTING.md            # Testing guide
├── ARCHITECTURE.md       # Architecture documentation
└── README.md             # Project documentation
```

## 📚 **Help & Documentation**

### **Getting Started**
- **[Quick Start Guide](docs/help-guides/quick-start.md)** - Get up and running in 5 minutes
- **[Basic Usage](docs/help-guides/usage/basic.md)** - Learn fundamental concepts
- **[Real-World Examples](docs/help-guides/usage/examples.md)** - Practical usage scenarios

### **Deployment Guides**
- **[Docker Deployment](docs/help-guides/deployment/docker.md)** - Deploy with Docker Compose
- **[Kubernetes Deployment](docs/help-guides/deployment/kubernetes.md)** - Deploy to Kubernetes
- **[Production Setup](docs/help-guides/deployment/production.md)** - Production-ready deployment

### **Troubleshooting**
- **[Common Issues](docs/help-guides/troubleshooting/common-issues.md)** - Solutions to common problems
- **[Health Checks](docs/help-guides/troubleshooting/health-checks.md)** - System health monitoring
- **[Debug Guide](docs/help-guides/troubleshooting/debug.md)** - Debugging and diagnostics

### **Complete Help Guide**
- **[Help Guides Index](docs/help-guides/README.md)** - Complete documentation index

## 🛠️ **Quick Commands**

```bash
# Start everything
make up              # Start all services
make health          # Check system health

# Testing
make test            # Run all tests
make test-api-endpoints  # Test API endpoints

# Troubleshooting
make troubleshoot    # Run diagnostics
make logs            # View logs
make restart         # Restart services

# Cleanup
make down            # Stop services
make clean           # Clean everything
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details 
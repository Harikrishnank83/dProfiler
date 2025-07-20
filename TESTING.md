# Testing Guide for dProfiler

This guide provides comprehensive instructions for running and testing the dProfiler application.

## Prerequisites

Before running the application, ensure you have the following installed:

- **Python 3.9+**
- **Docker and Docker Compose**
- **Git**

## Quick Start

### Option 1: Using Docker Compose (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd dProfiler
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Check service status:**
   ```bash
   docker-compose ps
   ```

4. **View logs:**
   ```bash
   # All services
   docker-compose logs -f
   
   # Specific service
   docker-compose logs -f api
   docker-compose logs -f worker
   ```

5. **Stop services:**
   ```bash
   docker-compose down
   ```

### Option 2: Using Local Development Script

1. **Run the local development script:**
   ```bash
   python run_local.py
   ```

   This script will:
   - Start PostgreSQL and Redis using Docker
   - Install Python dependencies
   - Initialize the database
   - Start Celery worker and beat
   - Start the API server
   - Provide real-time logs

2. **Stop the application:**
   Press `Ctrl+C` to stop all services

## Testing the Application

### 1. Health Check

Verify that all services are running:

```bash
# API Health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "database": {
    "connected": true,
    "connection_info": {...}
  }
}
```

### 2. API Documentation

Access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Create a Profiling Job

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm_name": "bubble_sort",
    "input_size": 1000,
    "parameters": {"method": "standard"},
    "priority": 1
  }'
```

Expected response:
```json
{
  "id": 1,
  "job_id": "uuid-here",
  "algorithm_name": "bubble_sort",
  "input_size": 1000,
  "parameters": {"method": "standard"},
  "status": "pending",
  "priority": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "worker_id": null,
  "error_message": null
}
```

### 4. List Jobs

```bash
curl http://localhost:8000/api/v1/jobs
```

### 5. Get Job Results

```bash
# Replace JOB_ID with the actual job ID from step 3
curl http://localhost:8000/api/v1/jobs/JOB_ID/results
```

### 6. Compare Algorithms

```bash
curl -X POST http://localhost:8000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{
    "algorithms": ["bubble_sort", "quick_sort", "merge_sort"],
    "input_size": 1000,
    "iterations": 3
  }'
```

### 7. View System Metrics

```bash
curl http://localhost:8000/api/v1/metrics
```

### 8. List Available Algorithms

```bash
curl http://localhost:8000/api/v1/algorithms
```

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_api.py

# Run with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Integration Tests

```bash
# Start services for integration testing
docker-compose up -d

# Run integration tests
pytest tests/ -m integration

# Stop services
docker-compose down
```

### Performance Tests

```bash
# Run load tests (if available)
pytest tests/test_performance.py

# Or use a tool like Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health
```

## Monitoring and Debugging

### 1. View Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

### 2. Check Celery Worker Status

```bash
# If running locally
celery -A workers.task_queue.celery_app inspect active

# If running in Docker
docker-compose exec worker celery -A workers.task_queue.celery_app inspect active
```

### 3. Monitor Task Queue

```bash
# View queue statistics
curl http://localhost:8000/api/v1/queue/stats

# Monitor worker nodes
curl http://localhost:8000/api/v1/workers
```

### 4. Database Queries

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U dprofiler -d dprofiler

# Example queries:
SELECT * FROM jobs LIMIT 5;
SELECT * FROM profiling_results LIMIT 5;
SELECT * FROM worker_nodes;
SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT 10;
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   # Check if PostgreSQL is running
   docker-compose ps postgres
   
   # Check logs
   docker-compose logs postgres
   
   # Restart the service
   docker-compose restart postgres
   ```

2. **Redis Connection Failed**
   ```bash
   # Check if Redis is running
   docker-compose ps redis
   
   # Check logs
   docker-compose logs redis
   
   # Restart the service
   docker-compose restart redis
   ```

3. **Celery Worker Not Processing Jobs**
   ```bash
   # Check worker status
   docker-compose logs worker
   
   # Restart worker
   docker-compose restart worker
   
   # Check task queue
   curl http://localhost:8000/api/v1/queue/stats
   ```

4. **API Server Not Responding**
   ```bash
   # Check API logs
   docker-compose logs api
   
   # Check if port 8000 is available
   lsof -i :8000
   
   # Restart API
   docker-compose restart api
   ```

### Debug Mode

To run in debug mode with more verbose logging:

```bash
# Set debug environment variables
export LOG_LEVEL=DEBUG
export SQL_ECHO=true

# Restart services
docker-compose down
docker-compose up -d
```

### Performance Testing

```bash
# Test with different input sizes
for size in 100 1000 10000; do
  curl -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d "{\"algorithm_name\": \"quick_sort\", \"input_size\": $size}"
done

# Monitor system resources
docker stats

# Check database performance
docker-compose exec postgres psql -U dprofiler -d dprofiler -c "SELECT COUNT(*) FROM jobs;"
```

## Continuous Integration

The project includes a basic test suite that can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Test dProfiler

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=.
```

## Security Testing

```bash
# Test API endpoints for common vulnerabilities
# (Use tools like OWASP ZAP or Burp Suite)

# Check for SQL injection
curl "http://localhost:8000/api/v1/jobs?algorithm_name='; DROP TABLE jobs; --"

# Test authentication (if implemented)
curl -H "Authorization: Bearer invalid-token" http://localhost:8000/api/v1/jobs
```

## Load Testing

```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Using wrk
wrk -t12 -c400 -d30s http://localhost:8000/health

# Using locust (if available)
locust -f tests/locustfile.py --host=http://localhost:8000
```

## Cleanup

To completely clean up the environment:

```bash
# Stop all services
docker-compose down

# Remove volumes (this will delete all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Clean up any remaining containers
docker system prune -f
```

## Next Steps

After successfully running and testing the application:

1. **Explore the API documentation** at http://localhost:8000/docs
2. **Create custom algorithms** and add them to the profiler
3. **Set up monitoring** with Prometheus and Grafana
4. **Configure logging** with ELK stack
5. **Implement authentication** and authorization
6. **Add more comprehensive tests**
7. **Set up CI/CD pipeline**
8. **Deploy to production**

For more information, refer to the main README.md file. 
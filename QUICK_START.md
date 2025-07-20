# dProfiler Quick Start Guide

## 🚀 Quick Commands

### Start Everything
```bash
make up          # Start all services with Docker Compose
make health      # Run comprehensive health checks
```

### Stop Everything
```bash
make down        # Stop all services
make clean       # Stop and clean up everything
```

### Development Workflow
```bash
make up          # Start services
make test        # Run tests
make logs        # View logs
make restart     # Restart services
```

## 🔍 Troubleshooting Commands

### Health Checks
```bash
make health-api    # Check API health
make health-db     # Check database health
make health-redis  # Check Redis health
make health-worker # Check worker health
```

### Debug Mode
```bash
make troubleshoot  # Run comprehensive troubleshooting
make debug         # Enable debug mode and show logs
```

### Service Management
```bash
make status        # Show service status
make logs          # Show all logs
make restart       # Restart all services
```

## 🧪 Testing Commands

### API Testing
```bash
make test-api          # Run API tests
make test-integration  # Run integration tests
make test-api-endpoints # Test all API endpoints
```

### Performance Testing
```bash
make benchmark         # Run performance benchmarks
make monitor           # Start real-time monitoring
```

## 🏗️ Deployment Commands

### Docker Compose (Recommended)
```bash
make build        # Build Docker images
make up           # Start services
make down         # Stop services
```

### Local Development
```bash
make local-setup  # Setup local environment
make local-test   # Test local setup
make local-health # Health checks for local
```

### Kubernetes
```bash
make k8s-deploy   # Deploy to Kubernetes
make k8s-clean    # Clean up Kubernetes
```

## 📊 Monitoring Commands

### Real-time Monitoring
```bash
make monitor      # Start system monitoring
make logs         # View service logs
```

### Health Status
```bash
make health       # All health checks
make status       # Service status
```

## 🧹 Cleanup Commands

### Docker Cleanup
```bash
make clean        # Clean containers and volumes
make down         # Stop services
```

### Kubernetes Cleanup
```bash
make k8s-clean    # Remove Kubernetes deployment
```

## 🔧 Common Workflows

### 1. First Time Setup
```bash
make up           # Start services
make health       # Verify everything works
make test         # Run tests
```

### 2. Development Session
```bash
make up           # Start services
make logs         # Monitor logs in background
# ... do development work ...
make test         # Run tests
make restart      # Restart if needed
```

### 3. Troubleshooting
```bash
make troubleshoot # Comprehensive diagnostics
make debug        # Enable debug mode
make logs         # Check logs
make health       # Verify health
```

### 4. Production Deployment
```bash
make k8s-deploy   # Deploy to Kubernetes
make monitor      # Monitor deployment
```

## 📝 API Quick Reference

### Health Check
```bash
curl http://localhost:8000/health
```

### Create Job
```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"algorithm_name": "quick_sort", "input_size": 1000}'
```

### Check Job Status
```bash
curl http://localhost:8000/api/v1/jobs/{job_id}
```

### List Algorithms
```bash
curl http://localhost:8000/api/v1/algorithms
```

### View Metrics
```bash
curl http://localhost:8000/metrics
```

## 🚨 Emergency Commands

### Force Stop Everything
```bash
docker compose down -v  # Stop and remove volumes
docker system prune -f  # Clean up Docker
```

### Reset Database
```bash
docker compose down -v
docker compose up -d
docker compose exec api python -c "from core.database import db_manager; db_manager.init_db()"
```

### Check Port Conflicts
```bash
lsof -i :8000 -i :5432 -i :6379
```

## 📚 Additional Resources

- **Full Documentation**: `README.md`
- **Architecture**: `ARCHITECTURE.md`
- **Testing Guide**: `TESTING.md`
- **Kubernetes**: `k8s/` directory

## 🆘 Need Help?

1. Run `make troubleshoot` for diagnostics
2. Check `make logs` for error messages
3. Verify `make health` for service status
4. Review `TESTING.md` for detailed troubleshooting 
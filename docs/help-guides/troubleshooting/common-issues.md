# Common Issues & Solutions

This guide covers the most common issues you might encounter when using dProfiler and provides step-by-step solutions.

## 🚨 **Quick Emergency Commands**

If your system is down, run these commands immediately:

```bash
# Comprehensive diagnostics
make troubleshoot

# Check system health
make health

# View logs
make logs

# Restart services
make restart
```

## 🔍 **Issue Categories**

- [Service Startup Issues](#service-startup-issues)
- [Health Check Failures](#health-check-failures)
- [Job Processing Issues](#job-processing-issues)
- [Performance Issues](#performance-issues)
- [Database Issues](#database-issues)
- [Network Issues](#network-issues)
- [Docker Issues](#docker-issues)
- [Kubernetes Issues](#kubernetes-issues)

## 🚀 **Service Startup Issues**

### **Problem: Services Won't Start**

**Symptoms**:
- `make up` fails
- Docker containers exit immediately
- Port conflicts

**Solutions**:

#### **1. Check Port Conflicts**
```bash
# Check if ports are in use
lsof -i :8000 -i :5432 -i :6379

# Kill processes using required ports
sudo kill -9 $(lsof -t -i:8000)
sudo kill -9 $(lsof -t -i:5432)
sudo kill -9 $(lsof -t -i:6379)
```

#### **2. Clean Docker Environment**
```bash
# Stop all containers
docker compose down

# Clean up Docker
docker system prune -f
docker volume prune -f

# Restart Docker Desktop (if on Mac/Windows)
# Then try again
make up
```

#### **3. Check Docker Daemon**
```bash
# Check if Docker is running
docker info

# If Docker is not running, start it:
# - Mac: Open Docker Desktop
# - Linux: sudo systemctl start docker
# - Windows: Start Docker Desktop
```

#### **4. Insufficient Resources**
```bash
# Check available memory and disk space
df -h
free -h

# Increase Docker resources in Docker Desktop settings
# - Memory: At least 4GB
# - CPU: At least 2 cores
# - Disk: At least 20GB free space
```

### **Problem: Database Initialization Fails**

**Symptoms**:
- Database connection errors
- Tables not created
- Permission denied errors

**Solutions**:

#### **1. Reset Database**
```bash
# Stop services
make down

# Remove database volume
docker volume rm dprofiler_postgres_data

# Start services (will recreate database)
make up
```

#### **2. Manual Database Initialization**
```bash
# Connect to database container
docker compose exec postgres psql -U dprofiler -d dprofiler

# Check if tables exist
\dt

# Exit and reinitialize
exit
docker compose exec api python -c "from core.database import db_manager; db_manager.init_db()"
```

## 🏥 **Health Check Failures**

### **Problem: API Health Check Fails**

**Symptoms**:
- `make health-api` returns error
- API not responding
- Connection refused errors

**Solutions**:

#### **1. Check API Container**
```bash
# Check if API container is running
docker compose ps api

# Check API logs
docker compose logs api

# Restart API
docker compose restart api
```

#### **2. Check API Configuration**
```bash
# Verify environment variables
docker compose exec api env | grep -E "(DATABASE|REDIS)"

# Check API configuration
docker compose exec api python -c "import os; print('DATABASE_URL:', os.getenv('DATABASE_URL'))"
```

#### **3. API Port Issues**
```bash
# Check if port 8000 is available
netstat -tulpn | grep :8000

# Change port in docker-compose.yml if needed
# ports:
#   - "8001:8000"  # Use port 8001 instead
```

### **Problem: Database Health Check Fails**

**Symptoms**:
- Database connection timeout
- Authentication errors
- Connection pool exhausted

**Solutions**:

#### **1. Check Database Connection**
```bash
# Test database connectivity
docker compose exec api python -c "from core.database import db_manager; print('Connection:', db_manager.check_connection())"

# Check database logs
docker compose logs postgres
```

#### **2. Database Configuration Issues**
```bash
# Verify database credentials
docker compose exec postgres psql -U dprofiler -d dprofiler -c "SELECT version();"

# Reset database password if needed
docker compose exec postgres psql -U postgres -c "ALTER USER dprofiler PASSWORD 'password';"
```

#### **3. Connection Pool Issues**
```bash
# Check connection pool settings
docker compose exec api python -c "from core.database import db_manager; print('Pool size:', db_manager.engine.pool.size())"

# Restart database
docker compose restart postgres
```

### **Problem: Redis Health Check Fails**

**Symptoms**:
- Redis connection refused
- Redis authentication errors
- Redis memory issues

**Solutions**:

#### **1. Check Redis Container**
```bash
# Check Redis status
docker compose ps redis

# Check Redis logs
docker compose logs redis

# Test Redis connectivity
docker compose exec redis redis-cli ping
```

#### **2. Redis Configuration Issues**
```bash
# Check Redis configuration
docker compose exec redis redis-cli config get maxmemory

# Clear Redis if needed
docker compose exec redis redis-cli flushall
```

#### **3. Redis Port Issues**
```bash
# Check Redis port
netstat -tulpn | grep :6379

# If using different port, update configuration
# In docker-compose.yml, change Redis port mapping
```

### **Problem: Worker Health Check Fails**

**Symptoms**:
- Workers not responding
- Celery connection errors
- Task queue issues

**Solutions**:

#### **1. Check Worker Status**
```bash
# Check if worker container is running
docker compose ps worker

# Check worker logs
docker compose logs worker

# Check Celery status
docker compose exec api celery -A workers.task_queue.celery_app inspect active
```

#### **2. Restart Workers**
```bash
# Restart worker container
docker compose restart worker

# Wait for worker to be ready
sleep 10

# Check worker health
make health-worker
```

#### **3. Celery Configuration Issues**
```bash
# Check Celery configuration
docker compose exec api celery -A workers.task_queue.celery_app inspect stats

# Clear Celery queue if needed
docker compose exec api celery -A workers.task_queue.celery_app purge
```

## ⚙️ **Job Processing Issues**

### **Problem: Jobs Not Processing**

**Symptoms**:
- Jobs stuck in "pending" status
- No workers processing jobs
- Job queue not moving

**Solutions**:

#### **1. Check Worker Status**
```bash
# Check if workers are active
docker compose exec api celery -A workers.task_queue.celery_app inspect active

# Check worker statistics
docker compose exec api celery -A workers.task_queue.celery_app inspect stats
```

#### **2. Check Job Queue**
```bash
# List pending jobs
curl -s http://localhost:8000/api/v1/jobs | jq '.jobs[] | select(.status == "pending")'

# Check queue length
docker compose exec api celery -A workers.task_queue.celery_app inspect active_queues
```

#### **3. Restart Workers**
```bash
# Restart worker container
docker compose restart worker

# Wait for worker to be ready
sleep 15

# Check if jobs start processing
curl -s http://localhost:8000/api/v1/jobs | jq '.jobs[] | select(.status == "running")'
```

### **Problem: Jobs Failing**

**Symptoms**:
- Jobs in "failed" status
- Error messages in job results
- Algorithm execution errors

**Solutions**:

#### **1. Check Job Error Details**
```bash
# Get failed job details
curl -s http://localhost:8000/api/v1/jobs/{job_id} | jq '.error_message'

# Check worker logs for errors
docker compose logs worker | grep -i error
```

#### **2. Check Algorithm Implementation**
```bash
# Verify algorithm exists
curl -s http://localhost:8000/api/v1/algorithms | jq '.[] | .name'

# Test algorithm directly
docker compose exec api python -c "from core.profiler import profile_algorithm; print(profile_algorithm('quick_sort', 100))"
```

#### **3. Check System Resources**
```bash
# Check available memory
docker stats --no-stream

# Check disk space
df -h

# Restart with more resources if needed
```

## 📊 **Performance Issues**

### **Problem: Slow Job Processing**

**Symptoms**:
- Jobs taking too long to complete
- High CPU/memory usage
- System becoming unresponsive

**Solutions**:

#### **1. Monitor System Resources**
```bash
# Check system metrics
docker stats --no-stream

# Check dProfiler metrics
curl -s http://localhost:8000/metrics | grep -E "(cpu|memory|disk)"

# Monitor in real-time
make monitor
```

#### **2. Optimize Worker Configuration**
```bash
# Check worker concurrency
docker compose exec api celery -A workers.task_queue.celery_app inspect stats | jq '.pool.size'

# Increase worker concurrency in docker-compose.yml
# command: celery -A workers.task_queue.celery_app worker --loglevel=info --concurrency=4
```

#### **3. Scale Workers**
```bash
# Scale workers (if using Kubernetes)
kubectl scale deployment dprofiler-worker --replicas=3 -n dprofiler

# Or add more worker containers
docker compose up -d --scale worker=3
```

### **Problem: High Memory Usage**

**Symptoms**:
- Out of memory errors
- System becoming slow
- Containers being killed

**Solutions**:

#### **1. Check Memory Usage**
```bash
# Check container memory usage
docker stats --no-stream

# Check system memory
free -h

# Check memory limits in docker-compose.yml
```

#### **2. Optimize Memory Settings**
```bash
# Add memory limits to docker-compose.yml
# services:
#   worker:
#     deploy:
#       resources:
#         limits:
#           memory: 1G
#         reservations:
#           memory: 512M
```

#### **3. Clean Up Resources**
```bash
# Clean up Docker
docker system prune -f

# Restart services
make restart
```

## 🗄️ **Database Issues**

### **Problem: Database Connection Errors**

**Symptoms**:
- Connection timeout errors
- Connection pool exhausted
- Database not responding

**Solutions**:

#### **1. Check Database Status**
```bash
# Check if database is running
docker compose ps postgres

# Check database logs
docker compose logs postgres

# Test database connection
docker compose exec postgres pg_isready -U dprofiler
```

#### **2. Optimize Database Settings**
```bash
# Check database configuration
docker compose exec postgres psql -U dprofiler -d dprofiler -c "SHOW max_connections;"

# Increase connection pool in application
# DATABASE_URL with connection pool settings
```

#### **3. Database Maintenance**
```bash
# Vacuum database
docker compose exec postgres psql -U dprofiler -d dprofiler -c "VACUUM;"

# Analyze database
docker compose exec postgres psql -U dprofiler -d dprofiler -c "ANALYZE;"
```

## 🌐 **Network Issues**

### **Problem: Service Communication Issues**

**Symptoms**:
- Services can't communicate
- Network timeouts
- DNS resolution issues

**Solutions**:

#### **1. Check Network Configuration**
```bash
# Check Docker network
docker network ls
docker network inspect dprofiler_default

# Check service connectivity
docker compose exec api ping postgres
docker compose exec api ping redis
```

#### **2. Fix Network Issues**
```bash
# Recreate network
docker compose down
docker network prune -f
docker compose up -d
```

#### **3. Check Firewall Settings**
```bash
# Check if ports are blocked
sudo ufw status

# Allow required ports
sudo ufw allow 8000
sudo ufw allow 5432
sudo ufw allow 6379
```

## 🐳 **Docker Issues**

### **Problem: Docker Compose Issues**

**Symptoms**:
- `docker compose` command not found
- Compose file errors
- Container build failures

**Solutions**:

#### **1. Install Docker Compose**
```bash
# Install Docker Compose
# Mac/Windows: Install Docker Desktop
# Linux: sudo apt-get install docker-compose-plugin

# Verify installation
docker compose version
```

#### **2. Fix Compose File Issues**
```bash
# Validate compose file
docker compose config

# Check for syntax errors
docker compose config --quiet
```

#### **3. Build Issues**
```bash
# Rebuild images
docker compose build --no-cache

# Check build logs
docker compose build --progress=plain
```

### **Problem: Container Build Failures**

**Symptoms**:
- Docker build errors
- Missing dependencies
- Permission issues

**Solutions**:

#### **1. Check Dockerfile**
```bash
# Validate Dockerfile
docker build --dry-run .

# Check for syntax errors
docker build --target syntax-check .
```

#### **2. Fix Dependencies**
```bash
# Update requirements.txt
pip freeze > requirements.txt

# Rebuild with updated dependencies
docker compose build --no-cache
```

#### **3. Permission Issues**
```bash
# Fix file permissions
chmod +x scripts/*.sh

# Check Docker context
docker build --progress=plain .
```

## ☸️ **Kubernetes Issues**

### **Problem: Kubernetes Deployment Issues**

**Symptoms**:
- Pods not starting
- Services not accessible
- Resource constraints

**Solutions**:

#### **1. Check Pod Status**
```bash
# Check pod status
kubectl get pods -n dprofiler

# Check pod logs
kubectl logs deployment/dprofiler-api -n dprofiler

# Check pod events
kubectl describe pod <pod-name> -n dprofiler
```

#### **2. Check Service Status**
```bash
# Check services
kubectl get services -n dprofiler

# Check endpoints
kubectl get endpoints -n dprofiler

# Test service connectivity
kubectl port-forward service/dprofiler-api-service 8000:80 -n dprofiler
```

#### **3. Resource Issues**
```bash
# Check resource usage
kubectl top pods -n dprofiler

# Check resource limits
kubectl describe deployment dprofiler-api -n dprofiler

# Scale resources if needed
kubectl scale deployment dprofiler-api --replicas=2 -n dprofiler
```

### **Problem: Kubernetes Networking Issues**

**Symptoms**:
- Services not accessible
- Ingress not working
- DNS resolution issues

**Solutions**:

#### **1. Check Network Policies**
```bash
# Check network policies
kubectl get networkpolicies -n dprofiler

# Check service mesh (if using Istio)
kubectl get virtualservices -n dprofiler
```

#### **2. Check Ingress**
```bash
# Check ingress status
kubectl get ingress -n dprofiler

# Check ingress controller
kubectl get pods -n ingress-nginx

# Test ingress
curl -H "Host: dprofiler.local" http://localhost
```

## 🔧 **Prevention & Best Practices**

### **Regular Maintenance**
```bash
# Daily health checks
make health

# Weekly cleanup
make clean

# Monthly performance review
make benchmark
```

### **Monitoring Setup**
```bash
# Set up monitoring
make monitor

# Configure alerts
# Set up Prometheus/Grafana for production
```

### **Backup Strategy**
```bash
# Backup database
docker compose exec postgres pg_dump -U dprofiler dprofiler > backup.sql

# Backup configuration
cp docker-compose.yml backup/
cp k8s/*.yaml backup/
```

## 📞 **Getting More Help**

### **Self-Service**
1. Run `make troubleshoot` for comprehensive diagnostics
2. Check this guide for your specific issue
3. Review logs with `make logs`

### **Community Support**
- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share experiences
- **Documentation**: Check the main [README.md](../../../README.md)

### **Emergency Support**
If your system is completely down:
1. Run `make troubleshoot` immediately
2. Check [Debug Guide](debug.md) for detailed diagnostics
3. Review [Health Checks](health-checks.md) for system status

---

**Remember**: Most issues can be resolved by running `make troubleshoot` and following the diagnostic output. This guide covers the most common scenarios, but the troubleshooting command will provide specific guidance for your situation. 
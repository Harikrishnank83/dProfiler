# Quick Start Guide

Get dProfiler up and running in 5 minutes! This guide will help you deploy dProfiler and run your first algorithm profiling job.

## ⚡ **5-Minute Setup**

### **Step 1: Clone and Navigate**
```bash
git clone <repository-url>
cd dProfiler
```

### **Step 2: Start Services**
```bash
make up
```

This command will:
- Start PostgreSQL database
- Start Redis message queue
- Start API server
- Start worker nodes
- Initialize the database
- Wait for all services to be ready

### **Step 3: Verify Health**
```bash
make health
```

You should see:
```
✅ API is healthy
✅ Database is healthy
✅ Redis is healthy
✅ Worker is healthy
✅ All health checks completed!
```

### **Step 4: Run Your First Job**
```bash
# Create a profiling job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"algorithm_name": "quick_sort", "input_size": 1000}'
```

### **Step 5: Check Results**
```bash
# Get the job ID from the response above, then:
curl http://localhost:8000/api/v1/jobs/{job_id}/results
```

## 🎯 **What Just Happened?**

1. **dProfiler Started**: All services are running and healthy
2. **Job Created**: A profiling job was submitted to the queue
3. **Worker Processed**: A worker picked up the job and executed the algorithm
4. **Results Stored**: Performance metrics were collected and stored
5. **Results Retrieved**: You can now analyze the performance data

## 📊 **Understanding Your Results**

The profiling results include:
- **Execution Time**: How long the algorithm took to run
- **Memory Usage**: How much memory was consumed
- **CPU Usage**: CPU utilization during execution
- **Input Size**: Size of the data processed
- **Algorithm**: Which algorithm was profiled

## 🚀 **Next Steps**

### **Try Different Algorithms**
```bash
# Test bubble sort
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"algorithm_name": "bubble_sort", "input_size": 500}'

# Test merge sort
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"algorithm_name": "merge_sort", "input_size": 2000}'
```

### **Compare Algorithms**
```bash
# Compare multiple algorithms
curl -X POST "http://localhost:8000/api/v1/compare?input_size=1000&iterations=3" \
  -H "Content-Type: application/json" \
  -d '{"algorithms": ["bubble_sort", "quick_sort", "merge_sort"]}'
```

### **Explore the API**
```bash
# List available algorithms
curl http://localhost:8000/api/v1/algorithms

# View system metrics
curl http://localhost:8000/metrics

# Check API documentation
open http://localhost:8000/docs
```

## 🛠️ **Useful Commands**

### **Service Management**
```bash
make status        # Check service status
make logs          # View logs
make restart       # Restart services
make down          # Stop services
```

### **Testing**
```bash
make test          # Run all tests
make test-api-endpoints  # Test API endpoints
make benchmark     # Run performance benchmarks
```

### **Troubleshooting**
```bash
make health        # Health checks
make troubleshoot  # Comprehensive diagnostics
make debug         # Enable debug mode
```

## 🔍 **Common Issues**

### **Services Won't Start**
```bash
# Check if ports are available
lsof -i :8000 -i :5432 -i :6379

# Restart Docker if needed
docker system prune -f
make up
```

### **Health Checks Fail**
```bash
# Run diagnostics
make troubleshoot

# Check logs
make logs
```

### **Jobs Not Processing**
```bash
# Check worker status
make health-worker

# Restart workers
make restart
```

## 📚 **What's Next?**

Now that you're up and running:

1. **Read [Basic Usage](usage/basic.md)** - Learn fundamental concepts
2. **Try [Real-World Examples](usage/examples.md)** - See practical applications
3. **Explore [Advanced Usage](usage/advanced.md)** - Master advanced features
4. **Check [API Reference](usage/api-reference.md)** - Complete API documentation

## 🆘 **Need Help?**

- **Quick Fix**: Run `make troubleshoot`
- **Health Check**: Run `make health`
- **View Logs**: Run `make logs`
- **Common Issues**: Check [Common Issues](troubleshooting/common-issues.md)

---

**Congratulations!** You've successfully deployed dProfiler and run your first algorithm profiling job. You're now ready to explore the full power of distributed algorithm profiling! 
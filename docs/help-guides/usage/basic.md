# Basic Usage Guide

This guide covers the fundamental concepts and basic operations for using dProfiler. You'll learn how to create jobs, monitor progress, and understand results.

## 🎯 **What is dProfiler?**

dProfiler is a distributed algorithm profiling tool that helps you:
- **Profile algorithms** - Measure performance characteristics
- **Compare algorithms** - Find the best algorithm for your use case
- **Monitor resources** - Track CPU, memory, and execution time
- **Scale processing** - Distribute work across multiple workers

## 📋 **Core Concepts**

### **Jobs**
A **job** represents a single algorithm profiling task. Each job includes:
- **Algorithm name** - Which algorithm to profile
- **Input size** - Size of data to process
- **Parameters** - Algorithm-specific configuration
- **Status** - Current state (pending, running, completed, failed)

### **Workers**
**Workers** are distributed processing nodes that:
- Pick up jobs from the queue
- Execute algorithms
- Collect performance metrics
- Store results

### **Results**
**Results** contain performance metrics:
- **Execution time** - How long the algorithm took
- **Memory usage** - Memory consumed during execution
- **CPU usage** - CPU utilization percentage
- **Input size** - Size of processed data

## 🚀 **Getting Started**

### **1. Check System Health**
```bash
# Verify all services are running
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

### **2. List Available Algorithms**
```bash
# See what algorithms you can profile
curl http://localhost:8000/api/v1/algorithms
```

Response:
```json
[
  {
    "name": "bubble_sort",
    "description": "Bubble sort algorithm",
    "category": "sorting",
    "parameters": {}
  },
  {
    "name": "quick_sort",
    "description": "Quick sort algorithm",
    "category": "sorting",
    "parameters": {}
  },
  {
    "name": "merge_sort",
    "description": "Merge sort algorithm",
    "category": "sorting",
    "parameters": {}
  }
]
```

### **3. Create Your First Job**
```bash
# Profile a quick sort algorithm
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm_name": "quick_sort",
    "input_size": 1000
  }'
```

Response:
```json
{
  "id": 1,
  "job_id": "abc123-def456-ghi789",
  "algorithm_name": "quick_sort",
  "input_size": 1000,
  "parameters": null,
  "status": "pending",
  "priority": 0,
  "created_at": "2024-07-20T10:30:00Z",
  "updated_at": null,
  "started_at": null,
  "completed_at": null,
  "worker_id": null,
  "error_message": null
}
```

### **4. Check Job Status**
```bash
# Replace {job_id} with the actual job ID from step 3
curl http://localhost:8000/api/v1/jobs/{job_id}
```

Response:
```json
{
  "id": 1,
  "job_id": "abc123-def456-ghi789",
  "algorithm_name": "quick_sort",
  "input_size": 1000,
  "parameters": null,
  "status": "completed",
  "priority": 0,
  "created_at": "2024-07-20T10:30:00Z",
  "updated_at": "2024-07-20T10:30:05Z",
  "started_at": "2024-07-20T10:30:01Z",
  "completed_at": "2024-07-20T10:30:05Z",
  "worker_id": "worker-1",
  "error_message": null
}
```

### **5. Get Job Results**
```bash
# Get the profiling results
curl http://localhost:8000/api/v1/jobs/{job_id}/results
```

Response:
```json
{
  "id": 1,
  "job_id": 1,
  "algorithm_name": "quick_sort",
  "input_size": 1000,
  "execution_time": 0.012,
  "memory_usage": 4.2,
  "cpu_usage": 25.7,
  "iterations": 1,
  "parameters": null,
  "result_metadata": {
    "pivot_strategy": "median",
    "comparisons": 9876,
    "swaps": 5432
  },
  "timestamp": "2024-07-20T10:30:05Z"
}
```

## 📊 **Understanding Results**

### **Execution Time**
- **Unit**: Seconds
- **Meaning**: How long the algorithm took to complete
- **Example**: `0.012` means 12 milliseconds

### **Memory Usage**
- **Unit**: Megabytes (MB)
- **Meaning**: Peak memory consumed during execution
- **Example**: `4.2` means 4.2 MB of RAM used

### **CPU Usage**
- **Unit**: Percentage (%)
- **Meaning**: Average CPU utilization during execution
- **Example**: `25.7` means 25.7% CPU usage

### **Result Metadata**
- **Algorithm-specific data** - Additional metrics for the algorithm
- **Example**: For quick sort, shows pivot strategy, comparisons, swaps

## 🔄 **Job Lifecycle**

### **Job States**
1. **pending** - Job is queued, waiting for a worker
2. **running** - Worker is executing the algorithm
3. **completed** - Job finished successfully with results
4. **failed** - Job encountered an error

### **Monitoring Job Progress**
```bash
# Watch job status in real-time
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/jobs/{job_id} | jq -r '.status')
  echo "$(date): Job status is $STATUS"
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  
  sleep 2
done
```

## 📈 **Comparing Algorithms**

### **Compare Multiple Algorithms**
```bash
# Compare three sorting algorithms
curl -X POST "http://localhost:8000/api/v1/compare?input_size=5000&iterations=3" \
  -H "Content-Type: application/json" \
  -d '{
    "algorithms": ["bubble_sort", "quick_sort", "merge_sort"]
  }'
```

Response:
```json
{
  "comparison_id": "comp_123",
  "results": [
    {
      "algorithm": "bubble_sort",
      "avg_execution_time": 2.45,
      "avg_memory_usage": 15.2,
      "avg_cpu_usage": 85.3,
      "iterations": 3
    },
    {
      "algorithm": "quick_sort",
      "avg_execution_time": 0.12,
      "avg_memory_usage": 8.1,
      "avg_cpu_usage": 45.2,
      "iterations": 3
    },
    {
      "algorithm": "merge_sort",
      "avg_execution_time": 0.18,
      "avg_memory_usage": 12.5,
      "avg_cpu_usage": 52.1,
      "iterations": 3
    }
  ]
}
```

### **Understanding Comparison Results**
- **Average execution time** - Mean time across all iterations
- **Average memory usage** - Mean memory consumption
- **Average CPU usage** - Mean CPU utilization
- **Iterations** - Number of times each algorithm was tested

## 📋 **Managing Jobs**

### **List All Jobs**
```bash
# Get all jobs with pagination
curl "http://localhost:8000/api/v1/jobs?page=1&size=10"
```

### **Filter Jobs by Status**
```bash
# Get only completed jobs
curl "http://localhost:8000/api/v1/jobs?status=completed"
```

### **Delete a Job**
```bash
# Remove a job (if not needed)
curl -X DELETE http://localhost:8000/api/v1/jobs/{job_id}
```

## 🔍 **Monitoring System**

### **Check System Health**
```bash
# Comprehensive health check
curl http://localhost:8000/health
```

### **View System Metrics**
```bash
# Prometheus format metrics
curl http://localhost:8000/metrics
```

### **List Worker Nodes**
```bash
# See active workers
curl http://localhost:8000/api/v1/workers
```

## 🛠️ **Common Operations**

### **Create Multiple Jobs**
```bash
# Create jobs for different input sizes
for size in 100 1000 10000; do
  curl -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d "{\"algorithm_name\": \"quick_sort\", \"input_size\": $size}"
done
```

### **Wait for Job Completion**
```bash
# Wait for a specific job to complete
JOB_ID="your-job-id"
while true; do
  STATUS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID | jq -r '.status')
  if [ "$STATUS" = "completed" ]; then
    echo "Job completed!"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Job failed!"
    break
  fi
  sleep 2
done
```

### **Get Job Results with Error Handling**
```bash
# Get results with proper error handling
JOB_ID="your-job-id"
RESPONSE=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/results)

if [ $? -eq 0 ]; then
  echo "Results:"
  echo "$RESPONSE" | jq '.'
else
  echo "Failed to get results"
fi
```

## 📚 **Best Practices**

### **1. Choose Appropriate Input Sizes**
- **Small (100-1000)**: Quick testing and validation
- **Medium (1000-10000)**: Performance comparison
- **Large (10000+)**: Stress testing and scalability analysis

### **2. Use Multiple Iterations**
- Run algorithms multiple times for accurate averages
- Account for system variability
- Use the comparison endpoint for statistical significance

### **3. Monitor System Resources**
- Check system health before running large jobs
- Monitor resource usage during execution
- Use appropriate input sizes for your system

### **4. Clean Up Old Jobs**
- Delete completed jobs you no longer need
- Keep the job history manageable
- Archive important results

## 🚨 **Troubleshooting**

### **Job Stuck in Pending**
```bash
# Check worker status
make health-worker

# Restart workers if needed
make restart
```

### **Job Failed**
```bash
# Check error details
curl http://localhost:8000/api/v1/jobs/{job_id} | jq '.error_message'

# Check worker logs
make logs
```

### **System Not Responding**
```bash
# Run comprehensive diagnostics
make troubleshoot

# Check system health
make health
```

## 📖 **Next Steps**

Now that you understand the basics:

1. **Try [Advanced Usage](advanced.md)** - Learn advanced features
2. **Explore [Real-World Examples](examples.md)** - See practical applications
3. **Check [API Reference](api-reference.md)** - Complete API documentation
4. **Read [Troubleshooting](troubleshooting/common-issues.md)** - Solve common problems

## 🆘 **Need Help?**

- **Quick Fix**: Run `make troubleshoot`
- **Health Check**: Run `make health`
- **View Logs**: Run `make logs`
- **Common Issues**: Check [Common Issues](troubleshooting/common-issues.md)

---

**Congratulations!** You've mastered the basics of dProfiler. You can now create jobs, monitor progress, and analyze results. Ready to explore more advanced features? 
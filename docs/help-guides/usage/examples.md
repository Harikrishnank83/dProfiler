# Real-World Examples

This guide provides practical examples of how to use dProfiler in real-world scenarios. Each example includes complete code and expected outputs.

## 🎯 **Example Categories**

- [Algorithm Performance Comparison](#algorithm-performance-comparison)
- [Scalability Testing](#scalability-testing)
- [Resource Monitoring](#resource-monitoring)
- [Load Testing](#load-testing)
- [Algorithm Optimization](#algorithm-optimization)
- [Worker Scaling](#worker-scaling)
- [Performance Analysis](#performance-analysis)
- [Integration Examples](#integration-examples)

## 🔄 **Algorithm Performance Comparison**

### **Compare Multiple Sorting Algorithms**

**Scenario**: You want to compare the performance of different sorting algorithms to choose the best one for your application.

```bash
# Compare bubble sort vs quick sort vs merge sort
curl -X POST "http://localhost:8000/api/v1/compare?input_size=5000&iterations=3" \
  -H "Content-Type: application/json" \
  -d '{
    "algorithms": ["bubble_sort", "quick_sort", "merge_sort"]
  }'
```

**Expected Output**:
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

**Analysis**: Quick sort is the fastest, but merge sort uses more memory. Choose based on your priorities.

## 📈 **Scalability Testing**

### **Test Algorithm Performance Across Different Input Sizes**

**Scenario**: You need to understand how your algorithm scales with data size.

```bash
#!/bin/bash
# scalability_test.sh

echo "=== Algorithm Scalability Test ==="
echo "Testing quick_sort across different input sizes"
echo ""

# Test different input sizes
for size in 100 1000 10000 100000; do
  echo "Testing input size: $size"
  
  # Create job
  JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d "{\"algorithm_name\": \"quick_sort\", \"input_size\": $size}")
  
  JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id')
  echo "Job ID: $JOB_ID"
  
  # Wait for completion
  while true; do
    STATUS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID | jq -r '.status')
    if [ "$STATUS" = "completed" ]; then
      break
    elif [ "$STATUS" = "failed" ]; then
      echo "Job failed!"
      break
    fi
    sleep 2
  done
  
  # Get results
  RESULTS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/results | jq '.')
  echo "Results:"
  echo "$RESULTS" | jq '{execution_time, memory_usage, cpu_usage}'
  echo ""
done
```

**Expected Output**:
```
=== Algorithm Scalability Test ===
Testing quick_sort across different input sizes

Testing input size: 100
Job ID: job_123
Results:
{
  "execution_time": 0.001,
  "memory_usage": 2.1,
  "cpu_usage": 15.3
}

Testing input size: 1000
Job ID: job_124
Results:
{
  "execution_time": 0.012,
  "memory_usage": 4.2,
  "cpu_usage": 25.7
}

Testing input size: 10000
Job ID: job_125
Results:
{
  "execution_time": 0.089,
  "memory_usage": 8.5,
  "cpu_usage": 42.1
}

Testing input size: 100000
Job ID: job_126
Results:
{
  "execution_time": 1.234,
  "memory_usage": 15.8,
  "cpu_usage": 78.9
}
```

## 📊 **Resource Monitoring**

### **Monitor System Resources During Algorithm Execution**

**Scenario**: You want to monitor system performance while algorithms are running.

```bash
#!/bin/bash
# resource_monitor.sh

# Start a resource-intensive job
echo "Starting resource-intensive job..."
JOB_ID=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"algorithm_name": "bubble_sort", "input_size": 50000}' | jq -r '.job_id')

echo "Job ID: $JOB_ID"
echo "Monitoring job progress and system metrics..."
echo ""

# Monitor job progress and system metrics
while true; do
  echo "=== $(date) ==="
  
  # Get job status
  JOB_STATUS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID)
  STATUS=$(echo "$JOB_STATUS" | jq -r '.status')
  
  echo "Job Status: $STATUS"
  
  if [ "$STATUS" = "completed" ]; then
    echo "Job completed!"
    echo "Final Results:"
    curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/results | jq '{execution_time, memory_usage, cpu_usage}'
    break
  elif [ "$STATUS" = "failed" ]; then
    echo "Job failed!"
    break
  fi
  
  # Show current job metrics if available
  if [ "$STATUS" = "running" ]; then
    echo "Current Metrics:"
    echo "$JOB_STATUS" | jq '{execution_time, memory_usage, cpu_usage}' 2>/dev/null || echo "Metrics not available yet"
  fi
  
  # Show system metrics
  echo "System Metrics:"
  curl -s http://localhost:8000/metrics | grep -E "(cpu|memory|disk)" | head -3
  
  echo "---"
  sleep 5
done
```

## ⚡ **Load Testing**

### **Simulate High Load with Multiple Concurrent Jobs**

**Scenario**: You want to test how dProfiler performs under high load.

```bash
#!/bin/bash
# load_test.sh

echo "=== Load Testing dProfiler ==="
echo "Creating 10 concurrent jobs..."
echo ""

# Create 10 concurrent jobs
for i in {1..10}; do
  echo "Creating job $i/10..."
  curl -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d "{
      \"algorithm_name\": \"merge_sort\",
      \"input_size\": 10000,
      \"priority\": $((RANDOM % 3))
    }" &
done

# Wait for all jobs to be submitted
wait
echo "All jobs submitted!"
echo ""

# Monitor system performance under load
echo "Monitoring system performance..."
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
  echo "=== $(date) ==="
  
  # Get job statistics
  JOBS_RESPONSE=$(curl -s http://localhost:8000/api/v1/jobs)
  
  # Count jobs by status
  PENDING=$(echo "$JOBS_RESPONSE" | jq '.jobs[] | select(.status == "pending") | .job_id' | wc -l)
  RUNNING=$(echo "$JOBS_RESPONSE" | jq '.jobs[] | select(.status == "running") | .job_id' | wc -l)
  COMPLETED=$(echo "$JOBS_RESPONSE" | jq '.jobs[] | select(.status == "completed") | .job_id' | wc -l)
  FAILED=$(echo "$JOBS_RESPONSE" | jq '.jobs[] | select(.status == "failed") | .job_id' | wc -l)
  
  echo "Job Status:"
  echo "  Pending: $PENDING"
  echo "  Running: $RUNNING"
  echo "  Completed: $COMPLETED"
  echo "  Failed: $FAILED"
  
  # Show system metrics
  echo "System Metrics:"
  curl -s http://localhost:8000/metrics | grep -E "(http_requests_total|job_completion_rate)" | tail -3
  
  echo "---"
  sleep 5
done
```

## 🔧 **Algorithm Optimization**

### **Test Different Algorithm Parameters**

**Scenario**: You want to optimize algorithm performance by testing different parameters.

```bash
#!/bin/bash
# optimization_test.sh

echo "=== Algorithm Optimization Test ==="
echo "Testing quick_sort with different pivot strategies"
echo ""

# Test different pivot strategies
for pivot in "first" "last" "median" "random"; do
  echo "Testing pivot strategy: $pivot"
  
  # Create job with specific parameters
  JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d "{
      \"algorithm_name\": \"quick_sort\",
      \"input_size\": 10000,
      \"parameters\": {\"pivot_strategy\": \"$pivot\"}
    }")
  
  JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id')
  echo "Job ID: $JOB_ID"
  
  # Wait for completion
  while true; do
    STATUS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID | jq -r '.status')
    if [ "$STATUS" = "completed" ]; then
      break
    elif [ "$STATUS" = "failed" ]; then
      echo "Job failed!"
      break
    fi
    sleep 2
  done
  
  # Get results
  RESULTS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/results | jq '.')
  echo "Results:"
  echo "$RESULTS" | jq '{execution_time, memory_usage, cpu_usage}'
  echo ""
done
```

## 🚀 **Worker Scaling**

### **Test Distributed Processing Capabilities**

**Scenario**: You want to test how dProfiler scales with multiple workers.

```bash
#!/bin/bash
# worker_scaling_test.sh

echo "=== Worker Scaling Test ==="

# Scale workers (if using Kubernetes)
echo "Scaling workers to 5 replicas..."
kubectl scale deployment dprofiler-worker --replicas=5 -n dprofiler

# Wait for workers to be ready
echo "Waiting for workers to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/dprofiler-worker -n dprofiler

echo "Creating 20 jobs to test worker distribution..."
echo ""

# Create jobs that will be distributed across workers
for i in {1..20}; do
  echo "Creating job $i/20..."
  curl -X POST http://localhost:8000/api/v1/jobs \
    -H "Content-Type: application/json" \
    -d "{
      \"algorithm_name\": \"quick_sort\",
      \"input_size\": 5000
    }" &
done

wait
echo "All jobs submitted!"
echo ""

# Monitor worker distribution
echo "Monitoring worker distribution..."
while true; do
  echo "=== $(date) ==="
  
  # Get worker status
  WORKERS=$(curl -s http://localhost:8000/api/v1/workers)
  echo "Workers:"
  echo "$WORKERS" | jq -r '.[] | "\(.worker_id): \(.status) - \(.active_jobs) active jobs"'
  
  # Get job statistics
  JOBS_RESPONSE=$(curl -s http://localhost:8000/api/v1/jobs)
  COMPLETED=$(echo "$JOBS_RESPONSE" | jq '.jobs[] | select(.status == "completed") | .job_id' | wc -l)
  TOTAL=$(echo "$JOBS_RESPONSE" | jq '.jobs | length')
  
  echo "Jobs: $COMPLETED/$TOTAL completed"
  
  if [ "$COMPLETED" -eq "$TOTAL" ]; then
    echo "All jobs completed!"
    break
  fi
  
  echo "---"
  sleep 5
done
```

## 📊 **Performance Analysis**

### **Generate Comprehensive Performance Reports**

**Scenario**: You need detailed performance analysis for decision making.

```bash
#!/bin/bash
# performance_analysis.sh

echo "=== Algorithm Performance Analysis ==="
echo "Date: $(date)"
echo ""

# Test all algorithms with different input sizes
algorithms=("bubble_sort" "quick_sort" "merge_sort")
sizes=(100 1000 10000)

# Create results file
RESULTS_FILE="performance_analysis_$(date +%Y%m%d_%H%M%S).json"
echo "[]" > "$RESULTS_FILE"

for algo in "${algorithms[@]}"; do
  echo "=== Testing $algo ==="
  
  for size in "${sizes[@]}"; do
    echo "Input size: $size"
    
    # Create job
    JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
      -H "Content-Type: application/json" \
      -d "{\"algorithm_name\": \"$algo\", \"input_size\": $size}")
    
    JOB_ID=$(echo "$JOB_RESPONSE" | jq -r '.job_id')
    
    # Wait for completion
    while true; do
      STATUS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID | jq -r '.status')
      if [ "$STATUS" = "completed" ]; then
        break
      elif [ "$STATUS" = "failed" ]; then
        echo "Job failed!"
        break
      fi
      sleep 2
    done
    
    # Get results
    RESULTS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/results | jq '.')
    
    # Add to results file
    jq --arg algo "$algo" --arg size "$size" --argjson results "$RESULTS" \
      '. += [{"algorithm": $algo, "input_size": ($size | tonumber), "results": $results}]' \
      "$RESULTS_FILE" > temp.json && mv temp.json "$RESULTS_FILE"
    
    echo "Results:"
    echo "$RESULTS" | jq '{execution_time, memory_usage, cpu_usage}'
    echo ""
  done
done

echo "Analysis complete! Results saved to: $RESULTS_FILE"
echo ""
echo "Summary:"
jq -r 'group_by(.algorithm) | .[] | "Algorithm: \(.[0].algorithm)" + "\n" + (.[] | "  Size \(.input_size): \(.results.execution_time)s (\(.results.memory_usage)MB)")' "$RESULTS_FILE"
```

## 🔗 **Integration Examples**

### **Python Integration**

```python
import requests
import json
import time
from typing import List, Dict, Any

class dProfilerClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def profile_algorithm(self, algorithm_name: str, input_size: int, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Profile an algorithm and return results"""
        payload = {
            "algorithm_name": algorithm_name,
            "input_size": input_size
        }
        if parameters:
            payload["parameters"] = parameters
            
        response = requests.post(f"{self.base_url}/api/v1/jobs", json=payload)
        response.raise_for_status()
        job_id = response.json()["job_id"]
        
        # Wait for completion
        while True:
            status_response = requests.get(f"{self.base_url}/api/v1/jobs/{job_id}")
            status_response.raise_for_status()
            status = status_response.json()["status"]
            
            if status == "completed":
                break
            elif status == "failed":
                raise Exception(f"Job {job_id} failed")
            
            time.sleep(2)
        
        # Get results
        results_response = requests.get(f"{self.base_url}/api/v1/jobs/{job_id}/results")
        results_response.raise_for_status()
        return results_response.json()
    
    def compare_algorithms(self, algorithms: List[str], input_size: int, iterations: int = 3) -> Dict[str, Any]:
        """Compare multiple algorithms"""
        params = {"input_size": input_size, "iterations": iterations}
        response = requests.post(
            f"{self.base_url}/api/v1/compare",
            params=params,
            json={"algorithms": algorithms}
        )
        response.raise_for_status()
        return response.json()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

# Usage examples
def main():
    client = dProfilerClient()
    
    # Check system health
    health = client.get_system_health()
    print(f"System Status: {health['status']}")
    
    # Profile a single algorithm
    print("\nProfiling quick_sort...")
    results = client.profile_algorithm("quick_sort", 10000)
    print(f"Execution time: {results['execution_time']}s")
    print(f"Memory usage: {results['memory_usage']}MB")
    print(f"CPU usage: {results['cpu_usage']}%")
    
    # Compare algorithms
    print("\nComparing algorithms...")
    comparison = client.compare_algorithms(
        ["bubble_sort", "quick_sort", "merge_sort"], 
        5000
    )
    print("Comparison Results:")
    for result in comparison["results"]:
        print(f"  {result['algorithm']}: {result['avg_execution_time']}s avg")

if __name__ == "__main__":
    main()
```

### **Shell Script Integration**

```bash
#!/bin/bash
# algorithm_benchmark.sh

# Usage: ./algorithm_benchmark.sh <algorithm> <input_size> [iterations]

ALGORITHM=$1
INPUT_SIZE=$2
ITERATIONS=${3:-5}

if [ -z "$ALGORITHM" ] || [ -z "$INPUT_SIZE" ]; then
    echo "Usage: $0 <algorithm> <input_size> [iterations]"
    echo "Example: $0 quick_sort 10000 10"
    exit 1
fi

echo "Benchmarking $ALGORITHM with input size $INPUT_SIZE ($ITERATIONS iterations)"
echo ""

# Create multiple jobs for averaging
for i in $(seq 1 $ITERATIONS); do
    echo "Creating job $i/$ITERATIONS..."
    JOB_ID=$(curl -s -X POST http://localhost:8000/api/v1/jobs \
        -H "Content-Type: application/json" \
        -d "{\"algorithm_name\": \"$ALGORITHM\", \"input_size\": $INPUT_SIZE}" | \
        jq -r '.job_id')
    
    # Wait for completion
    while true; do
        STATUS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID | jq -r '.status')
        if [ "$STATUS" = "completed" ]; then
            break
        fi
        sleep 1
    done
    
    # Get results
    RESULTS=$(curl -s http://localhost:8000/api/v1/jobs/$JOB_ID/results)
    echo "$RESULTS" | jq -r '.execution_time'
done | awk '{sum+=$1; count++} END {print "Average execution time:", sum/count, "seconds"}'
```

## 📈 **Real-Time Dashboard**

### **Create a Simple Monitoring Dashboard**

```bash
#!/bin/bash
# dashboard.sh

# Create a simple monitoring dashboard
while true; do
    clear
    echo "=== dProfiler Dashboard ==="
    echo "Time: $(date)"
    echo ""
    
    # System health
    echo "System Health:"
    HEALTH=$(curl -s http://localhost:8000/health)
    echo "$HEALTH" | jq -r '.status'
    echo ""
    
    # Job statistics
    echo "Job Statistics:"
    JOBS=$(curl -s http://localhost:8000/api/v1/jobs)
    echo "$JOBS" | jq -r '.jobs | group_by(.status) | map({status: .[0].status, count: length})[] | "\(.status): \(.count)"'
    echo ""
    
    # Worker status
    echo "Worker Status:"
    WORKERS=$(curl -s http://localhost:8000/api/v1/workers)
    echo "$WORKERS" | jq -r '.[] | "\(.worker_id): \(.status)"'
    echo ""
    
    # Recent metrics
    echo "Recent Metrics:"
    curl -s http://localhost:8000/metrics | grep -E "(http_requests_total|job_completion_rate)" | tail -5
    echo ""
    
    sleep 10
done
```

## 🎯 **Key Testing Areas**

1. **Performance Testing**: Compare algorithms across different input sizes
2. **Load Testing**: Test system behavior under high load
3. **Scalability Testing**: Test with multiple workers
4. **Reliability Testing**: Test error handling and recovery
5. **Integration Testing**: Test with real applications
6. **Monitoring Testing**: Verify metrics and health checks

## 📚 **Next Steps**

After trying these examples:

1. **Customize**: Adapt examples to your specific use cases
2. **Extend**: Add your own algorithms and parameters
3. **Automate**: Create scripts for regular performance testing
4. **Monitor**: Set up continuous monitoring and alerting
5. **Optimize**: Use results to optimize your algorithms

---

These examples demonstrate the full power of dProfiler for real-world algorithm profiling and performance analysis. Use them as starting points and customize them for your specific needs! 
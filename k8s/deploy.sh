#!/bin/bash

# dProfiler Kubernetes Deployment Script

set -e

echo "🚀 Deploying dProfiler to Kubernetes..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Check if namespace exists, create if not
if ! kubectl get namespace dprofiler &> /dev/null; then
    echo "📦 Creating dprofiler namespace..."
    kubectl apply -f namespace.yaml
fi

# Set context to dprofiler namespace
kubectl config set-context --current --namespace=dprofiler

echo "📋 Applying Kubernetes manifests..."

# Apply all configurations
kubectl apply -f configmap.yaml
kubectl apply -f postgres.yaml
kubectl apply -f redis.yaml
kubectl apply -f api.yaml
kubectl apply -f worker.yaml

echo "⏳ Waiting for deployments to be ready..."

# Wait for deployments to be ready
kubectl wait --for=condition=available --timeout=300s deployment/postgres
kubectl wait --for=condition=available --timeout=300s deployment/redis
kubectl wait --for=condition=available --timeout=300s deployment/dprofiler-api
kubectl wait --for=condition=available --timeout=300s deployment/dprofiler-worker

echo "🗄️ Initializing database..."

# Initialize database
kubectl exec deployment/dprofiler-api -- python -c "from core.database import db_manager; db_manager.init_db(); print('Database initialized successfully')"

echo "✅ Deployment completed successfully!"

# Get service information
echo ""
echo "📊 Service Information:"
echo "========================"

# Get LoadBalancer IP/URL
API_SERVICE=$(kubectl get service dprofiler-api-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
if [ -z "$API_SERVICE" ]; then
    API_SERVICE=$(kubectl get service dprofiler-api-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
fi

if [ -n "$API_SERVICE" ]; then
    echo "🌐 API Service: http://$API_SERVICE"
else
    echo "🌐 API Service: Use port-forward to access locally"
    echo "   kubectl port-forward service/dprofiler-api-service 8000:80"
fi

echo "📊 API Documentation: http://$API_SERVICE/docs"
echo "🏥 Health Check: http://$API_SERVICE/health"
echo "📈 Metrics: http://$API_SERVICE/metrics"

echo ""
echo "🔍 Useful Commands:"
echo "==================="
echo "kubectl get pods -n dprofiler"
echo "kubectl logs -f deployment/dprofiler-api -n dprofiler"
echo "kubectl logs -f deployment/dprofiler-worker -n dprofiler"
echo "kubectl scale deployment dprofiler-worker --replicas=5 -n dprofiler"
echo "kubectl delete namespace dprofiler  # To clean up everything"

echo ""
echo "🎉 dProfiler is now running in Kubernetes!" 
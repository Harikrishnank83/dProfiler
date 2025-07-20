# dProfiler Makefile
# Comprehensive deployment, testing, and health check commands

.PHONY: help build up down restart logs status health test clean docker-build docker-push k8s-deploy k8s-clean local-setup local-test local-health

# Default target
help:
	@echo "dProfiler - Distributed Algorithm Profiling Tool"
	@echo ""
	@echo "Available commands:"
	@echo "  make help          - Show this help message"
	@echo ""
	@echo "Docker Compose Commands:"
	@echo "  make build         - Build Docker images"
	@echo "  make up            - Start all services"
	@echo "  make down          - Stop all services"
	@echo "  make restart       - Restart all services"
	@echo "  make logs          - Show logs from all services"
	@echo "  make status        - Show service status"
	@echo ""
	@echo "Health Check Commands:"
	@echo "  make health        - Run comprehensive health checks"
	@echo "  make health-api    - Check API health"
	@echo "  make health-db     - Check database health"
	@echo "  make health-redis  - Check Redis health"
	@echo "  make health-worker - Check worker health"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test          - Run all tests"
	@echo "  make test-api      - Run API tests"
	@echo "  make test-integration - Run integration tests"
	@echo ""
	@echo "Local Development:"
	@echo "  make local-setup   - Setup local development environment"
	@echo "  make local-test    - Test local setup"
	@echo "  make local-health  - Health checks for local setup"
	@echo ""
	@echo "Kubernetes Commands:"
	@echo "  make k8s-deploy    - Deploy to Kubernetes"
	@echo "  make k8s-clean     - Clean up Kubernetes deployment"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean         - Clean up containers and volumes"
	@echo "  make docker-build  - Build Docker images"
	@echo "  make docker-push   - Push Docker images to registry"

# Docker Compose Commands
build:
	@echo "🔨 Building Docker images..."
	docker compose build

up:
	@echo "🚀 Starting dProfiler services..."
	docker compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@echo "🗄️ Initializing database..."
	docker compose exec -T api python -c "from core.database import db_manager; db_manager.init_db(); print('Database initialized successfully')"
	@echo "✅ Services started successfully!"

down:
	@echo "🛑 Stopping dProfiler services..."
	docker compose down

restart:
	@echo "🔄 Restarting dProfiler services..."
	docker compose restart

logs:
	@echo "📋 Showing logs from all services..."
	docker compose logs -f

status:
	@echo "📊 Service Status:"
	docker compose ps

# Health Check Commands
health: health-api health-db health-redis health-worker
	@echo "✅ All health checks completed!"

health-api:
	@echo "🏥 Checking API health..."
	@if curl -f -s http://localhost:8000/health > /dev/null; then \
		echo "✅ API is healthy"; \
	else \
		echo "❌ API health check failed"; \
		exit 1; \
	fi

health-db:
	@echo "🗄️ Checking database health..."
	@if docker compose exec -T api python -c "from core.database import db_manager; print('Database connection:', 'OK' if db_manager.check_connection() else 'FAILED')" | grep -q "OK"; then \
		echo "✅ Database is healthy"; \
	else \
		echo "❌ Database health check failed"; \
		exit 1; \
	fi

health-redis:
	@echo "🔴 Checking Redis health..."
	@if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then \
		echo "✅ Redis is healthy"; \
	else \
		echo "❌ Redis health check failed"; \
		exit 1; \
	fi

health-worker:
	@echo "⚙️ Checking worker health..."
	@if docker compose exec -T api celery -A workers.task_queue.celery_app inspect active > /dev/null 2>&1; then \
		echo "✅ Worker is healthy"; \
	else \
		echo "❌ Worker health check failed"; \
		exit 1; \
	fi

# Testing Commands
test: test-api test-integration
	@echo "✅ All tests completed!"

test-api:
	@echo "🧪 Running API tests..."
	pytest tests/test_api.py -v

test-integration:
	@echo "🔗 Running integration tests..."
	@echo "Creating test job..."
	@JOB_ID=$$(curl -s -X POST http://localhost:8000/api/v1/jobs \
		-H "Content-Type: application/json" \
		-d '{"algorithm_name": "bubble_sort", "input_size": 100}' | jq -r '.job_id'); \
	echo "Job created with ID: $$JOB_ID"; \
	echo "Waiting for job completion..."; \
	for i in {1..30}; do \
		STATUS=$$(curl -s http://localhost:8000/api/v1/jobs/$$JOB_ID | jq -r '.status'); \
		if [ "$$STATUS" = "completed" ]; then \
			echo "✅ Job completed successfully"; \
			break; \
		elif [ "$$STATUS" = "failed" ]; then \
			echo "❌ Job failed"; \
			exit 1; \
		fi; \
		sleep 2; \
	done; \
	echo "Getting job results..."; \
	curl -s http://localhost:8000/api/v1/jobs/$$JOB_ID/results | jq '.'

# Local Development Commands
local-setup:
	@echo "🔧 Setting up local development environment..."
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Activating virtual environment..."
	@echo "source venv/bin/activate  # On Windows: venv\\Scripts\\activate"
	@echo "Installing dependencies..."
	pip install -r requirements.txt
	@echo "Starting infrastructure services..."
	docker run -d --name dprofiler-postgres \
		-e POSTGRES_DB=dprofiler \
		-e POSTGRES_USER=dprofiler \
		-e POSTGRES_PASSWORD=password \
		-p 5432:5432 postgres:15
	docker run -d --name dprofiler-redis \
		-p 6379:6379 redis:7-alpine
	@echo "Setting environment variables..."
	@echo "export DATABASE_URL=\"postgresql://dprofiler:password@localhost:5432/dprofiler\""
	@echo "export REDIS_URL=\"redis://localhost:6379/0\""
	@echo "Initializing database..."
	python -c "from core.database import db_manager; db_manager.init_db()"
	@echo "✅ Local setup completed!"
	@echo "Next steps:"
	@echo "1. source venv/bin/activate"
	@echo "2. export DATABASE_URL=\"postgresql://dprofiler:password@localhost:5432/dprofiler\""
	@echo "3. export REDIS_URL=\"redis://localhost:6379/0\""
	@echo "4. make local-test"

local-test:
	@echo "🧪 Testing local setup..."
	@echo "Starting API server..."
	@echo "uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"
	@echo "In another terminal, start Celery worker:"
	@echo "celery -A workers.task_queue.celery_app worker --loglevel=info"
	@echo "Then run: make local-health"

local-health:
	@echo "🏥 Running local health checks..."
	@echo "Checking API health..."
	@if curl -f -s http://localhost:8000/health > /dev/null; then \
		echo "✅ API is healthy"; \
	else \
		echo "❌ API health check failed"; \
	fi
	@echo "Checking database connection..."
	@if python -c "from core.database import db_manager; print('Database:', 'OK' if db_manager.check_connection() else 'FAILED')" | grep -q "OK"; then \
		echo "✅ Database is healthy"; \
	else \
		echo "❌ Database health check failed"; \
	fi
	@echo "Checking Redis connection..."
	@if python -c "import redis; r = redis.Redis(host='localhost', port=6379); print('Redis:', 'OK' if r.ping() else 'FAILED')" | grep -q "OK"; then \
		echo "✅ Redis is healthy"; \
	else \
		echo "❌ Redis health check failed"; \
	fi

# Kubernetes Commands
k8s-deploy:
	@echo "🚀 Deploying to Kubernetes..."
	cd k8s && ./deploy.sh

k8s-clean:
	@echo "🧹 Cleaning up Kubernetes deployment..."
	kubectl delete namespace dprofiler --ignore-not-found=true

# Utility Commands
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker compose down -v
	docker system prune -f
	docker volume prune -f

docker-build:
	@echo "🔨 Building Docker images..."
	docker build -t dprofiler-api:latest .
	docker build -t dprofiler-worker:latest .

docker-push:
	@echo "📤 Pushing Docker images..."
	@echo "Please update the registry URL and run:"
	@echo "docker tag dprofiler-api:latest <registry>/dprofiler-api:latest"
	@echo "docker tag dprofiler-worker:latest <registry>/dprofiler-worker:latest"
	@echo "docker push <registry>/dprofiler-api:latest"
	@echo "docker push <registry>/dprofiler-worker:latest"

# Troubleshooting Commands
troubleshoot:
	@echo "🔍 Running comprehensive troubleshooting..."
	@echo "1. Checking service status..."
	make status
	@echo ""
	@echo "2. Checking service logs..."
	docker compose logs --tail=20
	@echo ""
	@echo "3. Checking port usage..."
	lsof -i :8000 -i :5432 -i :6379 || echo "No processes found on required ports"
	@echo ""
	@echo "4. Checking Docker daemon..."
	docker info > /dev/null 2>&1 && echo "✅ Docker daemon is running" || echo "❌ Docker daemon is not running"
	@echo ""
	@echo "5. Checking disk space..."
	df -h | head -5
	@echo ""
	@echo "6. Checking memory usage..."
	free -h || vm_stat

debug:
	@echo "🐛 Enabling debug mode..."
	@echo "Setting debug environment variables..."
	export LOG_LEVEL=DEBUG
	export SQL_ECHO=true
	@echo "Restarting services in debug mode..."
	docker compose down
	docker compose up -d
	@echo "Showing debug logs..."
	docker compose logs -f

# API Testing Commands
test-api-endpoints:
	@echo "🧪 Testing API endpoints..."
	@echo "1. Health check..."
	curl -s http://localhost:8000/health | jq '.'
	@echo ""
	@echo "2. List algorithms..."
	curl -s http://localhost:8000/api/v1/algorithms | jq '.'
	@echo ""
	@echo "3. Create test job..."
	JOB_RESPONSE=$$(curl -s -X POST http://localhost:8000/api/v1/jobs \
		-H "Content-Type: application/json" \
		-d '{"algorithm_name": "quick_sort", "input_size": 1000}'); \
	echo "$$JOB_RESPONSE" | jq '.'; \
	JOB_ID=$$(echo "$$JOB_RESPONSE" | jq -r '.job_id'); \
	echo "Job ID: $$JOB_ID"
	@echo ""
	@echo "4. Get job status..."
	curl -s http://localhost:8000/api/v1/jobs/$$JOB_ID | jq '.'
	@echo ""
	@echo "5. List workers..."
	curl -s http://localhost:8000/api/v1/workers | jq '.'
	@echo ""
	@echo "6. Get metrics..."
	curl -s http://localhost:8000/metrics | head -20

# Performance Testing
benchmark:
	@echo "⚡ Running performance benchmarks..."
	@echo "Creating multiple jobs for benchmarking..."
	for i in {1..5}; do \
		echo "Creating job $$i..."; \
		curl -s -X POST http://localhost:8000/api/v1/jobs \
			-H "Content-Type: application/json" \
			-d "{\"algorithm_name\": \"merge_sort\", \"input_size\": 5000}" > /dev/null; \
	done
	@echo "Monitoring job completion..."
	for i in {1..30}; do \
		COMPLETED=$$(curl -s http://localhost:8000/api/v1/jobs | jq '.jobs[] | select(.status == "completed") | .job_id' | wc -l); \
		echo "Completed jobs: $$COMPLETED"; \
		if [ "$$COMPLETED" -eq 5 ]; then \
			echo "✅ All benchmark jobs completed!"; \
			break; \
		fi; \
		sleep 2; \
	done

# Monitoring Commands
monitor:
	@echo "📊 Starting system monitoring..."
	@echo "Press Ctrl+C to stop monitoring"
	@while true; do \
		echo "=== $$(date) ==="; \
		echo "API Health: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health)"; \
		echo "Active Jobs: $$(curl -s http://localhost:8000/api/v1/jobs | jq '.jobs[] | select(.status == "running") | .job_id' | wc -l)"; \
		echo "Completed Jobs: $$(curl -s http://localhost:8000/api/v1/jobs | jq '.jobs[] | select(.status == "completed") | .job_id' | wc -l)"; \
		echo "Worker Status: $$(docker compose exec -T api celery -A workers.task_queue.celery_app inspect active 2>/dev/null | jq -r '.active | length // 0')"; \
		echo "---"; \
		sleep 5; \
	done 
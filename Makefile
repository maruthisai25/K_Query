# Infra Copilot - Makefile
# Convenient commands for development and deployment

.PHONY: help setup build test run clean deploy

# Default target
help:
	@echo "Infra Copilot - Available Commands"
	@echo "=================================="
	@echo ""
	@echo "Development:"
	@echo "  setup     - Initialize knowledge base in Qdrant"
	@echo "  build     - Build Docker image"
	@echo "  test      - Run component tests"
	@echo "  run       - Start all services with docker-compose"
	@echo "  run-local - Run application locally (without Docker)"
	@echo "  clean     - Clean up containers and images"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy    - Deploy to Kubernetes"
	@echo "  build-multi - Build multi-arch Docker image"
	@echo ""
	@echo "Utilities:"
	@echo "  logs      - Show application logs"
	@echo "  shell     - Open shell in running container"

# Initialize knowledge base
setup:
	@echo "🚀 Initializing knowledge base..."
	chmod +x scripts/setup.sh
	./scripts/setup.sh

# Build Docker image
build:
	@echo "🐳 Building Docker image..."
	docker build -t infra-copilot:latest .

# Build multi-arch image
build-multi:
	@echo "🐳 Building multi-arch Docker image..."
	chmod +x scripts/build.sh
	./scripts/build.sh

# Run tests
test:
	@echo "🧪 Running component tests..."
	chmod +x scripts/test.sh
	./scripts/test.sh

# Start all services
run:
	@echo "🚀 Starting all services..."
	docker-compose up -d
	@echo "Services started! Access:"
	@echo "  - Main App: http://localhost:8000"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Grafana: http://localhost:3000"
	@echo "  - Qdrant: http://localhost:6333"

# Run locally without Docker
run-local:
	@echo "🚀 Running application locally..."
	chmod +x scripts/run-local.sh
	./scripts/run-local.sh

# Stop all services
stop:
	@echo "🛑 Stopping all services..."
	docker-compose down

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f

# Deploy to Kubernetes
deploy:
	@echo "☸️  Deploying to Kubernetes..."
	kubectl apply -k k8s/

# Show logs
logs:
	@echo "📋 Showing application logs..."
	docker-compose logs -f infra-copilot

# Open shell in container
shell:
	@echo "🐚 Opening shell in container..."
	docker-compose exec infra-copilot /bin/bash

# Development setup
dev-setup: setup run
	@echo "🎉 Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy .env.example to .env and add your Slack credentials"
	@echo "2. Run 'make test' to verify everything is working"
	@echo "3. Access the application at http://localhost:8000"

# Full deployment pipeline
deploy-full: build-multi deploy
	@echo "🚀 Full deployment completed!"

# Check status
status:
	@echo "📊 Service Status:"
	@docker-compose ps
	@echo ""
	@echo "🔍 Quick Health Check:"
	@curl -s http://localhost:8000/health || echo "❌ API not responding"
	@curl -s http://localhost:6333/health > /dev/null && echo "✅ Qdrant is healthy" || echo "❌ Qdrant not responding"
	@curl -s http://localhost:9090/api/v1/query?query=up > /dev/null && echo "✅ Prometheus is healthy" || echo "❌ Prometheus not responding"
# K-Query - DevOps Assistant

A Slack bot that answers DevOps questions using Ollama with kubectl and Prometheus integration.

## Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your Slack credentials

# 2. Start everything
make dev-setup

# 3. Test components
make test
```

## Features

- **Slack Integration**: `/devops` command and direct messages
- **Ollama Integration**: Local model inference
- **Kubernetes Integration**: Live cluster information via kubectl
- **Prometheus Monitoring**: Real-time metrics and alerts
- **Vector Search**: FAQ and runbook search with Qdrant
- **Multi-arch Support**: AMD64 and ARM64 Docker images
- **Production Ready**: Kubernetes manifests with HPA, RBAC, and monitoring

## Development Commands

```bash
make setup      # Initialize knowledge base
make build      # Build Docker image
make test       # Run component tests
make run        # Start all services with Docker
make run-local  # Run locally without Docker
make deploy     # Deploy to Kubernetes
make clean      # Clean up containers
```

## Quick Deploy

### Local Development
```bash
docker-compose up -d
```

### Kubernetes Production
```bash
kubectl apply -k k8s/
```

## License

This project is licensed under the MIT License.
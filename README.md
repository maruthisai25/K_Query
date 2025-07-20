# K-Query - Self-Hosted LLM DevOps Assistant

A Slack bot that answers DevOps questions using a local Llama model with kubectl and Prometheus integration.

## 🚀 Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your Slack credentials

# 2. Start everything
make dev-setup

# 3. Test components
make test
```

## 📁 Project Structure

```
k-query/
├── src/                    # Python source code
│   ├── main.py            # FastAPI application
│   ├── config.py          # Configuration management
│   ├── llm_service.py     # Ollama integration
│   ├── k8s_client.py      # Kubernetes client
│   ├── prometheus_client.py # Prometheus integration
│   ├── vector_store.py    # Qdrant vector database
│   └── slack_bot.py       # Slack bot handler
├── k8s/                   # Kubernetes manifests
│   ├── deployment.yaml    # Main application deployment
│   ├── service.yaml       # Kubernetes services
│   ├── rbac.yaml          # RBAC configuration
│   ├── hpa.yaml           # Horizontal Pod Autoscaler
│   ├── configmap.yaml     # Configuration and secrets
│   ├── qdrant.yaml        # Qdrant deployment
│   ├── namespace.yaml     # Kubernetes namespace
│   └── kustomization.yaml # Kustomize configuration
├── scripts/               # Setup and build scripts
│   ├── setup.sh           # Initialize knowledge base
│   ├── build.sh           # Multi-arch Docker build
│   ├── test.sh            # Component tests
│   └── start.sh           # Container startup script
├── config/                # Configuration files
│   └── prometheus.yml     # Prometheus configuration
├── docs/                  # Documentation
│   └── README.md          # Detailed documentation
├── .env.example           # Environment variables template
├── docker-compose.yml     # Local development stack
├── Dockerfile             # Container image definition
├── requirements.txt       # Python dependencies
└── Makefile              # Development commands
```

## 🛠️ Development Commands

```bash
make setup      # Initialize knowledge base
make build      # Build Docker image
make test       # Run component tests
make run        # Start all services with Docker
make run-local  # Run locally without Docker
make deploy     # Deploy to Kubernetes
make clean      # Clean up containers
```

## 📖 Documentation

For detailed setup instructions, API documentation, and deployment guides, see [docs/README.md](docs/README.md).

## 🎯 Features

- **Slack Integration**: `/devops` command and direct messages
- **Local LLM**: Ollama with Llama-2-7B model
- **Kubernetes Integration**: Live cluster information via kubectl
- **Prometheus Monitoring**: Real-time metrics and alerts
- **Vector Search**: FAQ and runbook search with Qdrant
- **Multi-arch Support**: AMD64 and ARM64 Docker images
- **Production Ready**: Kubernetes manifests with HPA, RBAC, and monitoring

## 🚀 Quick Deploy

### Local Development
```bash
docker-compose up -d
```

### Kubernetes Production
```bash
kubectl apply -k k8s/
```

## 📝 License

This project is licensed under the MIT License.
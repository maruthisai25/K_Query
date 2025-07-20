# K-Query - Project Structure

## 📁 Directory Layout

```
k-query/
├── 📁 src/                     # Python source code
│   ├── 🐍 main.py             # FastAPI application entry point
│   ├── ⚙️  config.py           # Configuration management
│   ├── 🤖 llm_service.py      # Ollama LLM integration
│   ├── ☸️  k8s_client.py       # Kubernetes API client
│   ├── 📊 prometheus_client.py # Prometheus metrics client
│   ├── 🔍 vector_store.py     # Qdrant vector database client
│   ├── 💬 slack_bot.py        # Slack bot integration
│   └── 📦 __init__.py         # Package initialization
├── 📁 k8s/                    # Kubernetes manifests
│   ├── 🚀 deployment.yaml    # Main application deployment
│   ├── 🌐 service.yaml       # Kubernetes services
│   ├── 🔐 rbac.yaml          # Role-based access control
│   ├── 📈 hpa.yaml           # Horizontal Pod Autoscaler
│   ├── ⚙️  configmap.yaml     # Configuration and secrets
│   ├── 🗄️  qdrant.yaml        # Qdrant vector database
│   ├── 🏷️  namespace.yaml     # Kubernetes namespace
│   └── 🔧 kustomization.yaml # Kustomize configuration
├── 📁 scripts/               # Automation scripts
│   ├── 🛠️  setup.sh           # Initialize knowledge base
│   ├── 🐳 build.sh           # Multi-arch Docker build
│   ├── 🧪 test.sh            # Component validation tests
│   ├── 🚀 start.sh           # Container startup script
│   └── 💻 run-local.sh       # Local development runner
├── 📁 config/                # Configuration files
│   └── 📊 prometheus.yml     # Prometheus scraping config
├── 📁 docs/                  # Documentation
│   └── 📖 README.md          # Detailed documentation
├── 🔧 .env.example           # Environment variables template
├── 🐳 docker-compose.yml     # Local development stack
├── 📦 Dockerfile             # Container image definition
├── 📋 requirements.txt       # Python dependencies
├── 🛠️  Makefile              # Development commands
├── 🚫 .gitignore             # Git ignore patterns
├── 🚫 .dockerignore          # Docker ignore patterns
├── 📖 README.md              # Main project documentation
└── 📝 tasks.md.txt           # Original task requirements
```

## 🔄 Data Flow

```
Slack User → Slack Bot → FastAPI → LLM Service → Ollama (Llama-2-7B)
                ↓              ↓
        Vector Store ← Kubernetes API
                ↓              ↓
            Qdrant ←   Prometheus API
```

## 🚀 Deployment Options

### 1. Local Development
- **Docker Compose**: Full stack with all services
- **Local Python**: Direct execution with virtual environment

### 2. Production Kubernetes
- **Kustomize**: Declarative configuration management
- **Manual**: Individual manifest deployment

## 🔧 Key Components

### Core Services
- **FastAPI**: REST API and webhook handler
- **Ollama**: Local LLM inference engine
- **Qdrant**: Vector database for knowledge search
- **Prometheus**: Metrics collection and monitoring

### Integrations
- **Slack**: Bot interface for user interactions
- **Kubernetes**: Live cluster information retrieval
- **Docker**: Containerized deployment

### Automation
- **Setup Scripts**: Knowledge base initialization
- **Build Scripts**: Multi-architecture image creation
- **Test Scripts**: Component validation
- **Makefile**: Development workflow automation

## 📊 Monitoring & Observability

- **Health Checks**: Application and dependency status
- **Metrics**: Request counts, response times, resource usage
- **Logging**: Structured application logs
- **Alerts**: Prometheus-based alerting (configurable)

## 🔐 Security Features

- **RBAC**: Kubernetes role-based access control
- **Secrets**: Encrypted configuration management
- **Network Policies**: Service-to-service communication control
- **Resource Limits**: Container resource constraints

## 🎯 Development Workflow

1. **Setup**: `make dev-setup` - Initialize everything
2. **Develop**: `make run-local` - Local development
3. **Test**: `make test` - Validate components
4. **Build**: `make build-multi` - Create images
5. **Deploy**: `make deploy` - Deploy to Kubernetes

## 📈 Scaling Strategy

- **Horizontal**: HPA based on CPU, memory, and request rate
- **Vertical**: Resource limit adjustments
- **Storage**: Persistent volumes for data persistence
- **Network**: Load balancing and service discovery
# K-Query - DevOps Automation Platform

A comprehensive Slack bot for DevOps automation with kubectl and Prometheus integration. Streamline infrastructure management, troubleshoot issues, and access real-time cluster metrics directly from Slack.

## Features

- **Slack Integration**: `/devops` command and direct messages
- **Local Model Integration**: Private model inference for security and control
- **Kubernetes Integration**: Live cluster information via kubectl
- **Prometheus Monitoring**: Real-time metrics and alerts
- **Vector Search**: FAQ and runbook search with Qdrant
- **Multi-arch Support**: AMD64 and ARM64 Docker images
- **Production Ready**: Kubernetes manifests with HPA, RBAC, and monitoring

## Prerequisites

- Docker and Docker Compose
- Kubernetes cluster (for production deployment)
- Slack workspace with bot permissions
- Python 3.11+ (for local development)

## Quick Start

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd k-query

# Copy environment template
cp .env.example .env
```

Edit `.env` with your Slack credentials:
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

### 2. Slack Application Setup

1. Go to [Slack API](https://api.slack.com/apps) and create a new app
2. Enable the following OAuth scopes:
   - `app_mentions:read`
   - `chat:write`
   - `commands`
   - `im:read`
   - `im:write`
3. Create a slash command `/devops`
4. Install the app to your workspace
5. Copy the Bot Token and Signing Secret to your `.env` file

### 3. Start Services

```bash
# Initialize everything (first time only)
make dev-setup

# Start all services
make run

# Or start with Docker Compose directly
docker-compose up -d
```

### 4. Verify Installation

```bash
# Check service health
curl http://localhost:8000/health

# Run component tests
make test
```

## Usage

### Slack Commands

- `/devops <question>` - Ask DevOps questions via slash command
- Direct message the bot for private conversations

### Example Questions

```
/devops Why are my pods crashing?
/devops Show me CPU usage for the frontend service
/devops What's the status of my deployments in production?
/devops How do I troubleshoot high memory usage?
/devops List all pods in the default namespace
/devops Show me error rates from Prometheus
```

### API Endpoints

- `GET /health` - Health check for all services
- `POST /chat` - Direct chat API
- `GET /metrics` - Prometheus metrics
- `POST /slack/events` - Slack webhook endpoint

## Architecture

### Components

- **FastAPI**: REST API and Slack webhook handler
- **Local Model Engine**: Private model inference engine
- **Qdrant**: Vector database for knowledge search
- **Kubernetes Client**: Live cluster information retrieval
- **Prometheus Client**: Metrics collection and querying
- **Slack Integration**: Interactive Slack integration

### Data Flow

```
Slack User → Slack Integration → FastAPI → Model Engine
                ↓                    ↓
        Vector Store ←      Kubernetes API
                ↓                    ↓
            Qdrant ←         Prometheus API
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SLACK_BOT_TOKEN="your-token"
export SLACK_SIGNING_SECRET="your-secret"

# Initialize knowledge base
./scripts/setup.sh

# Run the application
python -m src.main
```

### Development Commands

```bash
make setup      # Initialize knowledge base
make build      # Build Docker image
make test       # Run component tests
make run        # Start all services with Docker
make run-local  # Run locally without Docker
make deploy     # Deploy to Kubernetes
make clean      # Clean up containers
make lint       # Run code linting
make security   # Security vulnerability checks
```

### Project Structure

```
k-query/
├── src/                    # Python source code
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── llm_service.py     # Model integration service
│   ├── k8s_client.py      # Kubernetes API client
│   ├── prometheus_client.py # Prometheus metrics client
│   ├── vector_store.py    # Qdrant vector database client
│   └── slack_bot.py       # Slack integration service
├── k8s/                   # Kubernetes manifests
├── scripts/               # Setup and build scripts
├── config/                # Configuration files
├── tests/                 # Test files
├── docker-compose.yml     # Local development stack
├── Dockerfile             # Container image definition
├── requirements.txt       # Python dependencies
└── Makefile              # Development commands
```

## Deployment

### Local Development with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f k-query

# Stop services
docker-compose down
```

### Kubernetes Production

```bash
# Deploy with Kustomize (recommended)
kubectl apply -k k8s/

# Or deploy individual manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
```

### Configuration

Update the ConfigMap and Secret in `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: k-query-secrets
type: Opaque
stringData:
  slack-bot-token: "xoxb-your-actual-token"
  slack-signing-secret: "your-actual-secret"
```

### Monitoring

The application exposes Prometheus metrics at `/metrics`:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `chat_requests_total` - Total chat requests
- `chat_request_duration_seconds` - Chat processing time

Access monitoring dashboards:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

## Troubleshooting

### Common Issues

1. **Model not found**
   ```bash
   # Pull the model manually
   docker exec -it k-query_k-query_1 ollama pull llama2:7b
   ```

2. **Slack webhook verification failed**
   - Check your signing secret in `.env`
   - Ensure the webhook URL is accessible from Slack

3. **Kubernetes permissions denied**
   - Verify RBAC configuration
   - Check service account permissions

4. **Vector store initialization failed**
   - Ensure Qdrant is running and accessible
   - Check network connectivity between services

### Logs

```bash
# Docker Compose logs
docker-compose logs -f k-query

# Kubernetes logs
kubectl logs -f deployment/k-query

# Individual service logs
docker logs k-query_qdrant_1
docker logs k-query_prometheus_1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
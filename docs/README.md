# Infra Copilot - Self-Hosted LLM DevOps Assistant

A Slack bot that answers DevOps questions using a local Llama model with kubectl and Prometheus integration.

## Quick Start with Docker Compose

### Prerequisites
- Docker and Docker Compose
- Slack Bot Token and Signing Secret

### Setup

1. **Clone and configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your Slack credentials
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Access services:**
   - **Main App**: http://localhost:8000
   - **Prometheus**: http://localhost:9090
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **Qdrant**: http://localhost:6333

### Services Included

- **infra-copilot**: Main FastAPI application with Ollama
- **qdrant**: Vector database for FAQ/runbooks
- **prometheus**: Metrics collection
- **grafana**: Metrics visualization

### API Endpoints

- `GET /health` - Health check
- `POST /chat` - Chat with the AI assistant
- `GET /metrics` - Prometheus metrics
- `POST /slack/events` - Slack webhook

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster
- kubectl configured

### Deploy

1. **Using Kustomize (recommended):**
   ```bash
   kubectl apply -k k8s/
   ```

2. **Or deploy individually:**
   ```bash
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/rbac.yaml
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/qdrant.yaml
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml
   kubectl apply -f k8s/hpa.yaml
   ```

### Configuration

Update the Secret in `k8s/configmap.yaml` with your actual Slack credentials:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: infra-copilot-secrets
type: Opaque
stringData:
  slack-bot-token: "xoxb-your-actual-token"
  slack-signing-secret: "your-actual-secret"
```

## Usage

### Slack Commands

- `/devops <question>` - Ask DevOps questions
- Direct message the bot for private conversations

### Example Questions

- "Why are my pods crashing?"
- "Show me CPU usage"
- "What's the status of my deployments?"
- "How do I troubleshoot high memory usage?"

## Architecture

- **FastAPI**: REST API and Slack integration
- **Ollama**: Local LLM inference (Llama-2-7B)
- **Qdrant**: Vector database for knowledge base
- **Kubernetes Client**: Live cluster information
- **Prometheus**: Metrics and monitoring data

## Setup Scripts

### Initialize Knowledge Base
```bash
# Make script executable
chmod +x scripts/setup.sh

# Run setup (ensure Qdrant is running first)
./scripts/setup.sh
```

### Multi-arch Docker Build
```bash
# Make script executable
chmod +x scripts/build.sh

# Build for local use
./scripts/build.sh

# Build and push to registry
./scripts/build.sh --push --registry your-registry.com

# Build specific platforms
./scripts/build.sh --platforms linux/amd64 --tag v1.0.0
```

### Test Components
```bash
# Make script executable
chmod +x scripts/test.sh

# Run all tests
./scripts/test.sh

# Test with custom URLs
./scripts/test.sh --api-url http://localhost:8080
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

### Building Docker Image
```bash
# Simple build
docker build -t infra-copilot:latest .

# Multi-arch build with script
./scripts/build.sh --tag latest
```

## Monitoring

The application exposes Prometheus metrics at `/metrics`:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `chat_requests_total` - Total chat requests
- `chat_request_duration_seconds` - Chat processing time
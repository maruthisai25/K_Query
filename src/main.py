from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging
import time
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from .llm_service import LLMService
from .k8s_client import K8sClient
from .prometheus_client import PrometheusClient as CustomPrometheusClient
from .vector_store import VectorStore
from .slack_bot import SlackBot
from .config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
CHAT_REQUESTS = Counter('chat_requests_total', 'Total chat requests')
CHAT_DURATION = Histogram('chat_request_duration_seconds', 'Chat request duration')

# Initialize services
config = Config()
llm_service = LLMService()
k8s_client = K8sClient()
prometheus_client = CustomPrometheusClient(config.PROMETHEUS_URL)
vector_store = VectorStore(config.QDRANT_URL)
slack_bot = SlackBot()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting K-Query...")
    
    # Validate configuration
    if not config.validate():
        logger.error("Configuration validation failed")
        raise RuntimeError("Configuration validation failed")
    
    # Initialize vector store
    try:
        await vector_store.initialize_collection()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        raise
    
    logger.info("K-Query started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down K-Query...")


app = FastAPI(
    title="K-Query DevOps Platform", 
    version="1.0.0",
    description="DevOps automation platform with Slack integration",
    lifespan=lifespan
)

class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: Optional[list] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    REQUEST_COUNT.labels(method="GET", endpoint="/health").inc()
    
    # Check all dependencies
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    try:
        health_status["services"]["ollama"] = await llm_service.health_check()
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        health_status["services"]["ollama"] = False
    
    try:
        health_status["services"]["qdrant"] = await vector_store.health_check()
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        health_status["services"]["qdrant"] = False
    
    try:
        health_status["services"]["kubernetes"] = await k8s_client.health_check()
    except Exception as e:
        logger.error(f"Kubernetes health check failed: {e}")
        health_status["services"]["kubernetes"] = False
    
    try:
        health_status["services"]["prometheus"] = await prometheus_client.health_check()
    except Exception as e:
        logger.error(f"Prometheus health check failed: {e}")
        health_status["services"]["prometheus"] = False
    
    # Overall health
    if not all(health_status["services"].values()):
        health_status["status"] = "unhealthy"
        return JSONResponse(status_code=503, content=health_status)
    
    return health_status

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack events and slash commands"""
    REQUEST_COUNT.labels(method="POST", endpoint="/slack/events").inc()
    return await slack_bot.get_handler().handle(request)

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint for DevOps automation"""
    start_time = time.time()
    REQUEST_COUNT.labels(method="POST", endpoint="/chat").inc()
    CHAT_REQUESTS.inc()
    
    try:
        # Search for relevant context in vector store
        relevant_docs = await vector_store.search(request.message, limit=3)
        
        # Get Kubernetes context if question seems k8s related
        k8s_context = ""
        if any(keyword in request.message.lower() for keyword in ["pod", "deployment", "service", "namespace", "kubectl"]):
            k8s_context = await k8s_client.get_relevant_info(request.message)
        
        # Get Prometheus metrics if question seems monitoring related
        metrics_context = ""
        if any(keyword in request.message.lower() for keyword in ["metrics", "cpu", "memory", "error", "latency"]):
            metrics_context = await prometheus_client.get_relevant_metrics(request.message)
        
        # Combine all context
        context_parts = []
        if relevant_docs:
            context_parts.append(f"Relevant documentation: {relevant_docs}")
        if k8s_context:
            context_parts.append(f"Kubernetes context: {k8s_context}")
        if metrics_context:
            context_parts.append(f"Metrics context: {metrics_context}")
        if request.context:
            context_parts.append(f"Additional context: {request.context}")
        
        full_context = "\n".join(context_parts)
        
        # Generate response using model service
        response = await llm_service.generate_response(
            message=request.message,
            context=full_context.strip()
        )
        
        duration = time.time() - start_time
        CHAT_DURATION.observe(duration)
        
        return ChatResponse(
            response=response,
            sources=[doc.get("source", "") for doc in relevant_docs if doc.get("source")]
        )
        
    except Exception as e:
        duration = time.time() - start_time
        CHAT_DURATION.observe(duration)
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


def main():
    """Main entry point for the application"""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
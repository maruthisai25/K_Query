import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Slack configuration
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_SIGNING_SECRET: str = os.getenv("SLACK_SIGNING_SECRET", "")
    
    # Prometheus configuration
    PROMETHEUS_URL: str = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
    
    # Qdrant configuration
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    
    # Kubernetes configuration
    KUBERNETES_NAMESPACE: Optional[str] = os.getenv("KUBERNETES_NAMESPACE", "default")
    
    # Model configuration
    MODEL_PATH: str = os.getenv("MODEL_PATH", "llama2:7b")
    
    # Ollama configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "localhost")
    OLLAMA_PORT: int = int(os.getenv("OLLAMA_PORT", "11434"))
    
    @property
    def ollama_url(self) -> str:
        return f"http://{self.OLLAMA_HOST}:{self.OLLAMA_PORT}"
    
    def validate(self) -> bool:
        """Validate required configuration"""
        required_vars = [
            ("SLACK_BOT_TOKEN", self.SLACK_BOT_TOKEN),
            ("SLACK_SIGNING_SECRET", self.SLACK_SIGNING_SECRET),
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
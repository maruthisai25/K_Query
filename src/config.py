import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log') if os.getenv('LOG_TO_FILE', 'false').lower() == 'true' else logging.NullHandler()
    ]
)

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
    
    # Timeout configurations
    HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", "30"))
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_TO_FILE: bool = os.getenv("LOG_TO_FILE", "false").lower() == "true"
    
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
            logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        # Validate URL formats
        if not self._is_valid_url(self.PROMETHEUS_URL):
            logging.error(f"Invalid PROMETHEUS_URL: {self.PROMETHEUS_URL}")
            return False
            
        if not self._is_valid_url(self.QDRANT_URL):
            logging.error(f"Invalid QDRANT_URL: {self.QDRANT_URL}")
            return False
        
        # Validate port ranges
        if not (1 <= self.OLLAMA_PORT <= 65535):
            logging.error(f"Invalid OLLAMA_PORT: {self.OLLAMA_PORT}")
            return False
            
        # Validate timeout values
        if self.HTTP_TIMEOUT <= 0 or self.OLLAMA_TIMEOUT <= 0:
            logging.error("Timeout values must be positive")
            return False
        
        logging.info("Configuration validation passed")
        return True
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        return url.startswith(('http://', 'https://')) and len(url) > 8
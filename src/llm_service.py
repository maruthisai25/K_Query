import aiohttp
import json
import logging
from typing import Optional
from .config import Config
from .resilience import with_retries, with_circuit_breaker, ollama_circuit_breaker

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.config = Config()
        self.ollama_url = self.config.ollama_url
        self.model_name = self.config.MODEL_PATH
    
    async def ensure_model_loaded(self):
        """Ensure the Llama model is loaded in Ollama"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if model exists
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]
                        if self.model_name not in models:
                            logger.info(f"Pulling model {self.model_name}")
                            await self._pull_model()
        except Exception as e:
            logger.error(f"Error checking model status: {str(e)}")
    
    async def _pull_model(self):
        """Pull the Llama model if not available"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"name": self.model_name}
                async with session.post(
                    f"{self.ollama_url}/api/pull",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"Successfully pulled model {self.model_name}")
                    else:
                        logger.error(f"Failed to pull model: {response.status}")
        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")
    
    @with_retries(max_attempts=3, delay=1.0)
    @with_circuit_breaker(ollama_circuit_breaker)
    async def generate_response(self, message: str, context: Optional[str] = None) -> str:
        """Generate response using Ollama"""
        await self.ensure_model_loaded()
        
        # Create system prompt for DevOps assistant
        system_prompt = """You are an expert DevOps assistant. You help with Kubernetes, monitoring, 
        infrastructure questions, and troubleshooting. Use the provided context to give accurate, 
        actionable answers. If you don't know something, say so clearly."""
        
        # Combine user message with context
        full_prompt = f"{system_prompt}\n\nContext: {context}\n\nQuestion: {message}"
        
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": self.model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                }
                
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("response", "Sorry, I couldn't generate a response.")
                    else:
                        logger.error(f"Ollama API error: {response.status}")
                        return "Sorry, there was an error generating the response."
                        
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return "Sorry, I'm having trouble connecting to the language model."
    
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False
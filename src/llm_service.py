import asyncio
import logging
from typing import Optional

import aiohttp

from .config import Config
from .resilience import ollama_circuit_breaker, with_circuit_breaker, with_retries

logger = logging.getLogger(__name__)


class LLMServiceError(RuntimeError):
    """Raised when Ollama cannot be reached or returns a non-200 response."""


class LLMService:
    def __init__(self):
        self.config = Config()
        self.ollama_url = self.config.ollama_url
        self.model_name = self.config.MODEL_PATH
        self.timeout = aiohttp.ClientTimeout(total=self.config.OLLAMA_TIMEOUT)

    async def ensure_model_loaded(self):
        """Ensure the model is loaded in Ollama"""
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
        """Pull the model if not available"""
        try:
            # Use longer timeout for model pulling
            pull_timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
            async with aiohttp.ClientSession(timeout=pull_timeout) as session:
                payload = {"name": self.model_name}
                async with session.post(f"{self.ollama_url}/api/pull", json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Successfully pulled model {self.model_name}")
                    else:
                        logger.error(f"Failed to pull model: {response.status}")
        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")

    # Breaker outside, retries inside: a request that fails all three attempts
    # counts as one failure against the breaker, so a single bad request cannot
    # trip a threshold of three on its own.
    @with_circuit_breaker(ollama_circuit_breaker)
    @with_retries(max_attempts=3, delay=1.0)
    async def generate_response(self, message: str, context: Optional[str] = None) -> str:
        """Generate a response with Ollama.

        Raises LLMServiceError on transport failure or a non-200 response. This
        has to raise: it is wrapped in @with_retries and @with_circuit_breaker,
        and both of those only see a failure if one propagates out. Returning an
        apology string here would make the retry loop and the breaker dead code.
        Turning the error into something a human reads is the caller's job.
        """
        await self.ensure_model_loaded()

        # Create system prompt for DevOps automation
        system_prompt = (
            "You are an expert DevOps automation system. You help with Kubernetes, "
            "monitoring, infrastructure management, and troubleshooting. Use the "
            "provided context to give accurate, actionable responses. If you don't "
            "know something, say so clearly. Keep responses concise and practical."
        )

        # Combine user message with context
        if context and context.strip():
            full_prompt = f"{system_prompt}\n\nContext: {context}\n\nQuestion: {message}"
        else:
            full_prompt = f"{system_prompt}\n\nQuestion: {message}"

        payload = {
            "model": self.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 500,
                "stop": ["\n\nQuestion:", "\n\nContext:"],
            },
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate", json=payload
                ) as response:
                    if response.status != 200:
                        body = (await response.text())[:200]
                        raise LLMServiceError(f"Ollama returned HTTP {response.status}: {body}")
                    data = await response.json()
        except LLMServiceError:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise LLMServiceError(f"Could not reach Ollama at {self.ollama_url}: {e}") from e

        return data.get("response", "")

    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.ollama_url}/api/tags") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return False

import asyncio
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitBreakerOpen(RuntimeError):
    """Raised instead of calling through a breaker that is currently open."""


class CircuitBreaker:
    """Simple circuit breaker implementation"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call_failed(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def call_succeeded(self):
        self.failure_count = 0
        self.state = "closed"

    def can_execute(self) -> bool:
        if self.state == "closed":
            return True

        if self.state == "open":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = "half-open"
                logger.info("Circuit breaker entering half-open state")
                return True
            return False

        return True  # half-open state


def with_retries(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator for adding retry logic to async functions"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff**attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                            f"Retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )

            raise last_exception

        return wrapper

    return decorator


def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """Decorator for adding circuit breaker to async functions"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not circuit_breaker.can_execute():
                raise CircuitBreakerOpen(f"Circuit breaker is open for {func.__name__}")

            try:
                result = await func(*args, **kwargs)
                circuit_breaker.call_succeeded()
                return result
            except Exception:
                circuit_breaker.call_failed()
                raise

        return wrapper

    return decorator


# Ollama is the only dependency behind a breaker. The Kubernetes and Prometheus
# clients degrade to a message in the prompt context rather than failing the
# request, so tripping a breaker for them would not change any outcome.
ollama_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

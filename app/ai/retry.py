"""
Retry utilities with exponential backoff and jitter for resilient external API calls.
"""

import asyncio
import functools
import random
from typing import Any, Callable, Tuple, Type


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """Decorator for retrying async functions with exponential backoff and jitter."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_err: Exception | None = None
            delay = base_delay

            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    if attempt == max_retries:
                        break
                    # Calculate exponential backoff with full jitter
                    sleep_time = min(max_delay, delay * (2 ** (attempt - 1)))
                    jitter = random.uniform(0, sleep_time * 0.1)
                    actual_sleep = sleep_time + jitter
                    print(
                        f"[RETRY] Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}. Retrying in {actual_sleep:.2f}s"
                    )
                    await asyncio.sleep(actual_sleep)

            raise last_err if last_err else RuntimeError("Retry failed unexpectedly")

        return wrapper

    return decorator

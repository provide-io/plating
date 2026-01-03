#
# SPDX-FileCopyrightText: Copyright (c) 2025 provide.io llc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#

"""Foundation integration decorators for clean API."""

import asyncio
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
import functools
import time
from typing import Any, TypeVar

from provide.foundation import logger
from provide.foundation.resilience import BackoffStrategy, RetryExecutor, RetryPolicy, SyncCircuitBreaker

F = TypeVar("F", bound=Callable[..., Any])


def with_retry(
    max_attempts: int = 3,
    backoff: str = "exponential",
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_errors: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator for automatic retry with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff: Backoff strategy ("exponential", "linear", "constant")
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        retryable_errors: Tuple of exception types that should trigger retry
    """

    def decorator(func: F) -> F:
        # Convert string to BackoffStrategy enum
        backoff_strategy = {
            "exponential": BackoffStrategy.EXPONENTIAL,
            "linear": BackoffStrategy.LINEAR,
            "fixed": BackoffStrategy.FIXED,
            "constant": BackoffStrategy.FIXED,  # Map constant to fixed
        }.get(backoff, BackoffStrategy.EXPONENTIAL)

        retry_policy = RetryPolicy(
            max_attempts=max_attempts,
            backoff=backoff_strategy,
            base_delay=base_delay,
            max_delay=max_delay,
            retryable_errors=retryable_errors,
        )
        retry_executor = RetryExecutor(retry_policy)

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await retry_executor.execute_async(func, *args, **kwargs)

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return retry_executor.execute_sync(func, *args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def with_circuit_breaker(
    failure_threshold: int = 3, recovery_timeout: float = 30.0, expected_exception: type[Exception] = Exception
) -> Callable[[F], F]:
    """Decorator for circuit breaker protection.

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time to wait before attempting recovery
        expected_exception: Exception type that triggers circuit breaker

    Note: This decorator only supports synchronous functions. For async functions,
    use the AsyncCircuitBreaker directly.
    """

    def decorator(func: F) -> F:
        circuit = SyncCircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
        )

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            return circuit.call(func, *args, **kwargs)

        return sync_wrapper  # type: ignore[return-value]

    return decorator


def with_metrics(operation_name: str) -> Callable[[F], F]:
    """Decorator for automatic metrics collection via structured logging.

    Args:
        operation_name: Name for the operation metrics
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.perf_counter() - start
                    logger.info(
                        f"Operation {operation_name} completed",
                        operation=operation_name,
                        status="success",
                        duration_seconds=duration,
                    )
                    return result
                except Exception as e:
                    duration = time.perf_counter() - start
                    logger.error(
                        f"Operation {operation_name} failed",
                        operation=operation_name,
                        status="error",
                        error=type(e).__name__,
                        duration_seconds=duration,
                    )
                    raise

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    duration = time.perf_counter() - start
                    logger.info(
                        f"Operation {operation_name} completed",
                        operation=operation_name,
                        status="success",
                        duration_seconds=duration,
                    )
                    return result
                except Exception as e:
                    duration = time.perf_counter() - start
                    logger.error(
                        f"Operation {operation_name} failed",
                        operation=operation_name,
                        status="error",
                        error=type(e).__name__,
                        duration_seconds=duration,
                    )
                    raise

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def with_timing(func: F) -> F:
    """Decorator for automatic timing with structured logging.

    Uses foundation's timed_block for consistent timing and logging.
    """
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            from provide.foundation.utils import timed_block

            operation_name = f"{func.__module__}.{func.__name__}"
            with timed_block(logger, operation_name):  # type: ignore[arg-type]
                return await func(*args, **kwargs)

        return async_wrapper  # type: ignore[return-value]
    else:

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            from provide.foundation.utils import timed_block

            operation_name = f"{func.__module__}.{func.__name__}"
            with timed_block(logger, operation_name):  # type: ignore[arg-type]
                return func(*args, **kwargs)

        return sync_wrapper  # type: ignore[return-value]


@asynccontextmanager
async def async_rate_limited(rate: float, burst: int = 10) -> AsyncGenerator[None, None]:
    """Async context manager for rate limiting.

    Args:
        rate: Operations per second
        burst: Maximum burst capacity
    """
    from provide.foundation.utils import TokenBucketRateLimiter

    limiter = TokenBucketRateLimiter(capacity=float(burst), refill_rate=rate)

    # Wait until we're allowed to proceed
    while not await limiter.is_allowed():
        await asyncio.sleep(0.1)  # Small delay before checking again

    yield


class PlatingMetrics:
    """Centralized metrics collection for plating operations via structured logging."""

    @asynccontextmanager
    async def track_operation(self, operation: str, **labels: Any) -> Any:
        """Context manager for tracking operations with labels."""
        start = time.perf_counter()

        try:
            yield
            duration = time.perf_counter() - start
            logger.info(
                f"Plating operation {operation} completed",
                operation=operation,
                status="success",
                duration_seconds=duration,
                **labels,
            )
        except Exception as e:
            duration = time.perf_counter() - start
            logger.error(
                f"Plating operation {operation} failed",
                operation=operation,
                status="error",
                error=type(e).__name__,
                duration_seconds=duration,
                **labels,
            )
            raise


# Global metrics instance
plating_metrics = PlatingMetrics()

# 🍽️📖🔚

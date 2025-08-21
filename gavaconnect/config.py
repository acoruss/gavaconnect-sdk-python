"""
Configuration classes for the GavaConnect SDK.
"""

from dataclasses import dataclass, field


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    base_backoff_s: float = 0.2
    retry_on_status: tuple[int, ...] = (429, 500, 502, 503, 504)


@dataclass(slots=True)
class SDKConfig:
    base_url: str
    connect_timeout_s: float = 5.0
    read_timeout_s: float = 30.0
    total_timeout_s: float = 40.0
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    user_agent: str = "gavaconnect-py/1.0.0"

from __future__ import annotations

import hashlib
import hmac
import threading
import time
from dataclasses import dataclass
from typing import Protocol

from fastapi import HTTPException, Request, status

from app.core.config import Settings, get_settings

RATE_LIMIT_DETAIL = "Too many attempts. Please try again later."


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    name: str
    attempts: int
    window_seconds: int


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    count: int
    retry_after_seconds: int


class RateLimitStore(Protocol):
    def hit(self, key: str, window_seconds: int) -> RateLimitResult: ...

    def clear(self) -> None: ...


class InMemoryRateLimitStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, tuple[int, float]] = {}

    def hit(self, key: str, window_seconds: int) -> RateLimitResult:
        now = time.monotonic()
        with self._lock:
            count, reset_at = self._counters.get(key, (0, now + window_seconds))
            if reset_at <= now:
                count = 0
                reset_at = now + window_seconds
            count += 1
            self._counters[key] = (count, reset_at)
            retry_after = max(1, int(reset_at - now))
        return RateLimitResult(
            allowed=True,
            count=count,
            retry_after_seconds=retry_after,
        )

    def clear(self) -> None:
        with self._lock:
            self._counters.clear()


class RedisRateLimitStore:
    def __init__(self, redis_url: str) -> None:
        from redis import Redis

        self._redis = Redis.from_url(redis_url, decode_responses=True)

    def hit(self, key: str, window_seconds: int) -> RateLimitResult:
        count = int(self._redis.incr(key))
        if count == 1:
            self._redis.expire(key, window_seconds)
            retry_after = window_seconds
        else:
            retry_after = self._redis.ttl(key)
            if retry_after < 1:
                retry_after = window_seconds
                self._redis.expire(key, window_seconds)
        return RateLimitResult(
            allowed=True,
            count=count,
            retry_after_seconds=retry_after,
        )

    def clear(self) -> None:
        return None


class AuthRateLimiter:
    def __init__(self, settings: Settings, store: RateLimitStore) -> None:
        self._settings = settings
        self._store = store

    def enforce(self, *, action: str, request: Request, identifier: str | None) -> None:
        if not self._settings.auth_rate_limit_enabled:
            return

        for rule, key in self._rate_limit_checks(action, request, identifier):
            result = self._store.hit(key, rule.window_seconds)
            if result.count > rule.attempts:
                self._raise_rate_limited(result.retry_after_seconds)

    def reset(self) -> None:
        self._store.clear()

    def _rules_for(self, action: str) -> tuple[RateLimitRule, ...]:
        if action == "login":
            return (
                RateLimitRule(
                    "ip",
                    self._settings.login_rate_limit_ip_attempts,
                    self._settings.login_rate_limit_window_seconds,
                ),
                RateLimitRule(
                    "identifier",
                    self._settings.login_rate_limit_email_attempts,
                    self._settings.login_rate_limit_window_seconds,
                ),
            )
        if action == "password_reset":
            return (
                RateLimitRule(
                    "ip",
                    self._settings.login_rate_limit_ip_attempts,
                    self._settings.login_rate_limit_window_seconds,
                ),
                RateLimitRule(
                    "identifier",
                    self._settings.login_rate_limit_email_attempts,
                    self._settings.login_rate_limit_window_seconds,
                ),
            )
        if action == "register":
            return (
                RateLimitRule(
                    "ip",
                    self._settings.register_rate_limit_ip_attempts,
                    self._settings.register_rate_limit_window_seconds,
                ),
                RateLimitRule(
                    "identifier",
                    self._settings.register_rate_limit_email_attempts,
                    self._settings.register_rate_limit_window_seconds,
                ),
            )
        raise ValueError(f"Unknown rate-limited auth action: {action}")

    def _keys_for(
        self,
        action: str,
        request: Request,
        identifier: str | None,
    ) -> tuple[str, ...]:
        keys = [self._key(action, "ip", self._client_ip(request))]
        if identifier:
            keys.append(self._key(action, "identifier", identifier.strip().lower()))
        return tuple(keys)

    def _rate_limit_checks(
        self,
        action: str,
        request: Request,
        identifier: str | None,
    ) -> tuple[tuple[RateLimitRule, str], ...]:
        rules = self._rules_for(action)
        keys = self._keys_for(action, request, identifier)
        return tuple(zip(rules, keys))

    def _key(self, action: str, scope: str, value: str) -> str:
        digest = hmac.new(
            self._settings.secret_key.encode("utf-8"),
            value.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"auth-rate-limit:{action}:{scope}:{digest}"

    def _client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", maxsplit=1)[0].strip()
        if request.client is None:
            return "unknown"
        return request.client.host

    def _raise_rate_limited(self, retry_after_seconds: int) -> None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=RATE_LIMIT_DETAIL,
            headers={"Retry-After": str(max(1, retry_after_seconds))},
        )


def _build_store(settings: Settings) -> RateLimitStore:
    if settings.auth_rate_limit_backend == "redis":
        if settings.redis_url is None:
            raise RuntimeError("REDIS_URL is required for Redis rate limiting.")
        return RedisRateLimitStore(settings.redis_url)
    return InMemoryRateLimitStore()


_settings = get_settings()
auth_rate_limiter = AuthRateLimiter(_settings, _build_store(_settings))

"""
Advanced API Key Router for Krystal AI Engine.

Features:
- Per-key health tracking (success rate, latency, cooldown on failure)
- Weighted round-robin based on health score
- Automatic cooldown + exponential back-off on failures
- Rate limiting per key (requests/minute)
- Response caching with TTL
- Priority queues (HIGH / NORMAL / LOW)
- Async-safe with threading locks
- Detailed telemetry / stats
- Multi-provider support (Groq, Gemini, OpenAI, Anthropic)

Usage::

    router = APIRouter()
    key = router.get_best_key("groq")          # healthy key, weighted
    router.record_success("groq", key, latency_ms=240)
    router.record_failure("groq", key, error="rate_limit")

    cached = router.get_cached("my_prompt_hash")
    router.set_cache("my_prompt_hash", "response text", ttl=60)
"""

from __future__ import annotations
import sys
import dataclasses

# Python 3.13 ke liye sahi patch
_original_is_type = dataclasses._is_type

def _patched_is_type(ty, cls, ns, name, _is_kw_only):
    if ty is None:
        return False
    return _original_is_type(ty, cls, ns, name, _is_kw_only)

dataclasses._is_type = _patched_is_type
import os
import time
import threading
import hashlib
import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Constants ────────────────────────────────────────────────────────────────

_PROVIDER_PREFIXES: Dict[str, str] = {
    "groq":      "GROQ_KEY_",
    "gemini":    "GEMINI_KEY_",
    "openai":    "OPENAI_KEY_",
    "anthropic": "ANTHROPIC_KEY_",
}

_DEFAULT_RATE_LIMIT = 60          # requests per minute per key
_COOLDOWN_BASE      = 10.0        # seconds — first failure cooldown
_COOLDOWN_MAX       = 300.0       # 5 minutes — max cooldown
_HEALTH_WINDOW      = 20          # last N requests used for health score
_CACHE_MAX_ENTRIES  = 512
_CACHE_DEFAULT_TTL  = 120         # seconds


class Priority(Enum):
    HIGH   = 0
    NORMAL = 1
    LOW    = 2


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class KeyStats:
    key: str
    provider: str
    total_requests: int = 0
    successes:      int = 0
    failures:       int = 0
    total_latency:  float = 0.0    # ms
    last_used:      float = 0.0
    cooldown_until: float = 0.0
    cooldown_count: int   = 0      # consecutive failures
    # Sliding window for recent health
    recent: deque = field(default_factory=lambda: deque(maxlen=_HEALTH_WINDOW))
    # Rate-limiting: timestamps of recent requests
    request_times: deque = field(default_factory=lambda: deque(maxlen=_DEFAULT_RATE_LIMIT))

    @property
    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until

    @property
    def cooldown_remaining(self) -> float:
        return max(0.0, self.cooldown_until - time.time())

    @property
    def health_score(self) -> float:
        """0.0–1.0 — higher is healthier. Used for weighted selection."""
        if not self.recent:
            return 0.85  # Unknown → optimistic start
        wins = sum(1 for r in self.recent if r)
        rate = wins / len(self.recent)
        # Penalise high average latency (>1000ms starts hurting)
        avg_lat = self.avg_latency_ms
        lat_penalty = min(avg_lat / 5000.0, 0.4) if avg_lat > 0 else 0.0
        return max(0.0, rate - lat_penalty)

    @property
    def avg_latency_ms(self) -> float:
        if self.successes == 0:
            return 0.0
        return self.total_latency / self.successes

    @property
    def success_rate(self) -> float:
        total = self.total_requests
        return (self.successes / total) if total > 0 else 1.0

    def is_rate_limited(self, rpm: int = _DEFAULT_RATE_LIMIT) -> bool:
        now = time.time()
        # Purge timestamps older than 60s
        while self.request_times and now - self.request_times[0] > 60.0:
            self.request_times.popleft()
        return len(self.request_times) >= rpm

    def record_request(self) -> None:
        self.request_times.append(time.time())
        self.total_requests += 1
        self.last_used = time.time()

    def to_dict(self) -> dict:
        return {
            "provider":          self.provider,
            "key_hint":          f"{self.key[:8]}…" if len(self.key) > 8 else self.key,
            "total_requests":    self.total_requests,
            "successes":         self.successes,
            "failures":          self.failures,
            "success_rate":      round(self.success_rate, 3),
            "health_score":      round(self.health_score, 3),
            "avg_latency_ms":    round(self.avg_latency_ms, 1),
            "is_available":      self.is_available,
            "cooldown_remaining": round(self.cooldown_remaining, 1),
            "cooldown_count":    self.cooldown_count,
        }


@dataclass
class CacheEntry:
    value: str
    expires: float

    def is_alive(self) -> bool:
        return time.time() < self.expires


@dataclass
class RoutingRequest:
    prompt_hash: str
    provider: str
    priority: Priority
    timestamp: float = field(default_factory=time.time)


# ─── Main Router ──────────────────────────────────────────────────────────────

class APIRouter:
    """
    Central API key router with health awareness, rate limiting,
    exponential back-off, caching, and telemetry.
    """

    def __init__(self, env_path: Optional[str | Path] = None) -> None:
        self._lock   = threading.RLock()
        self._stats:  Dict[str, Dict[str, KeyStats]] = defaultdict(dict)  # provider → key → stats
        self._cache:  Dict[str, CacheEntry] = {}
        self._queue:  deque = deque()    # RoutingRequest queue (FIFO by priority order)

        # Telemetry counters
        self._global_requests  = 0
        self._global_successes = 0
        self._global_cache_hits = 0

        # Load environment
        root_env = Path(__file__).resolve().parent.parent / ".env"
        self._ingest_env_file(root_env)
        if env_path is not None:
            self._ingest_env_file(Path(env_path))

        # Discover keys for all providers
        for provider, prefix in _PROVIDER_PREFIXES.items():
            self._discover_keys(provider, prefix)

    # ── ENV loading ────────────────────────────────────────────────────────

    @staticmethod
    def _ingest_env_file(path: Path) -> None:
        if not path.exists():
            return
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip(); v = v.strip()
                if k:
                    os.environ[k] = v

    def _discover_keys(self, provider: str, prefix: str) -> None:
        found = []
        for name, value in sorted(os.environ.items()):
            if name.startswith(prefix) and value.strip():
                found.append(value.strip())
        with self._lock:
            for key in found:
                if key not in self._stats[provider]:
                    self._stats[provider][key] = KeyStats(key=key, provider=provider)

    # ── Key selection ───────────────────────────────────────────────────────

    def get_best_key(
        self,
        provider: str,
        rpm: int = _DEFAULT_RATE_LIMIT,
    ) -> str:
        """
        Return the healthiest available key for ``provider``.

        Selection order:
        1. Skip unavailable (cooldown) and rate-limited keys.
        2. Among eligible keys, pick by weighted random (health_score).
        3. Fall back to least-recently-used if all scores equal.

        Raises ``RuntimeError`` if no eligible key exists.
        """
        with self._lock:
            candidates = self._eligible_keys(provider, rpm)
            if not candidates:
                # Try to find a key regardless of rate-limit as last resort
                all_avail = [s for s in self._stats[provider].values() if s.is_available]
                if not all_avail:
                    raise RuntimeError(
                        f"No available keys for provider '{provider}'. "
                        f"All keys are either missing or in cooldown."
                    )
                # Pick the one with shortest cooldown remaining (should be 0 here)
                candidates = sorted(all_avail, key=lambda s: s.cooldown_remaining)

            chosen = self._weighted_choice(candidates)
            chosen.record_request()
            self._global_requests += 1
            return chosen.key

    def _eligible_keys(self, provider: str, rpm: int) -> List[KeyStats]:
        return [
            s for s in self._stats[provider].values()
            if s.is_available and not s.is_rate_limited(rpm)
        ]

    @staticmethod
    def _weighted_choice(candidates: List[KeyStats]) -> KeyStats:
        """Weighted random selection based on health_score."""
        total = sum(max(s.health_score, 0.01) for s in candidates)
        import random
        r = random.uniform(0, total)
        cumulative = 0.0
        for s in candidates:
            cumulative += max(s.health_score, 0.01)
            if r <= cumulative:
                return s
        return candidates[-1]

    # ── Outcome recording ───────────────────────────────────────────────────

    def record_success(self, provider: str, key: str, latency_ms: float = 0.0) -> None:
        with self._lock:
            stats = self._get_or_create(provider, key)
            stats.successes       += 1
            stats.total_latency   += latency_ms
            stats.cooldown_count   = 0          # reset consecutive failures
            stats.cooldown_until   = 0.0
            stats.recent.append(True)
            self._global_successes += 1

    def record_failure(
        self,
        provider: str,
        key: str,
        error: str = "",
        permanent: bool = False,
    ) -> None:
        """
        Record a failure and apply exponential back-off.

        Args:
            provider:  Provider name.
            key:       The key that failed.
            error:     Error type hint (e.g. 'rate_limit', 'auth', 'timeout').
            permanent: If True, puts the key in a very long cooldown (1 hour).
        """
        with self._lock:
            stats = self._get_or_create(provider, key)
            stats.failures       += 1
            stats.cooldown_count += 1
            stats.recent.append(False)

            if permanent or "auth" in error.lower() or "invalid" in error.lower():
                # Treat auth errors as long-term disqualification
                stats.cooldown_until = time.time() + 3600.0
            elif "rate" in error.lower():
                # Rate-limit: cool down for a minute
                stats.cooldown_until = time.time() + 60.0
            else:
                # Generic exponential back-off
                backoff = min(
                    _COOLDOWN_BASE * (2 ** (stats.cooldown_count - 1)),
                    _COOLDOWN_MAX,
                )
                stats.cooldown_until = time.time() + backoff

    def _get_or_create(self, provider: str, key: str) -> KeyStats:
        if key not in self._stats[provider]:
            self._stats[provider][key] = KeyStats(key=key, provider=provider)
        return self._stats[provider][key]

    # ── Caching ─────────────────────────────────────────────────────────────

    def cache_key(self, prompt: str, provider: str = "", model: str = "") -> str:
        """Generate a stable cache key from prompt + optional context."""
        raw = f"{provider}:{model}:{prompt}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def get_cached(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._cache.get(key)
            if entry and entry.is_alive():
                self._global_cache_hits += 1
                return entry.value
            if entry:
                del self._cache[key]  # Expired
        return None

    def set_cache(self, key: str, value: str, ttl: float = _CACHE_DEFAULT_TTL) -> None:
        with self._lock:
            # Evict oldest if full
            if len(self._cache) >= _CACHE_MAX_ENTRIES:
                oldest = min(self._cache, key=lambda k: self._cache[k].expires)
                del self._cache[oldest]
            self._cache[key] = CacheEntry(value=value, expires=time.time() + ttl)

    def invalidate_cache(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def _evict_expired_cache(self) -> int:
        now = time.time()
        expired = [k for k, v in self._cache.items() if not v.is_alive()]
        for k in expired:
            del self._cache[k]
        return len(expired)

    # ── Priority queue ───────────────────────────────────────────────────────

    def enqueue(
        self,
        prompt_hash: str,
        provider: str,
        priority: Priority = Priority.NORMAL,
    ) -> None:
        req = RoutingRequest(prompt_hash=prompt_hash, provider=provider, priority=priority)
        with self._lock:
            self._queue.append(req)
            # Sort by priority (lower value = higher priority), stable
            sorted_q = sorted(self._queue, key=lambda r: (r.priority.value, r.timestamp))
            self._queue.clear()
            self._queue.extend(sorted_q)

    def dequeue(self) -> Optional[RoutingRequest]:
        with self._lock:
            return self._queue.popleft() if self._queue else None

    def queue_depth(self) -> int:
        return len(self._queue)

    # ── Telemetry ────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            provider_stats: Dict[str, Any] = {}
            for provider, key_map in self._stats.items():
                provider_stats[provider] = {
                    "key_count":     len(key_map),
                    "available":     sum(1 for s in key_map.values() if s.is_available),
                    "avg_health":    round(
                        sum(s.health_score for s in key_map.values()) / max(len(key_map), 1), 3
                    ),
                    "keys":          [s.to_dict() for s in key_map.values()],
                }
            return {
                "global_requests":   self._global_requests,
                "global_successes":  self._global_successes,
                "global_cache_hits": self._global_cache_hits,
                "global_success_rate": round(
                    self._global_successes / max(self._global_requests, 1), 3
                ),
                "cache_size":        len(self._cache),
                "queue_depth":       len(self._queue),
                "providers":         provider_stats,
            }

    def get_provider_summary(self, provider: str) -> Dict[str, Any]:
        with self._lock:
            key_map = self._stats.get(provider, {})
            return {
                "provider":   provider,
                "key_count":  len(key_map),
                "available":  sum(1 for s in key_map.values() if s.is_available),
                "keys":       [s.to_dict() for s in key_map.values()],
            }

    def has_keys(self, provider: str) -> bool:
        return bool(self._stats.get(provider))

    def available_providers(self) -> List[str]:
        with self._lock:
            return [
                p for p, km in self._stats.items()
                if any(s.is_available for s in km.values())
            ]

    # ── Convenience: per-provider shortcuts ──────────────────────────────────

    def get_groq_key(self, rpm: int = _DEFAULT_RATE_LIMIT) -> str:
        return self.get_best_key("groq", rpm)

    def get_gemini_key(self, rpm: int = _DEFAULT_RATE_LIMIT) -> str:
        return self.get_best_key("gemini", rpm)

    def get_openai_key(self, rpm: int = _DEFAULT_RATE_LIMIT) -> str:
        return self.get_best_key("openai", rpm)

    def get_anthropic_key(self, rpm: int = _DEFAULT_RATE_LIMIT) -> str:
        return self.get_best_key("anthropic", rpm)

    # ── Context manager for timed calls ─────────────────────────────────────

    def call(self, provider: str, rpm: int = _DEFAULT_RATE_LIMIT) -> "_KeyContext":
        """
        Usage::

            with router.call("groq") as key:
                response = groq_client.chat(key, ...)
        """
        return _KeyContext(self, provider, rpm)

    def __repr__(self) -> str:
        providers = list(self._stats.keys())
        total_keys = sum(len(v) for v in self._stats.values())
        return f"<APIRouter providers={providers} keys={total_keys}>"


# ── Context manager ────────────────────────────────────────────────────────────

class _KeyContext:
    """Auto-records success/failure + latency for a key call."""

    def __init__(self, router: APIRouter, provider: str, rpm: int) -> None:
        self._router   = router
        self._provider = provider
        self._rpm      = rpm
        self._key:     str   = ""
        self._start:   float = 0.0
        self._failed:  bool  = False
        self._error:   str   = ""

    def __enter__(self) -> str:
        self._key   = self._router.get_best_key(self._provider, self._rpm)
        self._start = time.time()
        return self._key

    def fail(self, error: str = "", permanent: bool = False) -> None:
        self._failed  = True
        self._error   = error

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        latency = (time.time() - self._start) * 1000.0  # ms
        if exc_type is not None or self._failed:
            error_hint = self._error or (str(exc_val) if exc_val else "")
            self._router.record_failure(self._provider, self._key, error=error_hint)
            return False  # Re-raise exception
        self._router.record_success(self._provider, self._key, latency_ms=latency)
        return False


# ── Legacy KeyManager shim ─────────────────────────────────────────────────────
# Drop-in replacement for the original KeyManager so existing code doesn't break.

class KeyManager:
    """
    Backward-compatible wrapper around ``APIRouter``.

    Old code that called ``KeyManager().get_next_groq_key()`` will continue
    to work without modification.
    """

    def __init__(self, env_path: Optional[str | Path] = None) -> None:
        self._router = APIRouter(env_path=env_path)

    # ── Original interface ──────────────────────────────────────────────────

    def has_keys(self) -> bool:
        return bool(self._router.available_providers())

    def has_groq_keys(self) -> bool:
        return self._router.has_keys("groq")

    def has_gemini_keys(self) -> bool:
        return self._router.has_keys("gemini")

    @property
    def key_count(self) -> int:
        return sum(len(v) for v in self._router._stats.values())

    @property
    def groq_key_count(self) -> int:
        return len(self._router._stats.get("groq", {}))

    @property
    def gemini_key_count(self) -> int:
        return len(self._router._stats.get("gemini", {}))

    def get_next_groq_key(self) -> str:
        return self._router.get_groq_key()

    def get_next_gemini_key(self) -> str:
        return self._router.get_gemini_key()

    def get_next_key(self) -> str:
        for provider in ("groq", "gemini", "openai", "anthropic"):
            try:
                return self._router.get_best_key(provider)
            except RuntimeError:
                continue
        raise RuntimeError(
            "No API keys found for any provider. "
            "Add GROQ_KEY_1, GEMINI_KEY_1, etc. to your .env file."
        )

    def peek_next_key(self) -> str:
        """Return the best key without recording a request."""
        for provider in ("groq", "gemini", "openai", "anthropic"):
            with self._router._lock:
                candidates = self._router._eligible_keys(provider, _DEFAULT_RATE_LIMIT)
                if candidates:
                    return self._router._weighted_choice(candidates).key
        raise RuntimeError("No API keys available.")

    # ── Extra power exposed from the new router ─────────────────────────────

    @property
    def router(self) -> APIRouter:
        """Direct access to the underlying ``APIRouter`` for advanced use."""
        return self._router

    def stats(self) -> dict:
        return self._router.get_stats()
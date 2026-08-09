"""Per-client rate limiting for the public API.

The deployed service runs with ``--max-instances 1``, so an in-process sliding
window is an accurate global limit rather than a per-replica approximation. If
the service is ever scaled past one instance this needs to move to a shared
store (Redis, or a Postgres table) — the limits become per-instance otherwise.
"""

import secrets
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

# How many requests a single client may make in a window. The budgets are sized
# by what each endpoint costs us: LLM tokens > database writes > reads.
_IDLE_EVICTION_SECONDS = 900.0


@dataclass(frozen=True)
class Rule:
    limit: int
    window_seconds: float


@dataclass(frozen=True)
class Decision:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int
    window_seconds: float = 0.0


# Longest prefix wins, so "/auth/signin" beats a hypothetical "/auth".
_RULES: dict[str, Rule] = {
    # Every call spends LLM tokens.
    "/chat": Rule(limit=15, window_seconds=3600.0),
    # Writes to the database and shells out to the scraper; admin-key gated.
    "/ingest": Rule(limit=3, window_seconds=3600.0),
    # Read-only, but /search runs the cross-encoder on 4 vCPU.
    "/search": Rule(limit=30, window_seconds=60.0),
    "/feedback": Rule(limit=20, window_seconds=60.0),
    "/startups": Rule(limit=60, window_seconds=60.0),
}

# Liveness probes must never be throttled.
_UNLIMITED = frozenset({"/health", "/docs", "/openapi.json", "/redoc"})

_DEFAULT_RULE = Rule(limit=60, window_seconds=60.0)


def rule_for_path(path: str) -> Rule | None:
    """The rule governing ``path``, or None when the path is never limited."""
    if path in _UNLIMITED:
        return None
    if path in _RULES:
        return _RULES[path]
    matches = [p for p in _RULES if path.startswith(p + "/")]
    if matches:
        return _RULES[max(matches, key=len)]
    return _DEFAULT_RULE


def client_ip(
    forwarded_for: str | None, peer: str | None, trusted_hops: int
) -> str:
    """Resolve the caller's address from the X-Forwarded-For chain.

    Only the rightmost ``trusted_hops`` entries were written by infrastructure we
    control; anything further left is attacker-controlled and must not be used as
    a limiter key. On Cloud Run exactly one hop is appended, so the caller sits
    second from the right.
    """
    if trusted_hops <= 0 or not forwarded_for:
        return peer or "unknown"
    parts = [p.strip() for p in forwarded_for.split(",") if p.strip()]
    if not parts:
        return peer or "unknown"
    index = len(parts) - 1 - trusted_hops
    if index < 0:
        # Fewer entries than expected: fall back to the leftmost we were given.
        return parts[0]
    return parts[index]


def resolve_client(
    *,
    proxy_client_ip: str | None,
    proxy_secret_header: str | None,
    proxy_secret: str | None,
    forwarded_for: str | None,
    peer: str | None,
    trusted_hops: int,
) -> str:
    """Identify the caller, trusting the web app's proxy only when it proves itself.

    The Next.js app calls this API server-side, so without a forwarded address
    every browser looks like the same one or two hosting egress IPs and a single
    visitor could exhaust the budget for everyone. The forwarded address is only
    honoured when the caller knows the shared secret; otherwise anyone could
    send a fresh address per request and never be limited at all.
    """
    if proxy_secret and proxy_client_ip and proxy_secret_header:
        if secrets.compare_digest(proxy_secret_header, proxy_secret):
            return proxy_client_ip
    return client_ip(forwarded_for, peer, trusted_hops)


class RateLimiter:
    def __init__(
        self,
        default: Rule = _DEFAULT_RULE,
        rules: dict[str, Rule] | None = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._default = default
        # Policy is injected rather than read from the module table so the
        # limiter stays a plain mechanism that is easy to test in isolation.
        self._rules = rules if rules is not None else {}
        self._clock = clock
        self._hits: dict[tuple[str, str], deque[float]] = {}
        self._last_seen: dict[str, float] = {}

    def _rule(self, path: str) -> Rule | None:
        if path in _UNLIMITED:
            return None
        if path in self._rules:
            return self._rules[path]
        matches = [p for p in self._rules if path.startswith(p + "/")]
        if matches:
            return self._rules[max(matches, key=len)]
        return self._default

    def _evict_idle(self, now: float) -> None:
        stale = [
            client
            for client, seen in self._last_seen.items()
            if now - seen > _IDLE_EVICTION_SECONDS
        ]
        for client in stale:
            del self._last_seen[client]
        if stale:
            dropped = set(stale)
            self._hits = {
                key: hits for key, hits in self._hits.items() if key[0] not in dropped
            }

    def tracked_clients(self) -> int:
        return len(self._last_seen)

    def check(self, client: str, path: str) -> Decision:
        rule = self._rule(path)
        now = self._clock()
        self._evict_idle(now)
        self._last_seen[client] = now

        if rule is None:
            return Decision(allowed=True, limit=0, remaining=0, retry_after=0)

        hits = self._hits.setdefault((client, path), deque())
        cutoff = now - rule.window_seconds
        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= rule.limit:
            # The oldest hit is the one whose expiry frees the next slot.
            retry_after = max(1, int(round(hits[0] + rule.window_seconds - now)))
            return Decision(
                allowed=False,
                limit=rule.limit,
                remaining=0,
                retry_after=retry_after,
                window_seconds=rule.window_seconds,
            )

        hits.append(now)
        return Decision(
            allowed=True,
            limit=rule.limit,
            remaining=rule.limit - len(hits),
            retry_after=0,
            window_seconds=rule.window_seconds,
        )

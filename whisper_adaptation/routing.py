from __future__ import annotations


def choose_adapter(domain: str, routing: dict[str, str], default: str = "base") -> str:
    """Return a declared candidate; this is not a quality or deployment claim."""
    return routing.get(domain, default)

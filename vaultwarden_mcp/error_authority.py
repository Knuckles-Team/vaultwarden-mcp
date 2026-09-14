#!/usr/bin/python
"""One representation authority for agent-readable HTTP errors.

The generated module is deliberately framework-neutral.  HTTP, MCP, and A2A
adapters construct one :class:`ProblemDetails` value and negotiate only its
representation; they do not independently translate exceptions or retry
metadata.  Browser HTML remains available, but agent clients receive RFC 9457
JSON or structured Markdown when they ask for it.
"""

from __future__ import annotations

import html
import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from agent_utilities.security.persistence_privacy import sanitize_for_persistence

PROBLEM_JSON_MEDIA_TYPE = "application/problem+json"
STRUCTURED_MARKDOWN_MEDIA_TYPE = "text/markdown"
BROWSER_HTML_MEDIA_TYPE = "text/html"
AGENT_ERROR_ACCEPT = (
    f"{PROBLEM_JSON_MEDIA_TYPE}, "
    f"{STRUCTURED_MARKDOWN_MEDIA_TYPE};q=0.9, "
    f"{BROWSER_HTML_MEDIA_TYPE};q=0.5"
)
MAX_DETAIL_CHARS = 2048
MAX_INSTANCE_CHARS = 512
MAX_TYPE_CHARS = 256
MAX_RETRY_AFTER_S = 3600.0

_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,63}$")
_DENIAL_CODES = frozenset(
    {
        "access_denied",
        "authentication_required",
        "forbidden",
        "not_authorized",
        "permission_denied",
        "policy_denied",
        "unauthorized",
    }
)
_DEFAULT_TITLES = {
    "dependency_unavailable": "Dependency unavailable",
    "engine_degraded": "Service temporarily unavailable",
    "invalid_request": "Invalid request",
    "operation_failed": "Operation failed",
    "permission_denied": "Permission denied",
}
_METADATA_FIELDS = (
    "status",
    "code",
    "type",
    "instance",
    "retryable",
    "retry_after_s",
)


def _safe_text(value: Any, *, limit: int, fallback: str) -> str:
    """Sanitize and bound text before it crosses a public response boundary."""
    candidate = "" if isinstance(value, BaseException) else str(value or "")
    sanitized, _ = sanitize_for_persistence(candidate)
    text = str(sanitized).replace("\x00", "").strip()
    return text[:limit] or fallback


def _safe_code(value: Any) -> str:
    candidate = str(value or "operation_failed").strip().lower()
    return candidate if _CODE_RE.fullmatch(candidate) else "operation_failed"


def _bounded_retry_after(value: Any) -> float | None:
    if value is None:
        return None
    try:
        retry_after = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(retry_after) or retry_after < 0:
        return None
    return min(retry_after, MAX_RETRY_AFTER_S)


@dataclass(frozen=True)
class ProblemDetails:
    """Canonical RFC 9457 problem details plus agent retry metadata."""

    status: int
    code: str
    instance: str
    detail: str
    type_uri: str = ""
    title: str = ""
    retryable: bool = False
    retry_after_s: float | None = None

    def __post_init__(self) -> None:
        status = int(self.status)
        if not 100 <= status <= 599:
            raise ValueError("problem status must be between 100 and 599")

        code = _safe_code(self.code)
        denied = status in {401, 403} or code in _DENIAL_CODES
        type_uri = _safe_text(
            self.type_uri,
            limit=MAX_TYPE_CHARS,
            fallback=f"urn:agent-error:{code}",
        )
        instance = _safe_text(
            self.instance,
            limit=MAX_INSTANCE_CHARS,
            fallback="urn:agent-error-instance:unknown",
        )
        title = _safe_text(
            self.title,
            limit=256,
            fallback=_DEFAULT_TITLES.get(code, "Operation failed"),
        )
        detail = _safe_text(
            self.detail,
            limit=MAX_DETAIL_CHARS,
            fallback="The request could not be completed.",
        )
        retryable = bool(self.retryable) and not denied
        retry_after_s = _bounded_retry_after(self.retry_after_s) if retryable else None

        object.__setattr__(self, "status", status)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "type_uri", type_uri)
        object.__setattr__(self, "instance", instance)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "detail", detail)
        object.__setattr__(self, "retryable", retryable)
        object.__setattr__(self, "retry_after_s", retry_after_s)

    def metadata(self) -> dict[str, Any]:
        """Return the representation-invariant agent metadata."""
        return {
            "status": self.status,
            "code": self.code,
            "type": self.type_uri,
            "instance": self.instance,
            "retryable": self.retryable,
            "retry_after_s": self.retry_after_s,
        }

    def as_dict(self) -> dict[str, Any]:
        """Return an RFC 9457-compatible object with stable extension fields."""
        return {
            "type": self.type_uri,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance,
            "code": self.code,
            "retryable": self.retryable,
            "retry_after_s": self.retry_after_s,
        }

    def to_json(self) -> str:
        return json.dumps(
            self.as_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )

    def to_markdown(self) -> str:
        """Render structured Markdown from the same metadata object as JSON."""
        metadata = self.metadata()
        lines = ["---"]
        for field in _METADATA_FIELDS:
            rendered = json.dumps(metadata[field], ensure_ascii=False)
            lines.append(f"{field}: {rendered}")
        lines.extend(
            [
                "---",
                f"# {self.title}",
                "",
                "## Detail",
            ]
        )
        lines.extend(f"> {line}" if line else ">" for line in self.detail.splitlines())
        return "\n".join(lines) + "\n"

    def to_html(self) -> str:
        """Render the retained browser surface with escaped bounded fields."""
        metadata = self.metadata()
        attrs = " ".join(
            'data-error-{}="{}"'.format(
                field.replace("_", "-"), html.escape(str(value), quote=True)
            )
            for field, value in metadata.items()
        )
        detail = html.escape(self.detail, quote=False).replace("\n", "<br>")
        return (
            '<!doctype html>\n<html lang="en"><head>'
            f'<meta name="error-status" content="{self.status}">'
            f"<title>{html.escape(self.title)}</title></head>\n"
            f"<body><main {attrs}><h1>{html.escape(self.title)}</h1>"
            f"<p>{detail}</p></main></body></html>\n"
        )


@dataclass(frozen=True)
class RenderedError:
    """A transport-neutral response ready for an HTTP/MCP adapter."""

    status_code: int
    media_type: str
    body: str
    headers: Mapping[str, str]


def _accept_quality(accept: str, offered: str) -> tuple[float, int, int]:
    """Return q, specificity, and source order for one offered media type."""
    best_match = (-1, 0.0, -10_000)
    for order, item in enumerate(accept.split(",")):
        bits = [part.strip() for part in item.split(";")]
        media_range = bits[0].lower()
        try:
            quality = next(
                float(part.split("=", 1)[1].strip())
                for part in bits[1:]
                if part.lower().startswith("q=")
            )
        except (StopIteration, ValueError):
            quality = 1.0
        if not 0.0 <= quality <= 1.0:
            continue
        if media_range == offered:
            specificity = 2
        elif media_range == "*/*" or media_range == offered.split("/", 1)[0] + "/*":
            specificity = 1
        else:
            continue
        candidate = (specificity, quality, -order)
        if candidate > best_match:
            best_match = candidate
    specificity, quality, source_order = best_match
    return quality, specificity, source_order


def negotiate_media_type(accept: str | None) -> str:
    """Prefer agent formats, while retaining HTML for browser Accept headers."""
    if not accept or not accept.strip():
        return PROBLEM_JSON_MEDIA_TYPE
    offered = (
        PROBLEM_JSON_MEDIA_TYPE,
        STRUCTURED_MARKDOWN_MEDIA_TYPE,
        BROWSER_HTML_MEDIA_TYPE,
    )
    ranked = [
        (*_accept_quality(accept, media_type), -priority, media_type)
        for priority, media_type in enumerate(offered)
    ]
    supported = [candidate for candidate in ranked if candidate[0] > 0]
    return max(supported)[-1] if supported else PROBLEM_JSON_MEDIA_TYPE


def render_error(
    problem: ProblemDetails, *, accept: str | None = None
) -> RenderedError:
    """Negotiate one bounded representation without changing its semantics."""
    media_type = negotiate_media_type(accept)
    if media_type == STRUCTURED_MARKDOWN_MEDIA_TYPE:
        body = problem.to_markdown()
    elif media_type == BROWSER_HTML_MEDIA_TYPE:
        body = problem.to_html()
    else:
        media_type = PROBLEM_JSON_MEDIA_TYPE
        body = problem.to_json()
    headers = {
        "Content-Type": f"{media_type}; charset=utf-8",
        "Vary": "Accept",
    }
    if problem.retry_after_s is not None:
        headers["Retry-After"] = str(problem.retry_after_s)
    return RenderedError(
        status_code=problem.status,
        media_type=media_type,
        body=body,
        headers=headers,
    )


def error_response(
    *,
    status: int,
    code: str,
    instance: str,
    detail: str,
    type_uri: str = "",
    title: str = "",
    retryable: bool = False,
    retry_after_s: float | None = None,
    accept: str | None = None,
) -> RenderedError:
    """Construct and render a problem through the single package authority."""
    return render_error(
        ProblemDetails(
            status=status,
            code=code,
            instance=instance,
            detail=detail,
            type_uri=type_uri,
            title=title,
            retryable=retryable,
            retry_after_s=retry_after_s,
        ),
        accept=accept,
    )


__all__ = [
    "BROWSER_HTML_MEDIA_TYPE",
    "AGENT_ERROR_ACCEPT",
    "MAX_DETAIL_CHARS",
    "PROBLEM_JSON_MEDIA_TYPE",
    "ProblemDetails",
    "RenderedError",
    "STRUCTURED_MARKDOWN_MEDIA_TYPE",
    "error_response",
    "negotiate_media_type",
    "render_error",
]

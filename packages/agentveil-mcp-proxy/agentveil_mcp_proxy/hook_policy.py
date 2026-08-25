# SPDX-FileCopyrightText: 2026 Oleg Boiko
# SPDX-License-Identifier: BUSL-1.1

"""Shared connector-neutral policy outcome for native client hooks."""

from __future__ import annotations

from enum import Enum

from agentveil_mcp_proxy.policy import PolicyDecision, PolicyEvaluation


AGENTVEIL_CONTROLLED_MCP_SERVER = "agentveil-mcp-proxy"
AGENTVEIL_CONTROLLED_MCP_SERVER_ALIASES = frozenset({
    AGENTVEIL_CONTROLLED_MCP_SERVER,
    AGENTVEIL_CONTROLLED_MCP_SERVER.replace("-", "_"),
})


class HookDisposition(str, Enum):
    """Bounded outcome shared by native hook adapters."""

    ALLOW = "allow"
    REDIRECT = "redirect"
    HARD_BLOCK = "hard_block"


def resolve_hook_disposition(
    evaluation: PolicyEvaluation,
    *,
    controlled_route_call: bool = False,
    native_write_redirect_supported: bool = False,
    redirect_route_ready: bool = False,
) -> HookDisposition:
    """Resolve one policy evaluation without inventing hook-side approval."""

    if controlled_route_call:
        return HookDisposition.ALLOW
    if evaluation.decision in (PolicyDecision.ALLOW, PolicyDecision.OBSERVE):
        return HookDisposition.ALLOW
    if (
        evaluation.decision is PolicyDecision.APPROVAL
        and evaluation.risk_class.value == "write"
        and native_write_redirect_supported
        and redirect_route_ready
    ):
        return HookDisposition.REDIRECT
    return HookDisposition.HARD_BLOCK


def is_agentveil_controlled_mcp_server(server: str) -> bool:
    """Return True when a normalized MCP server label is the AgentVeil route."""

    return server in AGENTVEIL_CONTROLLED_MCP_SERVER_ALIASES


def resolve_native_hook_disposition_on_deny(
    evaluation: PolicyEvaluation,
    *,
    native_tool: str,
    redirect_route_ready: bool,
) -> HookDisposition:
    """Resolve deny-path disposition using shared redirect readiness rules."""

    from agentveil_mcp_proxy.client_guidance import native_write_redirect_supported

    return resolve_hook_disposition(
        evaluation,
        native_write_redirect_supported=native_write_redirect_supported(
            native_tool=native_tool,
        ),
        redirect_route_ready=redirect_route_ready,
    )


__all__ = [
    "AGENTVEIL_CONTROLLED_MCP_SERVER",
    "AGENTVEIL_CONTROLLED_MCP_SERVER_ALIASES",
    "HookDisposition",
    "is_agentveil_controlled_mcp_server",
    "resolve_hook_disposition",
    "resolve_native_hook_disposition_on_deny",
]

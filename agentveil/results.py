"""Typed SDK result objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional


ControlledActionStatus = Literal["executed", "approval_required", "blocked"]


@dataclass(frozen=True)
class ControlledActionOutcome:
    """Result returned by AVPAgent.controlled_action.

    The object exposes typed attributes for IDEs and static tooling. It also
    supports light dict-style access for ergonomic migration from examples.
    """

    status: ControlledActionStatus
    decision: Optional[dict[str, Any]] = None
    receipt_jcs: Optional[str] = None
    receipt: Optional[dict[str, Any]] = None
    approval: Optional[dict[str, Any]] = None
    reason: Optional[str] = None
    audit_id: Optional[str] = None
    approval_id: Optional[str] = None

    def __getitem__(self, key: str) -> Any:
        if not hasattr(self, key):
            raise KeyError(key)
        value = getattr(self, key)
        if value is None:
            raise KeyError(key)
        return value

    def get(self, key: str, default: Any = None) -> Any:
        if not hasattr(self, key):
            return default
        value = getattr(self, key)
        return default if value is None else value

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"status": self.status}
        for key in (
            "decision",
            "receipt_jcs",
            "receipt",
            "approval",
            "reason",
            "audit_id",
            "approval_id",
        ):
            value = getattr(self, key)
            if value is not None:
                data[key] = value
        return data


__all__ = ["ControlledActionOutcome", "ControlledActionStatus"]

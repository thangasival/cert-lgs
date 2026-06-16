from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Certificate:
    name: str
    valid: bool
    reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

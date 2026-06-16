from __future__ import annotations

from cert_lgs.certification.certificates import Certificate
from cert_lgs.planner.types import Plan


class PlanValidator:
    """Validates returned plans."""

    def validate(self, plan: Plan) -> Certificate:
        if not plan.steps:
            return Certificate(name="plan_validation", valid=False, reason="empty plan")
        if any(step.cost < 0 for step in plan.steps):
            return Certificate(name="plan_validation", valid=False, reason="negative plan-step cost")
        return Certificate(
            name="plan_validation",
            valid=True,
            reason="placeholder plan accepted",
            metadata={"cost": plan.cost, "length": len(plan.steps)},
        )

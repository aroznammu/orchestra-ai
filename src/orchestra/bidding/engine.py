"""Bidding engine -- state machine managing autonomy phase transitions.

Three autonomy phases:
  1. Hard Guardrail (default) -- human approval for everything
  2. Semi-Autonomous -- auto-adjust within capped ranges
  3. Controlled Autonomous -- advanced users, still bounded

Transitions require data maturity + verified profitability + audit trail.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import structlog
from pydantic import BaseModel, Field

from orchestra.core.exceptions import BudgetExceededError

logger = structlog.get_logger("bidding.engine")


class AutonomyPhase(str, Enum):
    HARD_GUARDRAIL = "hard_guardrail"
    SEMI_AUTONOMOUS = "semi_autonomous"
    CONTROLLED_AUTONOMOUS = "controlled_autonomous"


class BiddingAction(str, Enum):
    CREATE_CAMPAIGN = "create_campaign"
    ADJUST_BID = "adjust_bid"
    INCREASE_BUDGET = "increase_budget"
    DECREASE_BUDGET = "decrease_budget"
    REALLOCATE_BUDGET = "reallocate_budget"
    PAUSE_CAMPAIGN = "pause_campaign"
    RESUME_CAMPAIGN = "resume_campaign"
    CHANGE_AUDIENCE = "change_audience"


class TransitionRequirements(BaseModel):
    """Requirements for moving to a higher autonomy phase."""

    min_days_active: int = 90
    min_positive_roi_cycles: int = 3
    anomaly_detection_validated: bool = False
    customer_opt_in: bool = False
    legal_acknowledgement: bool = False
    owner_manual_enable: bool = False


class PhaseTransitionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    from_phase: AutonomyPhase
    to_phase: AutonomyPhase
    approved_by: str
    reason: str
    requirements_met: dict[str, bool] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class BiddingDecision(BaseModel):
    """Record of a bidding decision with full audit trail."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    action: BiddingAction
    platform: str
    campaign_id: str | None = None
    current_value: float = 0.0
    proposed_value: float = 0.0
    change_pct: float = 0.0
    requires_approval: bool = True
    approved: bool = False
    approved_by: str | None = None
    reasoning: str = ""
    risk_score: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# Thresholds that trigger approval requirements in hard guardrail mode
HARD_GUARDRAIL_THRESHOLDS = {
    "budget_change_pct": 10.0,    # >10% budget change needs approval
    "bid_increase_pct": 15.0,     # >15% bid increase needs approval
    "max_daily_spend": 500.0,     # $500/day default cap
    "max_campaign_budget": 5000.0, # $5000 per campaign
}

SEMI_AUTO_THRESHOLDS = {
    "budget_change_pct": 25.0,    # auto-adjust up to 25%
    "bid_increase_pct": 20.0,     # auto-adjust bids up to 20%
    "max_daily_spend": 2000.0,
    "max_campaign_budget": 10000.0,
}


class BiddingEngine:
    """State machine for guardrailed bidding."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self.phase = AutonomyPhase.HARD_GUARDRAIL
        self._transition_history: list[PhaseTransitionRecord] = []
        self._decision_history: list[BiddingDecision] = []
        self._daily_spend: float = 0.0
        self._kill_switch_active: bool = False

    def evaluate_action(
        self,
        action: BiddingAction,
        platform: str,
        current_value: float,
        proposed_value: float,
        campaign_id: str | None = None,
        reasoning: str = "",
    ) -> BiddingDecision:
        """Evaluate whether a bidding action is allowed under current phase."""
        if self._kill_switch_active:
            raise BudgetExceededError(
                "Kill switch is active -- all spend operations halted",
                details={"tenant_id": self.tenant_id},
            )

        change_pct = (
            abs(proposed_value - current_value) / current_value * 100
            if current_value > 0 else 100.0
        )

        thresholds = self._get_thresholds()
        requires_approval = self._needs_approval(action, change_pct, proposed_value, thresholds)

        # In hard guardrail mode, auto-approve only safe decreases
        auto_approved = False
        if not requires_approval:
            auto_approved = True
        elif self.phase == AutonomyPhase.SEMI_AUTONOMOUS and not requires_approval:
            auto_approved = True
        elif self.phase == AutonomyPhase.CONTROLLED_AUTONOMOUS:
            auto_approved = not requires_approval

        decision = BiddingDecision(
            tenant_id=self.tenant_id,
            action=action,
            platform=platform,
            campaign_id=campaign_id,
            current_value=current_value,
            proposed_value=proposed_value,
            change_pct=round(change_pct, 2),
            requires_approval=requires_approval,
            approved=auto_approved,
            reasoning=reasoning,
            risk_score=self._compute_risk(action, change_pct, proposed_value),
        )

        self._decision_history.append(decision)

        logger.info(
            "bidding_decision",
            tenant_id=self.tenant_id,
            phase=self.phase.value,
            action=action.value,
            change_pct=round(change_pct, 2),
            requires_approval=requires_approval,
            auto_approved=auto_approved,
        )

        return decision

    def approve_decision(self, decision_id: str, approved_by: str) -> bool:
        """Manually approve a pending bidding decision."""
        for d in self._decision_history:
            if d.id == decision_id and d.requires_approval and not d.approved:
                d.approved = True
                d.approved_by = approved_by
                logger.info(
                    "decision_approved",
                    decision_id=decision_id,
                    approved_by=approved_by,
                )
                return True
        return False

    def reject_decision(self, decision_id: str, rejected_by: str) -> bool:
        """Reject a pending bidding decision."""
        for d in self._decision_history:
            if d.id == decision_id and d.requires_approval and not d.approved:
                d.approved = False
                d.approved_by = rejected_by
                d.reasoning += f" [REJECTED by {rejected_by}]"
                return True
        return False

    def transition_phase(
        self,
        target_phase: AutonomyPhase,
        approved_by: str,
        reason: str,
        requirements: TransitionRequirements | None = None,
    ) -> PhaseTransitionRecord:
        """Attempt to transition to a higher autonomy phase."""
        if requirements is None:
            requirements = TransitionRequirements()

        reqs_met = self._check_transition_requirements(target_phase, requirements)

        if not all(reqs_met.values()):
            unmet = [k for k, v in reqs_met.items() if not v]
            logger.warning(
                "phase_transition_blocked",
                target=target_phase.value,
                unmet=unmet,
            )
            raise ValueError(
                f"Cannot transition to {target_phase.value}: "
                f"unmet requirements: {', '.join(unmet)}"
            )

        record = PhaseTransitionRecord(
            tenant_id=self.tenant_id,
            from_phase=self.phase,
            to_phase=target_phase,
            approved_by=approved_by,
            reason=reason,
            requirements_met=reqs_met,
        )

        self._transition_history.append(record)
        self.phase = target_phase

        logger.info(
            "phase_transitioned",
            tenant_id=self.tenant_id,
            from_phase=record.from_phase.value,
            to_phase=target_phase.value,
            approved_by=approved_by,
        )

        return record

    def activate_kill_switch(self, activated_by: str, reason: str) -> None:
        """Activate kill switch -- halts ALL spend operations immediately."""
        self._kill_switch_active = True
        logger.critical(
            "kill_switch_activated",
            tenant_id=self.tenant_id,
            activated_by=activated_by,
            reason=reason,
        )

    def deactivate_kill_switch(self, deactivated_by: str) -> None:
        """Deactivate kill switch (requires manual action)."""
        self._kill_switch_active = False
        logger.info(
            "kill_switch_deactivated",
            tenant_id=self.tenant_id,
            deactivated_by=deactivated_by,
        )

    def record_spend(self, amount: float) -> None:
        """Record spend against daily cap."""
        thresholds = self._get_thresholds()
        new_daily = self._daily_spend + amount

        if new_daily > thresholds["max_daily_spend"]:
            raise BudgetExceededError(
                f"Daily spend cap exceeded: ${new_daily:.2f} > ${thresholds['max_daily_spend']:.2f}",
                details={
                    "tenant_id": self.tenant_id,
                    "current_daily": self._daily_spend,
                    "attempted": amount,
                    "cap": thresholds["max_daily_spend"],
                },
            )

        self._daily_spend = new_daily

    def reset_daily_spend(self) -> None:
        """Reset daily spend counter (called by scheduler at midnight)."""
        self._daily_spend = 0.0

    def get_status(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "phase": self.phase.value,
            "kill_switch_active": self._kill_switch_active,
            "daily_spend": round(self._daily_spend, 2),
            "daily_cap": self._get_thresholds()["max_daily_spend"],
            "pending_approvals": sum(
                1 for d in self._decision_history
                if d.requires_approval and not d.approved and d.approved_by is None
            ),
            "total_decisions": len(self._decision_history),
            "transitions": len(self._transition_history),
        }

    def _get_thresholds(self) -> dict[str, float]:
        if self.phase == AutonomyPhase.HARD_GUARDRAIL:
            return HARD_GUARDRAIL_THRESHOLDS
        elif self.phase == AutonomyPhase.SEMI_AUTONOMOUS:
            return SEMI_AUTO_THRESHOLDS
        else:
            return {k: v * 2 for k, v in SEMI_AUTO_THRESHOLDS.items()}

    def _needs_approval(
        self,
        action: BiddingAction,
        change_pct: float,
        proposed_value: float,
        thresholds: dict[str, float],
    ) -> bool:
        if self.phase == AutonomyPhase.HARD_GUARDRAIL:
            # Everything except small decreases needs approval
            if action == BiddingAction.DECREASE_BUDGET:
                return change_pct > 50.0
            if action == BiddingAction.PAUSE_CAMPAIGN:
                return False
            if action in (BiddingAction.ADJUST_BID, BiddingAction.INCREASE_BUDGET):
                return change_pct > thresholds["budget_change_pct"]
            return True  # All other actions need approval

        elif self.phase == AutonomyPhase.SEMI_AUTONOMOUS:
            if action in (BiddingAction.ADJUST_BID,):
                return change_pct > thresholds["bid_increase_pct"]
            if action in (BiddingAction.INCREASE_BUDGET, BiddingAction.REALLOCATE_BUDGET):
                return change_pct > thresholds["budget_change_pct"]
            if action == BiddingAction.CREATE_CAMPAIGN:
                return proposed_value > thresholds["max_campaign_budget"]
            return False

        else:  # Controlled autonomous
            return proposed_value > thresholds["max_campaign_budget"] * 2

    def _compute_risk(
        self, action: BiddingAction, change_pct: float, proposed_value: float,
    ) -> float:
        risk = 0.0
        if action in (BiddingAction.INCREASE_BUDGET, BiddingAction.ADJUST_BID):
            risk += min(change_pct / 10.0, 5.0)
        if proposed_value > 1000:
            risk += min(proposed_value / 5000.0, 3.0)
        if action == BiddingAction.CREATE_CAMPAIGN:
            risk += 2.0
        return min(round(risk, 2), 10.0)

    def _check_transition_requirements(
        self,
        target: AutonomyPhase,
        reqs: TransitionRequirements,
    ) -> dict[str, bool]:
        if target == AutonomyPhase.SEMI_AUTONOMOUS:
            return {
                "min_days_active": reqs.min_days_active >= 90,
                "positive_roi_cycles": reqs.min_positive_roi_cycles >= 3,
                "anomaly_detection_validated": reqs.anomaly_detection_validated,
                "customer_opt_in": reqs.customer_opt_in,
            }
        elif target == AutonomyPhase.CONTROLLED_AUTONOMOUS:
            return {
                "min_days_active": reqs.min_days_active >= 180,
                "positive_roi_cycles": reqs.min_positive_roi_cycles >= 6,
                "anomaly_detection_validated": reqs.anomaly_detection_validated,
                "customer_opt_in": reqs.customer_opt_in,
                "legal_acknowledgement": reqs.legal_acknowledgement,
                "owner_manual_enable": reqs.owner_manual_enable,
            }
        return {"already_at_lowest": True}

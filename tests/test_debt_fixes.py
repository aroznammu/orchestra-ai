"""Tests for the 3 high-impact technical debt fixes:

1. Bidding engine auto_approved logic for all 3 phases
2. Scheduler registers jobs without crashing
3. Cost router video pipeline tier differentiation
"""

import pytest

from orchestra.bidding.engine import (
    AutonomyPhase,
    BiddingAction,
    BiddingEngine,
    HARD_GUARDRAIL_THRESHOLDS,
    SEMI_AUTO_THRESHOLDS,
    TransitionRequirements,
)
from orchestra.core.cost_router import (
    ModelTier,
    TaskComplexity,
    VideoTier,
    VIDEO_MODELS,
    route_model,
    route_video,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _semi_engine() -> BiddingEngine:
    """Return a BiddingEngine already transitioned to SEMI_AUTONOMOUS."""
    engine = BiddingEngine(tenant_id="t1")
    reqs = TransitionRequirements(
        min_days_active=90,
        min_positive_roi_cycles=3,
        anomaly_detection_validated=True,
        customer_opt_in=True,
    )
    engine.transition_phase(AutonomyPhase.SEMI_AUTONOMOUS, approved_by="admin", reason="test", requirements=reqs)
    return engine


def _controlled_engine() -> BiddingEngine:
    """Return a BiddingEngine transitioned to CONTROLLED_AUTONOMOUS."""
    engine = _semi_engine()
    reqs = TransitionRequirements(
        min_days_active=180,
        min_positive_roi_cycles=6,
        anomaly_detection_validated=True,
        customer_opt_in=True,
        legal_acknowledgement=True,
        owner_manual_enable=True,
    )
    engine.transition_phase(AutonomyPhase.CONTROLLED_AUTONOMOUS, approved_by="admin", reason="test", requirements=reqs)
    return engine


# ===================================================================
# 1. Bidding engine -- auto_approved for all 3 phases
# ===================================================================

class TestBiddingHardGuardrail:

    def test_small_decrease_auto_approved(self):
        engine = BiddingEngine(tenant_id="t1")
        d = engine.evaluate_action(
            BiddingAction.DECREASE_BUDGET, "twitter",
            current_value=100, proposed_value=80, reasoning="trim spend",
        )
        assert d.approved is True
        assert d.requires_approval is False

    def test_large_decrease_needs_approval(self):
        engine = BiddingEngine(tenant_id="t1")
        d = engine.evaluate_action(
            BiddingAction.DECREASE_BUDGET, "twitter",
            current_value=100, proposed_value=20, reasoning="drastic cut",
        )
        assert d.requires_approval is True
        assert d.approved is False

    def test_pause_auto_approved(self):
        engine = BiddingEngine(tenant_id="t1")
        d = engine.evaluate_action(
            BiddingAction.PAUSE_CAMPAIGN, "twitter",
            current_value=100, proposed_value=0,
        )
        assert d.approved is True

    def test_small_bid_increase_auto_approved(self):
        engine = BiddingEngine(tenant_id="t1")
        d = engine.evaluate_action(
            BiddingAction.ADJUST_BID, "twitter",
            current_value=100, proposed_value=105,
        )
        assert d.approved is True

    def test_large_bid_increase_needs_approval(self):
        engine = BiddingEngine(tenant_id="t1")
        d = engine.evaluate_action(
            BiddingAction.ADJUST_BID, "twitter",
            current_value=100, proposed_value=200,
        )
        assert d.requires_approval is True
        assert d.approved is False

    def test_create_campaign_always_needs_approval(self):
        engine = BiddingEngine(tenant_id="t1")
        d = engine.evaluate_action(
            BiddingAction.CREATE_CAMPAIGN, "twitter",
            current_value=0, proposed_value=500,
        )
        assert d.requires_approval is True
        assert d.approved is False


class TestBiddingSemiAutonomous:
    """After the fix, SEMI_AUTONOMOUS should auto-approve within thresholds."""

    def test_small_bid_adjust_auto_approved(self):
        engine = _semi_engine()
        d = engine.evaluate_action(
            BiddingAction.ADJUST_BID, "twitter",
            current_value=100, proposed_value=110,
        )
        assert engine.phase == AutonomyPhase.SEMI_AUTONOMOUS
        assert d.approved is True

    def test_large_bid_adjust_within_semi_threshold(self):
        """Change <= 20% should be auto-approved in semi mode."""
        engine = _semi_engine()
        d = engine.evaluate_action(
            BiddingAction.ADJUST_BID, "twitter",
            current_value=100, proposed_value=119,
        )
        assert d.approved is True

    def test_over_threshold_bid_adjust_not_auto_approved(self):
        """Change > 20% exceeds semi threshold -- NOT auto-approved (needs human review)."""
        engine = _semi_engine()
        d = engine.evaluate_action(
            BiddingAction.ADJUST_BID, "twitter",
            current_value=100, proposed_value=130,
        )
        assert d.requires_approval is True
        assert d.approved is False

    def test_budget_increase_within_threshold(self):
        engine = _semi_engine()
        d = engine.evaluate_action(
            BiddingAction.INCREASE_BUDGET, "twitter",
            current_value=1000, proposed_value=1200,
        )
        assert d.approved is True

    def test_create_campaign_under_max(self):
        engine = _semi_engine()
        d = engine.evaluate_action(
            BiddingAction.CREATE_CAMPAIGN, "twitter",
            current_value=0, proposed_value=5000,
        )
        assert d.requires_approval is False
        assert d.approved is True

    def test_create_campaign_over_max_needs_approval(self):
        engine = _semi_engine()
        d = engine.evaluate_action(
            BiddingAction.CREATE_CAMPAIGN, "twitter",
            current_value=0, proposed_value=15000,
        )
        assert d.requires_approval is True

    def test_decrease_always_approved_in_semi(self):
        engine = _semi_engine()
        d = engine.evaluate_action(
            BiddingAction.DECREASE_BUDGET, "twitter",
            current_value=500, proposed_value=100,
        )
        assert d.approved is True

    def test_pause_always_approved_in_semi(self):
        engine = _semi_engine()
        d = engine.evaluate_action(
            BiddingAction.PAUSE_CAMPAIGN, "twitter",
            current_value=500, proposed_value=0,
        )
        assert d.approved is True


class TestBiddingControlledAutonomous:
    """After the fix, CONTROLLED_AUTONOMOUS should auto-approve broadly."""

    def test_large_bid_adjust_auto_approved(self):
        """Controlled autonomous auto-approves even large changes <= 50%."""
        engine = _controlled_engine()
        d = engine.evaluate_action(
            BiddingAction.ADJUST_BID, "twitter",
            current_value=100, proposed_value=140,
        )
        assert engine.phase == AutonomyPhase.CONTROLLED_AUTONOMOUS
        assert d.approved is True

    def test_extreme_outlier_not_auto_approved(self):
        """Extreme proposals (>2x campaign cap AND change > 50%) need human review."""
        engine = _controlled_engine()
        d = engine.evaluate_action(
            BiddingAction.CREATE_CAMPAIGN, "twitter",
            current_value=0, proposed_value=50000,
        )
        assert d.requires_approval is True
        assert d.approved is False  # change_pct 100 > 50 -> not auto in controlled

    def test_moderate_campaign_auto_approved(self):
        engine = _controlled_engine()
        d = engine.evaluate_action(
            BiddingAction.CREATE_CAMPAIGN, "twitter",
            current_value=0, proposed_value=5000,
        )
        assert d.approved is True

    def test_budget_reallocate_auto_approved(self):
        engine = _controlled_engine()
        d = engine.evaluate_action(
            BiddingAction.REALLOCATE_BUDGET, "twitter",
            current_value=1000, proposed_value=1400,
        )
        assert d.approved is True

    def test_decrease_auto_approved(self):
        engine = _controlled_engine()
        d = engine.evaluate_action(
            BiddingAction.DECREASE_BUDGET, "twitter",
            current_value=1000, proposed_value=100,
        )
        assert d.approved is True


class TestBiddingPhaseSpecific:
    """Cross-phase comparison: same action, different phase -> different result."""

    def test_same_action_different_approval_across_phases(self):
        """A 15% bid increase: approved differently per phase."""
        for phase_fn in [
            lambda: BiddingEngine("t1"),
            _semi_engine,
            _controlled_engine,
        ]:
            engine = phase_fn()
            d = engine.evaluate_action(
                BiddingAction.ADJUST_BID, "twitter",
                current_value=100, proposed_value=115,
            )
            if engine.phase == AutonomyPhase.HARD_GUARDRAIL:
                # 15% > 10% threshold -> requires approval, not auto-approved
                assert d.requires_approval is True
                assert d.approved is False
            elif engine.phase == AutonomyPhase.SEMI_AUTONOMOUS:
                # 15% <= 20% threshold -> no approval needed, auto-approved
                assert d.requires_approval is False
                assert d.approved is True
            elif engine.phase == AutonomyPhase.CONTROLLED_AUTONOMOUS:
                # Very permissive, auto-approved
                assert d.approved is True


# ===================================================================
# 2. Scheduler registers jobs without crashing
# ===================================================================

class TestScheduler:

    @pytest.mark.asyncio
    async def test_start_scheduler_registers_jobs(self):
        import orchestra.core.scheduler as sched_mod
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        fresh = AsyncIOScheduler()
        original = sched_mod.scheduler
        sched_mod.scheduler = fresh
        try:
            sched_mod.start_scheduler()
            jobs = sched_mod.get_registered_jobs()
            job_ids = {j["id"] for j in jobs}
            assert "reset_daily_spend" in job_ids
            assert "reset_monthly_spend" in job_ids
            assert "update_velocity_baselines" in job_ids
            assert len(jobs) >= 3
        finally:
            sched_mod.stop_scheduler()
            sched_mod.scheduler = original

    @pytest.mark.asyncio
    async def test_start_scheduler_idempotent(self):
        import orchestra.core.scheduler as sched_mod
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        fresh = AsyncIOScheduler()
        original = sched_mod.scheduler
        sched_mod.scheduler = fresh
        try:
            sched_mod.start_scheduler()
            sched_mod.start_scheduler()  # should not crash
            assert sched_mod.scheduler.running is True
        finally:
            sched_mod.stop_scheduler()
            sched_mod.scheduler = original

    def test_stop_scheduler_when_not_running(self):
        from orchestra.core.scheduler import stop_scheduler

        stop_scheduler()  # should not crash

    def test_register_tracker_and_monitor(self):
        from orchestra.core.scheduler import (
            register_spend_tracker,
            register_velocity_monitor,
            _spend_trackers,
            _velocity_monitors,
        )
        from orchestra.risk.spend_caps import SpendTracker
        from orchestra.risk.velocity import SpendVelocityMonitor

        tracker = SpendTracker("t1")
        monitor = SpendVelocityMonitor("t1")

        register_spend_tracker("t1", tracker)
        register_velocity_monitor("t1", monitor)

        assert "t1" in _spend_trackers
        assert "t1" in _velocity_monitors

    @pytest.mark.asyncio
    async def test_reset_daily_spend_caps_job(self):
        from orchestra.core.scheduler import (
            _reset_daily_spend_caps,
            register_spend_tracker,
        )
        from orchestra.risk.spend_caps import SpendTracker

        tracker = SpendTracker("t-daily-test")
        tracker.record_spend(100.0, "twitter")
        assert tracker._global_daily == 100.0

        register_spend_tracker("t-daily-test", tracker)
        await _reset_daily_spend_caps()

        assert tracker._global_daily == 0.0

    @pytest.mark.asyncio
    async def test_update_velocity_baselines_job(self):
        from orchestra.core.scheduler import (
            _update_velocity_baselines,
            register_velocity_monitor,
        )
        from orchestra.risk.velocity import SpendVelocityMonitor

        monitor = SpendVelocityMonitor("t-vel-test")
        monitor.record_spend(50.0)
        register_velocity_monitor("t-vel-test", monitor)

        await _update_velocity_baselines()
        assert monitor._baseline_velocity > 0


# ===================================================================
# 3. Cost router -- video pipeline tier differentiation
# ===================================================================

class TestVideoRouting:

    def test_draft_tier_default(self):
        model, tier, config = route_video()
        assert tier == VideoTier.DRAFT
        assert model == "runway-gen3-alpha-turbo"
        assert config["cost_per_minute"] == 0.05

    def test_upscale_tier_for_validated_winner(self):
        model, tier, config = route_video(is_validated_winner=True)
        assert tier == VideoTier.UPSCALE
        assert model == "sora-v1"
        assert config["cost_per_minute"] == 0.50

    def test_byok_with_tenant_key(self):
        model, tier, config = route_video(
            tenant_byok_key="sk-tenant-unlimited-xyz",
            tenant_byok_model="custom-model",
        )
        assert tier == VideoTier.BYOK
        assert model == "custom-model"
        assert config["cost_per_minute"] == 0.0
        assert config["byok_key"] == "sk-tenant-unlimited-xyz"

    def test_byok_without_model_defaults_to_tenant_provided(self):
        model, tier, config = route_video(tenant_byok_key="sk-xyz")
        assert tier == VideoTier.BYOK
        assert model == "tenant-provided"

    def test_byok_overrides_validated_winner(self):
        """BYOK takes precedence even if is_validated_winner=True."""
        model, tier, _ = route_video(
            is_validated_winner=True,
            tenant_byok_key="sk-tenant-unlimited",
        )
        assert tier == VideoTier.BYOK

    def test_draft_has_fallback(self):
        config = VIDEO_MODELS[VideoTier.DRAFT]
        assert config["fallback"] == "kling-v1"

    def test_upscale_has_fallback(self):
        config = VIDEO_MODELS[VideoTier.UPSCALE]
        assert config["fallback"] == "veo-v2"

    def test_byok_no_fallback(self):
        config = VIDEO_MODELS[VideoTier.BYOK]
        assert config["fallback"] is None

    def test_draft_cheaper_than_upscale(self):
        assert VIDEO_MODELS[VideoTier.DRAFT]["cost_per_minute"] < VIDEO_MODELS[VideoTier.UPSCALE]["cost_per_minute"]

    def test_byok_zero_cost(self):
        assert VIDEO_MODELS[VideoTier.BYOK]["cost_per_minute"] == 0.0


class TestTextRoutingUnchanged:
    """Verify the existing route_model still works after refactor."""

    def test_simple_routes_to_fast_or_local(self):
        model, tier = route_model(TaskComplexity.SIMPLE)
        assert tier in (ModelTier.FAST, ModelTier.LOCAL)

    def test_moderate_routes_correctly(self):
        model, tier = route_model(TaskComplexity.MODERATE)
        assert tier in (ModelTier.FAST, ModelTier.CAPABLE, ModelTier.LOCAL)

    def test_complex_routes_correctly(self):
        model, tier = route_model(TaskComplexity.COMPLEX)
        assert tier in (ModelTier.FAST, ModelTier.CAPABLE, ModelTier.LOCAL)

    def test_prefer_local_overrides(self):
        model, tier = route_model(TaskComplexity.COMPLEX, prefer_local=True)
        assert tier == ModelTier.LOCAL

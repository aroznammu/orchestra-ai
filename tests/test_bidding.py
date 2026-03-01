"""Tests for the bidding engine, guardrails, and kill switch."""

from orchestra.bidding.engine import AutonomyPhase, BiddingEngine
from orchestra.bidding.guardrails import ABSOLUTE_LIMITS, SpendGuardrails, check_all_guardrails
from orchestra.bidding.kill_switch import KillSwitch


def test_bidding_engine_starts_in_hard_guardrail():
    engine = BiddingEngine(tenant_id="t1")
    assert engine.phase == AutonomyPhase.HARD_GUARDRAIL


def test_bidding_engine_has_zero_daily_spend():
    engine = BiddingEngine(tenant_id="t1")
    assert engine._daily_spend == 0.0


def test_kill_switch_activates_globally():
    ks = KillSwitch()
    ks.activate_global(triggered_by="test", reason="Emergency test")
    assert ks.is_global_active is True


def test_kill_switch_deactivates():
    ks = KillSwitch()
    ks.activate_global(triggered_by="test", reason="Test")
    ks.deactivate_global(triggered_by="test")
    assert ks.is_global_active is False


def test_kill_switch_tenant_level():
    ks = KillSwitch()
    ks.activate_tenant("tenant-1", triggered_by="test", reason="Test")
    assert ks.is_active("tenant-1") is True
    assert ks.is_active("tenant-2") is False


def test_kill_switch_global_overrides_tenant():
    ks = KillSwitch()
    ks.activate_global(triggered_by="test", reason="Global halt")
    assert ks.is_active("any-tenant") is True


def test_absolute_limits_is_dict():
    assert isinstance(ABSOLUTE_LIMITS, dict)
    assert "max_daily_spend_any_tenant" in ABSOLUTE_LIMITS
    assert ABSOLUTE_LIMITS["max_daily_spend_any_tenant"] > 0


def test_spend_guardrails_defaults():
    g = SpendGuardrails()
    assert g.global_daily_cap > 0
    assert g.global_monthly_cap > 0


def test_check_guardrails_clean():
    results = check_all_guardrails(
        action="adjust_bid",
        amount=50.0,
        current_daily_spend=100.0,
        current_monthly_spend=500.0,
    )
    passing = [r for r in results if r.passed]
    assert len(passing) > 0


def test_check_guardrails_over_daily():
    results = check_all_guardrails(
        action="adjust_bid",
        amount=50.0,
        current_daily_spend=480.0,
        current_monthly_spend=500.0,
    )
    failed = [r for r in results if not r.passed]
    assert len(failed) > 0


def test_bidding_engine_phase_transition():
    from orchestra.bidding.engine import TransitionRequirements

    engine = BiddingEngine(tenant_id="t1")
    reqs = TransitionRequirements(
        min_days_active=90,
        min_positive_roi_cycles=3,
        anomaly_detection_validated=True,
        customer_opt_in=True,
    )
    engine.transition_phase(
        AutonomyPhase.SEMI_AUTONOMOUS,
        approved_by="admin",
        reason="Performance threshold met",
        requirements=reqs,
    )
    assert engine.phase == AutonomyPhase.SEMI_AUTONOMOUS


def test_kill_switch_event_log():
    ks = KillSwitch()
    ks.activate_global(triggered_by="admin", reason="Test 1")
    ks.deactivate_global(triggered_by="admin")
    assert len(ks._event_log) >= 2

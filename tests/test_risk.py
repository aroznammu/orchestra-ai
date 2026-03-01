"""Tests for risk management: spend caps, anomaly detection, alerts, velocity."""

from orchestra.risk.spend_caps import SpendCaps, SpendTracker
from orchestra.risk.anomaly import AnomalyDetector
from orchestra.risk.alerts import AlertManager, ALERT_THRESHOLDS
from orchestra.risk.velocity import SpendVelocityMonitor


def test_spend_caps_defaults():
    caps = SpendCaps()
    assert caps.global_daily_cap == 500.0
    assert caps.global_monthly_cap == 10000.0


def test_spend_tracker_no_violation_on_small_amount():
    tracker = SpendTracker(tenant_id="t1")
    violations = tracker.check_spend(amount=10.0, platform="twitter")
    assert len(violations) == 0


def test_spend_tracker_violation_over_daily_cap():
    caps = SpendCaps(global_daily_cap=100.0)
    tracker = SpendTracker(tenant_id="t1", caps=caps)
    violations = tracker.check_spend(amount=150.0, platform="twitter")
    assert len(violations) > 0
    assert any(v["cap"] == "global_daily" for v in violations)


def test_spend_tracker_platform_cap_violation():
    caps = SpendCaps(default_platform_daily_cap=50.0)
    tracker = SpendTracker(tenant_id="t1", caps=caps)
    violations = tracker.check_spend(amount=60.0, platform="facebook")
    assert any("platform_daily" in v["cap"] for v in violations)


def test_anomaly_detector_no_anomaly_on_first_point():
    detector = AnomalyDetector(tenant_id="t1")
    result = detector.check(amount=100.0, auto_raise=False)
    assert result["is_anomaly"] is False


def test_anomaly_detector_records_baseline():
    detector = AnomalyDetector(tenant_id="t1")
    result = detector.check(amount=50.0, auto_raise=False)
    assert result["amount"] == 50.0
    assert "is_anomaly" in result


def test_alert_manager_fires_at_50_pct():
    mgr = AlertManager()
    alerts = mgr.check_budget_thresholds(
        tenant_id="t1",
        current_spend=260.0,
        budget_cap=500.0,
    )
    types = [a.alert_type.value for a in alerts]
    assert "budget_50pct" in types


def test_alert_manager_fires_at_75_and_90():
    mgr = AlertManager()
    alerts_75 = mgr.check_budget_thresholds(
        tenant_id="t1",
        current_spend=380.0,
        budget_cap=500.0,
    )
    alerts_90 = mgr.check_budget_thresholds(
        tenant_id="t1",
        current_spend=460.0,
        budget_cap=500.0,
    )
    all_types = [a.alert_type.value for a in alerts_75 + alerts_90]
    assert "budget_75pct" in all_types
    assert "budget_90pct" in all_types


def test_alert_manager_no_duplicate_fires():
    mgr = AlertManager()
    mgr.check_budget_thresholds("t1", 260.0, 500.0)
    alerts2 = mgr.check_budget_thresholds("t1", 260.0, 500.0)
    assert len(alerts2) == 0


def test_alert_thresholds_defined():
    assert len(ALERT_THRESHOLDS) == 4


def test_velocity_monitor_records_spend():
    monitor = SpendVelocityMonitor(tenant_id="t1")
    result = monitor.record_spend(50.0)
    assert "current_velocity_per_hour" in result
    assert result["is_spike"] is False


def test_velocity_monitor_multiple_records():
    monitor = SpendVelocityMonitor(tenant_id="t1")
    for _ in range(5):
        result = monitor.record_spend(10.0)
    assert result["current_velocity_per_hour"] >= 0

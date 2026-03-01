"""Optimization Agent -- multi-armed bandit + Bayesian optimization.

Selects the best content variant, learns from engagement data,
and recommends budget allocation across platforms.
"""

import math
import random
from typing import Any

import structlog

from orchestra.agents.contracts import OptimizationRequest, OptimizationResult
from orchestra.agents.trace import ExecutionTrace, TraceTimer

logger = structlog.get_logger("agent.optimizer")


class ThompsonSamplingBandit:
    """Multi-armed bandit using Thompson Sampling for variant selection."""

    def __init__(self, n_arms: int) -> None:
        self.n_arms = n_arms
        self.successes = [1.0] * n_arms  # Beta prior alpha
        self.failures = [1.0] * n_arms   # Beta prior beta

    def select_arm(self) -> int:
        """Sample from each arm's Beta distribution, pick highest."""
        samples = [
            random.betavariate(self.successes[i], self.failures[i])
            for i in range(self.n_arms)
        ]
        return int(max(range(self.n_arms), key=lambda i: samples[i]))

    def update(self, arm: int, reward: float) -> None:
        """Update arm's distribution with observed reward (0-1)."""
        if reward > 0.5:
            self.successes[arm] += 1
        else:
            self.failures[arm] += 1

    def get_arm_stats(self) -> list[dict[str, float]]:
        return [
            {
                "arm": i,
                "mean": self.successes[i] / (self.successes[i] + self.failures[i]),
                "trials": self.successes[i] + self.failures[i] - 2,
            }
            for i in range(self.n_arms)
        ]


class BayesianBudgetOptimizer:
    """Bayesian approach to cross-platform budget allocation."""

    def __init__(self) -> None:
        self.platform_performance: dict[str, list[float]] = {}

    def record_performance(self, platform: str, roi: float) -> None:
        if platform not in self.platform_performance:
            self.platform_performance[platform] = []
        self.platform_performance[platform].append(roi)

    def recommend_allocation(self, total_budget: float) -> dict[str, float]:
        """Recommend budget split based on historical ROI."""
        if not self.platform_performance:
            return {}

        means: dict[str, float] = {}
        for platform, values in self.platform_performance.items():
            if values:
                means[platform] = sum(values) / len(values)

        total_mean = sum(max(m, 0.01) for m in means.values())
        if total_mean == 0:
            equal_share = total_budget / len(means)
            return {p: equal_share for p in means}

        return {
            platform: round(total_budget * max(mean, 0.01) / total_mean, 2)
            for platform, mean in means.items()
        }


async def run_optimization(
    request: OptimizationRequest,
    trace: ExecutionTrace,
) -> OptimizationResult:
    """Run optimization on content variants or budget allocation."""
    with TraceTimer() as timer:
        if request.optimization_type == "content":
            result = _optimize_content_variants(request)
        elif request.optimization_type == "budget":
            result = _optimize_budget(request)
        else:
            result = OptimizationResult(
                reasoning=f"Unknown optimization type: {request.optimization_type}"
            )

    trace.log(
        agent="optimizer",
        action=f"optimize_{request.optimization_type}",
        input_summary=f"campaign={request.campaign_id}, type={request.optimization_type}, "
        f"variants={len(request.variants)}",
        output_summary=f"recommended={result.recommended_variant}, "
        f"improvement={result.expected_improvement:.1%}",
        confidence=result.confidence,
        duration_ms=timer.duration_ms,
    )

    return result


def _optimize_content_variants(request: OptimizationRequest) -> OptimizationResult:
    """Use Thompson Sampling to select best content variant."""
    n_variants = len(request.variants)
    if n_variants == 0:
        return OptimizationResult(reasoning="No variants to optimize")

    bandit = ThompsonSamplingBandit(n_variants)

    # Load historical engagement data if available
    history = request.historical_data.get("engagement_rates", [])
    for record in history:
        arm = record.get("variant", 0)
        reward = record.get("engagement_rate", 0.0)
        if arm < n_variants:
            bandit.update(arm, reward)

    selected = bandit.select_arm()
    stats = bandit.get_arm_stats()

    best_mean = stats[selected]["mean"] if stats else 0.5
    baseline = 1.0 / n_variants
    improvement = (best_mean - baseline) / baseline if baseline > 0 else 0.0

    return OptimizationResult(
        recommended_variant=selected,
        expected_improvement=improvement,
        confidence=min(best_mean, 0.99),
        reasoning=f"Thompson Sampling selected variant {selected} with "
        f"estimated {best_mean:.1%} success rate "
        f"(+{improvement:.1%} vs uniform random)",
        next_experiment={
            "type": "a_b_test",
            "arms": n_variants,
            "next_arm_to_explore": _ucb_selection(stats),
            "recommended_sample_size": _required_sample_size(n_variants),
        },
    )


def _optimize_budget(request: OptimizationRequest) -> OptimizationResult:
    """Recommend budget allocation across platforms."""
    optimizer = BayesianBudgetOptimizer()

    platform_history = request.historical_data.get("platform_roi", {})
    for platform, roi_values in platform_history.items():
        for roi in roi_values:
            optimizer.record_performance(platform, roi)

    total_budget = request.constraints.get("total_budget", 1000.0)
    allocation = optimizer.recommend_allocation(total_budget)

    return OptimizationResult(
        recommended_variant=0,
        expected_improvement=0.0,
        confidence=0.5,
        reasoning=f"Budget allocation across {len(allocation)} platforms "
        f"based on historical ROI",
        next_experiment={
            "type": "budget_allocation",
            "allocation": allocation,
            "total_budget": total_budget,
        },
    )


def _ucb_selection(stats: list[dict[str, float]]) -> int:
    """Upper Confidence Bound -- balance exploration vs exploitation."""
    if not stats:
        return 0
    total_trials = sum(s["trials"] for s in stats) + 1
    ucb_values = []
    for s in stats:
        trials = max(s["trials"], 1)
        ucb = s["mean"] + math.sqrt(2 * math.log(total_trials) / trials)
        ucb_values.append(ucb)
    return int(max(range(len(ucb_values)), key=lambda i: ucb_values[i]))


def _required_sample_size(n_variants: int, effect_size: float = 0.05) -> int:
    """Estimate needed samples per variant for statistical significance."""
    # Simplified: 16 * sigma^2 / delta^2 for 80% power
    p = 0.5
    sigma_sq = p * (1 - p)
    n = int(16 * sigma_sq / (effect_size ** 2))
    return max(n, 100) * n_variants

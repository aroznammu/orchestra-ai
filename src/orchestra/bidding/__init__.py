"""Guardrailed AI-Assisted Bidding System.

Three-phase autonomy model: Hard Guardrail -> Semi-Autonomous -> Controlled Autonomous.
"""

from orchestra.bidding.engine import AutonomyPhase, BiddingEngine
from orchestra.bidding.kill_switch import KillSwitch, get_kill_switch

__all__ = ["AutonomyPhase", "BiddingEngine", "KillSwitch", "get_kill_switch"]

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SimulationStep:
    technique_id: str
    asset_ref: str
    expected_control: str

    def __post_init__(self) -> None:
        if not self.technique_id.startswith("T"):
            raise ValueError("technique_id must be an ATT&CK-style technique identifier")
        if not self.asset_ref.strip() or not self.expected_control.strip():
            raise ValueError("asset_ref and expected_control must not be blank")


@dataclass(frozen=True, slots=True)
class AuthorizedSimulationPlan:
    authorization_ref: str
    lab_only: bool
    steps: tuple[SimulationStep, ...]

    def __post_init__(self) -> None:
        if not self.authorization_ref.strip():
            raise ValueError("authorization_ref must not be blank")
        if not self.lab_only:
            raise ValueError("simulation execution contract is restricted to lab_only=True")
        if not self.steps:
            raise ValueError("steps must not be empty")


def evaluate_control_results(plan: AuthorizedSimulationPlan, observations: dict[str, bool]) -> dict[str, bool]:
    return {step.technique_id: bool(observations.get(step.technique_id, False)) for step in plan.steps}

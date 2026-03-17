"""Runtime kill switch for generation and task admission controls."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class KillSwitchState:
    enabled: bool = False
    reason: str = ""


class BudgetKillSwitch:
    def __init__(self) -> None:
        self._state = KillSwitchState()

    def enable(self, reason: str = "MANUAL_KILL_SWITCH") -> None:
        self._state = KillSwitchState(enabled=True, reason=reason)

    def disable(self) -> None:
        self._state = KillSwitchState(enabled=False, reason="")

    def is_enabled(self) -> bool:
        return self._state.enabled

    def reason(self) -> str:
        return self._state.reason

    def snapshot(self) -> KillSwitchState:
        return KillSwitchState(enabled=self._state.enabled, reason=self._state.reason)


runtime_kill_switch = BudgetKillSwitch()

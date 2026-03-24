from dataclasses import dataclass
from typing import Any, Dict, Optional, Literal

@dataclass
class ExecutionResult:
    source: Literal["skill", "realtime", "direct"]
    label: str
    data: Dict[str, Any]
    timestamp: str
    status: Literal["success", "error"]
    error_reason: Optional[str] = None

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class LearningProfile:
    type: str  # 'symbolic', 'statistical', 'causal'
    arc_performance: Optional[Dict[str, Any]] = field(default_factory=dict)
    tag_performance: Optional[Dict[str, Any]] = field(default_factory=dict)
    variable_stats: Optional[Dict[str, Any]] = field(default_factory=dict)
    causal_links: Optional[Dict[str, Any]] = field(default_factory=dict)
    causal_paths: Optional[Dict[str, Any]] = field(default_factory=dict)
    avg_regret: Optional[float] = None
    # Add more fields as needed

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LearningProfile":
        return cls(**d)

from dataclasses import dataclass

@dataclass
class TargetData:
    track_id: int
    confidence: float
    x: float
    y: float
    z: float = 0.0


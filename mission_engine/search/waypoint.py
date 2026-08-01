from dataclasses import dataclass

@dataclass
class Waypoint:
    x: float
    y: float
    z: float
    yaw: float = 0.0
    speed: float = 1.5
    command: str = "WAYPOINT"

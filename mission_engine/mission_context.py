from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


# ==========================================================
# ENUMS
# ==========================================================

class FlightMode(Enum):
    UNKNOWN = auto()
    OFFBOARD = auto()
    POSCTL = auto()
    AUTO = auto()
    RTL = auto()
    LAND = auto()
    MISSION = auto()


class SearchPattern(Enum):
    NONE = auto()
    LAWNMOWER = auto()
    SPIRAL = auto()
    SQUARE = auto()
    ROTATE = auto()


class FailsafeReason(Enum):
    NONE = auto()
    GPS_LOST = auto()
    IMU_FAILURE = auto()
    BARO_FAILURE = auto()
    CAMERA_FAILURE = auto()
    VISION_LOST = auto()
    LOW_BATTERY = auto()
    TELEMETRY_TIMEOUT = auto()
    PX4_CONNECTION_LOST = auto()
    OFFBOARD_LOST = auto()


# ==========================================================
# SYSTEM HEALTH
# ==========================================================

@dataclass
class HealthStatus:

    sensor_ok: bool = False

    gps_ok: bool = False
    imu_ok: bool = False
    baro_ok: bool = False

    camera_ok: bool = False
    vision_ok: bool = False

    telemetry_ok: bool = False
    px4_connected: bool = False
    offboard_ok: bool = False


# ==========================================================
# BATTERY
# ==========================================================

@dataclass
class BatteryStatus:

    percentage: float = 100.0
    voltage: float = 0.0
    remaining_time: float = 0.0

    ok: bool = False


# ==========================================================
# LOCAL POSITION (NED)
# ==========================================================

@dataclass
class LocalPosition:

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0

    heading: float = 0.0

    relative_altitude: float = 0.0
    absolute_altitude: float = 0.0

    timestamp: float = 0.0


# ==========================================================
# HOME POSITION
# ==========================================================

@dataclass
class HomePosition:

    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


# ==========================================================
# WAYPOINT
# ==========================================================

@dataclass
class WaypointState:

    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None

    reached: bool = False

    command: str = "HOLD"


# ==========================================================
# SEARCH
# ==========================================================

@dataclass
class SearchState:

    pattern: SearchPattern = SearchPattern.LAWNMOWER

    center_x: float = 0.0
    center_y: float = 0.0

    radius: float = 15.0

    waypoint_index: int = 0

    completed: bool = False

    coverage_percent: float = 0.0


# ==========================================================
# TARGET
# ==========================================================

@dataclass
class TargetState:

    found: bool = False

    confirmed: bool = False

    lost: bool = False

    track_id: Optional[int] = None

    confidence: float = 0.0

    # Pixel Coordinates

    pixel_x: float = 0.0
    pixel_y: float = 0.0

    # Bounding Box

    bbox_x1: float = 0.0
    bbox_y1: float = 0.0

    bbox_x2: float = 0.0
    bbox_y2: float = 0.0

    # World Coordinates

    world_x: float = 0.0
    world_y: float = 0.0
    world_z: float = 0.0

    # Velocity

    vx: float = 0.0
    vy: float = 0.0

    visible_duration: float = 0.0

    last_seen_timestamp: float = 0.0


# ==========================================================
# FLIGHT STATUS
# ==========================================================

@dataclass
class FlightStatus:

    armed: bool = False

    mode: FlightMode = FlightMode.UNKNOWN

    offboard_active: bool = False

    takeoff_completed: bool = False

    rtl_completed: bool = False

    landing_completed: bool = False


# ==========================================================
# MISSION STATUS
# ==========================================================

@dataclass
class MissionStatus:

    mission_started: bool = False

    mission_completed: bool = False

    mission_start_timestamp: float = 0.0

    mission_elapsed_time: float = 0.0


# ==========================================================
# FAILSAFE
# ==========================================================

@dataclass
class FailsafeStatus:

    active: bool = False

    reason: FailsafeReason = FailsafeReason.NONE

    timestamp: float = 0.0


# ==========================================================
# MISSION CONTEXT
# ==========================================================

@dataclass
class MissionContext:

    ########################################################
    # TIME
    ########################################################

    telemetry_timestamp: float = 0.0

    ########################################################
    # SUB MODELS
    ########################################################

    health: HealthStatus = field(default_factory=HealthStatus)

    battery: BatteryStatus = field(default_factory=BatteryStatus)

    position: LocalPosition = field(default_factory=LocalPosition)

    home: HomePosition = field(default_factory=HomePosition)

    waypoint: WaypointState = field(default_factory=WaypointState)

    search: SearchState = field(default_factory=SearchState)

    target: TargetState = field(default_factory=TargetState)

    flight: FlightStatus = field(default_factory=FlightStatus)

    mission: MissionStatus = field(default_factory=MissionStatus)

    failsafe: FailsafeStatus = field(default_factory=FailsafeStatus)

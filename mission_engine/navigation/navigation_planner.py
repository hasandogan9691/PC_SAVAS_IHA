import math
from dataclasses import dataclass


# ==========================================================
# NAVIGATION COMMAND
# ==========================================================

@dataclass
class NavigationCommand:
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    yaw_rate: float = 0.0
    command_type: str = "HOVER"


# ==========================================================
# NAVIGATION PLANNER
# ==========================================================

class NavigationPlanner:

    def __init__(
        self,
        position_gain=0.8,
        max_horizontal_speed=1.5,
        max_vertical_speed=0.5,
        waypoint_tolerance=0.5,
        takeoff_altitude=2.5,
    ):
        self.position_gain = position_gain
        self.max_horizontal_speed = max_horizontal_speed
        self.max_vertical_speed = max_vertical_speed
        self.waypoint_tolerance = waypoint_tolerance
        self.takeoff_altitude = takeoff_altitude

        print("[NAVIGATION PLANNER] Hareket planlama motoru aktif.")

    # ======================================================
    # YARDIMCI FONKSİYONLAR
    # ======================================================

    @staticmethod
    def _clamp(value, minimum, maximum):
        return max(minimum, min(value, maximum))

    # ======================================================
    # HORIZONTAL VELOCITY LIMIT
    # ======================================================

    def _limit_horizontal_velocity(self, vx, vy):
        speed = math.hypot(vx, vy)

        if speed <= self.max_horizontal_speed:
            return vx, vy

        scale = self.max_horizontal_speed / speed

        return (
            vx * scale,
            vy * scale,
        )

    # ======================================================
    # SEARCH / WAYPOINT NAVIGATION
    # ======================================================

    def compute_search_command(
        self,
        current_x,
        current_y,
        current_z,
        waypoint,
    ):
        """
        SearchPlanner tarafından üretilen waypoint'e
        ulaşmak için hareket komutu üretir.
        """

        if waypoint is None:
            return NavigationCommand(
                command_type="HOVER"
            )

        if waypoint.command == "ROTATE":
            return NavigationCommand(
                vx=0.0,
                vy=0.0,
                vz=0.0,
                yaw_rate=0.5,
                command_type="ROTATE"
            )

        if waypoint.command == "SEARCH_COMPLETE":
            return NavigationCommand(
                vx=0.0,
                vy=0.0,
                vz=0.0,
                yaw_rate=0.0,
                command_type="SEARCH_COMPLETE"
            )

        error_x = waypoint.x - current_x
        error_y = waypoint.y - current_y

        distance = math.hypot(
            error_x,
            error_y
        )

        if distance <= self.waypoint_tolerance:
            return NavigationCommand(
                vx=0.0,
                vy=0.0,
                vz=0.0,
                yaw_rate=0.0,
                command_type="WAYPOINT_REACHED"
            )

        vx = self.position_gain * error_x
        vy = self.position_gain * error_y

        vx, vy = self._limit_horizontal_velocity(
            vx,
            vy
        )

        altitude_error = waypoint.z - current_z

        vz = self._clamp(
            altitude_error * self.position_gain,
            -self.max_vertical_speed,
            self.max_vertical_speed
        )

        return NavigationCommand(
            vx=vx,
            vy=vy,
            vz=vz,
            yaw_rate=0.0,
            command_type=waypoint.command
        )

    # ======================================================
    # HOVER
    # ======================================================

    def compute_hover_command(self):
        return NavigationCommand(
            vx=0.0,
            vy=0.0,
            vz=0.0,
            yaw_rate=0.0,
            command_type="HOVER"
        )

    # ======================================================
    # TAKEOFF
    # ======================================================

    def compute_takeoff_command(
        self,
        current_z,
        target_altitude=None,
    ):
        if target_altitude is None:
            target_altitude = self.takeoff_altitude

        altitude_error = (
            target_altitude - current_z
        )

        if abs(altitude_error) <= 0.15:
            return NavigationCommand(
                vx=0.0,
                vy=0.0,
                vz=0.0,
                command_type="TAKEOFF_COMPLETE"
            )

        vz = self._clamp(
            altitude_error * 0.5,
            -self.max_vertical_speed,
            self.max_vertical_speed
        )

        return NavigationCommand(
            vx=0.0,
            vy=0.0,
            vz=vz,
            yaw_rate=0.0,
            command_type="TAKEOFF"
        )

    # ======================================================
    # RTL
    # ======================================================

    def compute_rtl_command(self):
        return NavigationCommand(
            vx=0.0,
            vy=0.0,
            vz=0.0,
            yaw_rate=0.0,
            command_type="RTL_REQUEST"
        )

    # ======================================================
    # LAND
    # ======================================================

    def compute_land_command(self):
        return NavigationCommand(
            vx=0.0,
            vy=0.0,
            vz=0.0,
            yaw_rate=0.0,
            command_type="LAND_REQUEST"
        )

    # ======================================================
    # FAILSAFE
    # ======================================================

    def compute_failsafe_command(self):
        return NavigationCommand(
            vx=0.0,
            vy=0.0,
            vz=0.0,
            yaw_rate=0.0,
            command_type="FAILSAFE"
        )

    # ======================================================
    # GENERAL COMMAND DISPATCHER
    # ======================================================

    def compute_command(
        self,
        state,
        current_x=0.0,
        current_y=0.0,
        current_z=0.0,
        waypoint=None,
        target_altitude=None,
    ):
        state_name = (
            state.name
            if hasattr(state, "name")
            else str(state)
        )

        if state_name == "TAKEOFF":
            return self.compute_takeoff_command(
                current_z=current_z,
                target_altitude=target_altitude
            )

        if state_name == "HOVER":
            return self.compute_hover_command()

        if state_name == "SEARCH":
            return self.compute_search_command(
                current_x=current_x,
                current_y=current_y,
                current_z=current_z,
                waypoint=waypoint
            )

        if state_name in ["TARGET_CANDIDATE", "TARGET_CONFIRM", "TRACK", "MISSION_COMPLETE"]:
            return self.compute_hover_command()

        if state_name == "RTL":
            return self.compute_rtl_command()

        if state_name == "LAND":
            return self.compute_land_command()

        if state_name == "FAILSAFE":
            return self.compute_failsafe_command()

        if state_name == "SHUTDOWN":
            return NavigationCommand(
                vx=0.0,
                vy=0.0,
                vz=0.0,
                yaw_rate=0.0,
                command_type="SHUTDOWN"
            )

        return self.compute_hover_command()

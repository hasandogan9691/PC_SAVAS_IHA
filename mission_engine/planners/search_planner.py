import math
from dataclasses import dataclass


# ==========================================================
# WAYPOINT
# ==========================================================

@dataclass
class Waypoint:
    x: float
    y: float
    z: float
    yaw: float = 0.0
    speed: float = 1.5
    command: str = "WAYPOINT"


# ==========================================================
# SEARCH CONFIG
# ==========================================================

@dataclass
class SearchConfig:
    square_size: float = 5.0
    spiral_spacing: float = 0.5
    spiral_start_radius: float = 1.0
    lawn_width: int = 5          # sütun sayısı
    lawn_height: int = 5         # satır sayısı
    lawn_step: float = 3.0
    altitude: float = 2.5
    waypoint_speed: float = 1.5
    max_search_radius: float = 25.0


# ==========================================================
# SEARCH PLANNER
# ==========================================================

class SearchPlanner:

    def __init__(
            self,
            pattern="lawnmower",
            center_x=0.0,
            center_y=0.0,
            config=None):

        self.pattern = pattern
        self.center_x = center_x
        self.center_y = center_y
        self.config = config or SearchConfig()
        self.index = 0
        self.finished = False

        print(f"[SEARCH] Pattern : {self.pattern.upper()}")

    # ------------------------------------------------------

    def reset(self):
        self.index = 0
        self.finished = False

    # ------------------------------------------------------

    def set_pattern(self, pattern):
        self.pattern = pattern
        self.reset()
        print(f"[SEARCH] Yeni Pattern : {pattern.upper()}")

    # ------------------------------------------------------

    def advance_waypoint(self):
        self.index += 1

    # ------------------------------------------------------

    def is_finished(self):
        return self.finished

    # ------------------------------------------------------

    def get_next_waypoint(self):
        if self.finished:
            return Waypoint(
                self.center_x,
                self.center_y,
                self.config.altitude,
                command="SEARCH_COMPLETE"
            )

        # ==================================================
        # 360 ROTATE
        # ==================================================

        if self.pattern == "360_scan":
            yaw = (self.index * 45.0) % 360

            if self.index >= 8:
                self.finished = True

            return Waypoint(
                self.center_x,
                self.center_y,
                self.config.altitude,
                yaw=yaw,
                speed=0.0,
                command="ROTATE"
            )

        # ==================================================
        # SQUARE
        # ==================================================

        elif self.pattern == "square":
            s = self.config.square_size

            points = [
                (+s, +s),
                (-s, +s),
                (-s, -s),
                (+s, -s)
            ]

            if self.index >= len(points):
                self.finished = True
                return Waypoint(
                    self.center_x,
                    self.center_y,
                    self.config.altitude,
                    command="SEARCH_COMPLETE"
                )

            dx, dy = points[self.index]

            return Waypoint(
                self.center_x + dx,
                self.center_y + dy,
                self.config.altitude,
                speed=self.config.waypoint_speed,
                command="WAYPOINT"
            )

        # ==================================================
        # SPIRAL
        # ==================================================

        elif self.pattern == "spiral":
            theta = self.index * 0.5

            r = (
                self.config.spiral_start_radius +
                self.config.spiral_spacing * theta
            )

            if r > self.config.max_search_radius:
                self.finished = True
                return Waypoint(
                    self.center_x,
                    self.center_y,
                    self.config.altitude,
                    command="SEARCH_COMPLETE"
                )

            x = self.center_x + r * math.cos(theta)
            y = self.center_y + r * math.sin(theta)

            return Waypoint(
                x,
                y,
                self.config.altitude,
                speed=self.config.waypoint_speed,
                command="SPIRAL"
            )

        # ==================================================
        # LAWNMOWER
        # ==================================================

        elif self.pattern == "lawnmower":
            width = self.config.lawn_width
            height = self.config.lawn_height
            step = self.config.lawn_step

            if self.index >= width * height:
                self.finished = True
                return Waypoint(
                    self.center_x,
                    self.center_y,
                    self.config.altitude,
                    command="SEARCH_COMPLETE"
                )

            row = self.index // width
            col = self.index % width

            y = self.center_y + row * step

            if row % 2 == 0:
                x = self.center_x + col * step
            else:
                x = self.center_x + (width - 1 - col) * step

            return Waypoint(
                x,
                y,
                self.config.altitude,
                speed=self.config.waypoint_speed,
                command="LAWNMOWER"
            )

        # ==================================================
        # UNKNOWN
        # ==================================================

        return Waypoint(
            self.center_x,
            self.center_y,
            self.config.altitude,
            command="HOLD"
        )


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":
    planner = SearchPlanner(pattern="lawnmower")

    while not planner.is_finished():
        wp = planner.get_next_waypoint()
        print(wp)
        planner.advance_waypoint()

    print("SEARCH FINISHED")

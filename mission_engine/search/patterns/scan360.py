from .base_pattern import SearchPattern
from ..waypoint import Waypoint

class Scan360Pattern(SearchPattern):
    def next_waypoint(self):
        cfg = self.config

        if self.index >= 8:
            self.finished = True
            return Waypoint(
                self.center_x,
                self.center_y,
                cfg.altitude,
                command="SEARCH_COMPLETE"
            )

        yaw = self.index * 45

        return Waypoint(
            self.center_x,
            self.center_y,
            cfg.altitude,
            yaw=yaw,
            speed=0,
            command="ROTATE"
        )

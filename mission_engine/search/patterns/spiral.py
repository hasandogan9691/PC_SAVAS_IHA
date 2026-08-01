import math
from .base_pattern import SearchPattern
from ..waypoint import Waypoint

class SpiralPattern(SearchPattern):
    def next_waypoint(self):
        cfg = self.config
        theta = self.index * 0.5
        radius = 1.0 + theta * cfg.spiral_spacing

        if radius > cfg.max_radius:
            self.finished = True
            return Waypoint(
                self.center_x,
                self.center_y,
                cfg.altitude,
                command="SEARCH_COMPLETE"
            )

        x = self.center_x + radius * math.cos(theta)
        y = self.center_y + radius * math.sin(theta)

        return Waypoint(
            x,
            y,
            cfg.altitude,
            speed=cfg.speed,
            command="SPIRAL"
        )

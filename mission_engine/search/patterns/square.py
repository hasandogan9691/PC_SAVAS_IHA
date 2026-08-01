from .base_pattern import SearchPattern
from ..waypoint import Waypoint

class SquarePattern(SearchPattern):
    def next_waypoint(self):
        cfg = self.config
        s = cfg.square_size
        points = [
            (s, s),
            (-s, s),
            (-s, -s),
            (s, -s)
        ]

        if self.index >= len(points):
            self.finished = True
            return Waypoint(
                self.center_x,
                self.center_y,
                cfg.altitude,
                command="SEARCH_COMPLETE"
            )

        dx, dy = points[self.index]

        return Waypoint(
            self.center_x + dx,
            self.center_y + dy,
            cfg.altitude,
            speed=cfg.speed,
            command="SQUARE"
        )

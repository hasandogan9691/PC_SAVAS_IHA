from .base_pattern import SearchPattern
from ..waypoint import Waypoint

class LawnmowerPattern(SearchPattern):
    def next_waypoint(self):
        cfg = self.config
        total = cfg.lawn_rows * cfg.lawn_cols

        if self.index >= total:
            self.finished = True
            return Waypoint(
                self.center_x,
                self.center_y,
                cfg.altitude,
                command="SEARCH_COMPLETE"
            )

        row = self.index // cfg.lawn_cols
        col = self.index % cfg.lawn_cols

        if row % 2 == 0:
            x = self.center_x + col * cfg.lawn_step
        else:
            x = self.center_x + (cfg.lawn_cols - 1 - col) * cfg.lawn_step

        y = self.center_y + row * cfg.lawn_step

        return Waypoint(
            x,
            y,
            cfg.altitude,
            speed=cfg.speed,
            command="LAWNMOWER"
        )

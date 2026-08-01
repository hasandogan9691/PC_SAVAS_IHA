from .patterns.lawnmower import LawnmowerPattern
from .patterns.spiral import SpiralPattern
from .patterns.square import SquarePattern
from .patterns.scan360 import Scan360Pattern

class SearchPlanner:
    def __init__(self, pattern="lawnmower", center_x=0.0, center_y=0.0, config=None):
        patterns = {
            "lawnmower": LawnmowerPattern,
            "spiral": SpiralPattern,
            "square": SquarePattern,
            "360_scan": Scan360Pattern
        }

        if pattern not in patterns:
            raise ValueError(f"Bilinmeyen arama deseni: {pattern}")

        print(f"[SEARCH] Pattern seçildi: {pattern.upper()}")
        self.pattern = patterns[pattern](center_x, center_y, config)

    def get_next_waypoint(self):
        return self.pattern.next_waypoint()

    def advance(self):
        self.pattern.advance()

    def finished(self):
        return self.pattern.done()

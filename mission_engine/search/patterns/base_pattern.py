from abc import ABC, abstractmethod

class SearchPattern(ABC):
    def __init__(self, center_x, center_y, config):
        self.center_x = center_x
        self.center_y = center_y
        self.config = config
        self.index = 0
        self.finished = False

    @abstractmethod
    def next_waypoint(self):
        pass

    def advance(self):
        self.index += 1

    def done(self):
        return self.finished

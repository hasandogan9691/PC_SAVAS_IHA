import time
from .target_events import TargetEvent
from .target import TargetData

class TargetManager:
    def __init__(
            self,
            confidence_threshold=0.75,
            required_confirm_count=3,
            loss_timeout=1.0):

        self.confidence_threshold = confidence_threshold
        self.required_confirm_count = required_confirm_count
        self.loss_timeout = loss_timeout

        self.confirm_count = 0
        self.last_seen = 0
        self.current_track_id = None
        self.target = None
        self.confirmed = False

    def update(self, detection):
        now = time.time()

        if detection is None:
            if now - self.last_seen > self.loss_timeout:
                self.reset()
                return TargetEvent.TARGET_LOST
            return TargetEvent.NONE

        confidence = detection.confidence

        if confidence < self.confidence_threshold:
            return TargetEvent.NONE

        # Track ID kontrolü
        if (
            self.current_track_id is not None
            and detection.track_id != self.current_track_id
        ):
            self.reset()

        self.current_track_id = detection.track_id
        self.target = detection
        self.last_seen = now
        self.confirm_count += 1

        if self.confirm_count >= self.required_confirm_count:
            self.confirmed = True
            return TargetEvent.TARGET_CONFIRMED

        return TargetEvent.TARGET_CANDIDATE

    def reset(self):
        self.confirm_count = 0
        self.confirmed = False
        self.target = None
        self.current_track_id = None

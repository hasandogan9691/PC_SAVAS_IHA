import threading
import time

class TelemetryProvider:
    def __init__(self, mavlink_connection):
        self.master = mavlink_connection
        self.lock = threading.Lock()
        self.running = False
        self.data = {
            "mode": "UNKNOWN", 
            "is_armed": False, 
            "voltage": 15.2,
            "battery_percent": 100, 
            "lat": 0.0, 
            "lon": 0.0,
            "alt": 0.0, 
            "relative_alt": 0.0, 
            "ekf_healthy": True
        }

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'): 
            self.thread.join()

    def _listen_loop(self):
        last_mode = "UNKNOWN"
        while self.running:
            try:
                msg = self.master.recv_match(blocking=False)
                if not msg:
                    time.sleep(0.01)
                    continue
                msg_type = msg.get_type()
                with self.lock:
                    if msg_type == 'HEARTBEAT':
                        self.data["is_armed"] = bool(msg.base_mode & 128)
                        # PX4 Offboard modunu bitmask üzerinden yakalama
                        if msg.custom_mode == 393216: 
                            self.data["mode"] = "OFFBOARD"
                        else:
                            self.data["mode"] = f"PX4_MODE({msg.custom_mode})"
                            
                        if self.data["mode"] != last_mode:
                            print(f"[{time.strftime('%H:%M:%S')}] PX4 Durumu: {last_mode} -> {self.data['mode']}")
                            last_mode = self.data["mode"]
                            
                    elif msg_type == 'BATTERY_STATUS':
                        self.data["battery_percent"] = msg.battery_remaining
                        if hasattr(msg, 'voltages'):
                            self.data["voltage"] = msg.voltages[0] / 1000.0
                        
                    elif msg_type == 'GLOBAL_POSITION_INT':
                        self.data["lat"] = msg.lat / 1E7
                        self.data["lon"] = msg.lon / 1E7
                        self.data["alt"] = msg.alt / 1000.0
                        self.data["relative_alt"] = msg.relative_alt / 1000.0
            except Exception:
                time.sleep(0.1)

    def get_telemetry(self):
        with self.lock: 
            return self.data.copy()

import time
from pymavlink import mavutil

class MavlinkCommander:
    def __init__(self, port, baudrate, timeout=15):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.master = None
        self.target_system = 1
        self.target_component = 1

    def connect(self):
        try:
            print(f"Sanal PX4 SITL Otopilotuna Bağlanılıyor (Port: {self.port})...")
            self.master = mavutil.mavlink_connection(self.port, baud=self.baudrate, autoreconnect=True)
            start_time = time.time()
            while True:
                msg = self.master.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
                if msg:
                    self.target_system = msg.get_srcSystem()
                    self.target_component = msg.get_srcComponent()
                    print(f"PX4 Bağlantısı Başarılı! Sistem ID: {self.target_system}")
                    return True
                if time.time() - start_time > self.timeout: 
                    return False
        except Exception: 
            return False

    def set_offboard_mode(self):
        # PX4 Offboard moduna geçmeden önce otopilota en az 1-2 saniye boyunca boş hız verisi akmalıdır
        for _ in range(15):
            self.send_velocity_body(0.0, 0.0, 0.0, 0.0)
            time.sleep(0.05)
            
        # PX4 OFFBOARD modunu tetikleyen MAVLink komutu
        self.master.mav.command_long_send(
            self.target_system, self.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE, 0,
            1, 393216, 0, 0, 0, 0, 0
        )
        print("PX4 OFFBOARD Uçuş Modu Aktif Edildi.")

    def set_arm_state(self, arm_state=True):
        param1 = 1 if arm_state else 0
        self.master.mav.command_long_send(
            self.target_system, self.target_component, 
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 
            param1, 0, 0, 0, 0, 0, 0
        )
        return True

    def send_velocity_body(self, vx=0.0, vy=0.0, vz=0.0, yaw_rate=0.0):
        type_mask = 3011 # Pozisyon ve ivmeleri kapat, hızları aç bitmaskı
        self.master.mav.set_position_target_local_ned_send(
            0, self.target_system, self.target_component, 
            mavutil.mavlink.MAV_FRAME_BODY_NED, # PX4 Standart Gövde Çerçevesi
            type_mask, 
            0, 0, 0, 
            vx, vy, vz, 
            0, 0, 0, 
            0, yaw_rate
        )

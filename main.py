import time
import json
import sys
import signal
import socket

# YENİ NESİL MODÜLER YAPI: Yapay zeka tespit motorunu kendi yazdığımız rakip_iha dosyasından çağırıyoruz
from rakip_iha import MockVisionProcessor

class PCSavasanIHAMasterSim:
    def __init__(self):
        with open("config.json", "r") as f:
            self.config = json.load(f)
        self.system_running = False
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Dışarıdan çağırdığımız yapay zeka nesnesini başlatıyoruz
        self.vision = MockVisionProcessor()
        
        # Askeri Görev Strateji Safhaları (Savaş FSM)
        self.fsm_state = "SEARCHING" 
        self.lock_start_time = None
        
        # Canlı Simülasyon Veri Paketi
        self.telemetry_data = {
            "mode": "OFFBOARD",
            "is_armed": True,
            "voltage": 15.4,
            "battery_percent": 100,
            "lat": 40.123456,
            "lon": 32.567890,
            "alt": 15.0,
            "relative_alt": 15.0,
            "ekf_healthy": True
        }

    def run(self):
        self.system_running = True
        print("\033[92m[MODÜLER SAVAŞ MOTORU AKTİF]\033[0m")
        print("Yapay zeka verileri 'rakip_iha.py' kütüphanesinden canlı çekiliyor.")
        
        gcs_cfg = self.config["gcs_connection"]
        yaw_rate_cmd = 0.0

        while self.system_running:
            t1 = time.time()
            
            # Yapay zekadan anlık rakip koordinatlarını çek
            drone_moving = (self.fsm_state in ["TRACKING", "LOCKING"])
            v_data = self.vision.get_target_coordinates(drone_moving, yaw_rate_cmd)
            
            # TEKNOFEST Savaş FSM Algoritması
            if self.fsm_state == "SEARCHING":
                yaw_rate_cmd = 0.15 # 360 derece gökyüzünü tara
                if v_data["detected"]:
                    print("\033[93m[FSM]: Rakip İHA Kadraja Girdi! Takip Başlatılıyor...\033[0m")
                    self.fsm_state = "TRACKING"

            elif self.fsm_state == "TRACKING":
                # PID Kontrol: Pikselsel sapmayı kapatacak dönüş açısını hesapla
                yaw_rate_cmd = (v_data["offset_x"] / 320.0) * self.config["pid_tuning"]["max_yaw_rate"]
                
                # Hedef merkezlendi mi? (30 piksel emniyet deadzone filtresi)
                if abs(v_data["offset_x"]) < 30 and abs(v_data["offset_y"]) < 30:
                    print("\033[96m[FSM]: Hedef Tam Merkezde! 3 Saniyelik Kilitlenme Geri Sayımı...\033[0m")
                    self.fsm_state = "LOCKING"
                    self.lock_start_time = time.time()

            elif self.fsm_state == "LOCKING":
                yaw_rate_cmd = (v_data["offset_x"] / 320.0) * 0.1 # Kilidi korumak için mikro manevra
                
                if abs(v_data["offset_x"]) > 50:
                    print("\033[91m[FSM]: Kilitlenme Koptu! Rakip Keskin Manevrayla Kaçtı.\033[0m")
                    self.fsm_state = "TRACKING"
                elif time.time() - self.lock_start_time >= 3.0:
                    print("\033[92m🎯 [BAŞARILI VURUŞ]: 3 Saniye Kilitlenme Sağlandı! Puan Paketlendi.\033[0m")
                    self.fsm_state = "SEARCHING" # Yeniden gökyüzü taramasına dön

            # Durum çubuğunu anlık güncelle
            self.telemetry_data["mode"] = f"OFFBOARD ({self.fsm_state})"
            
            # Paketleri yer istasyonuna UDP 5005 portuna fırlat
            try:
                packet_bytes = json.dumps(self.telemetry_data).encode('utf-8')
                self.udp_sock.sendto(packet_bytes, (gcs_cfg["ip"], gcs_cfg["telemetry_port"]))
            except Exception:
                pass

            dt = time.time() - t1
            if dt < 0.033:
                time.sleep(0.033 - dt)

    def terminate_system(self):
        self.system_running = False
        self.udp_sock.close()
        print("Sistem Kapatildi.")

if __name__ == "__main__":
    master = PCSavasanIHAMasterSim()
    signal.signal(signal.SIGINT, lambda s, f: (master.terminate_system(), sys.exit(0)))
    master.run()


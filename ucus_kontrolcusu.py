import time
from pymavlink import mavutil

class UcusKontrolcusu:
    def __init__(self, baglanti_adresi="udpin:127.0.0.1:14540"):
        self.baglanti_adresi = baglanti_adresi
        self.master = None

    def baglan(self):
        print(f"[KASLAR] İHA ile uçuş hattı kuruluyor: {self.baglanti_adresi}")
        self.master = mavutil.mavlink_connection(self.baglanti_adresi)
        self.master.wait_heartbeat()
        print("[KASLAR] Kalp atışı alındı, otopilot ile bağ kuruldu!")

    def hiz_komutu_gonder(self, vx, vy, vz):
        """
        İHA'nın kendi gövde referansına göre (İleri: vx, Sağ: vy, Aşağı: vz) m/s cinsinden hız gönderir.
        """
        if not self.master:
            return

        self.master.mav.set_position_target_local_ned_send(
            0,  # time_boot_ms
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_FRAME_BODY_NED,  # İHA'nın kendi gövde yönelim referansı
            0b0000111111000111,  # Sadece vx, vy, vz hızlarını dikkate alan maske (3575)
            0, 0, 0,  # x, y, z konumları (önemsenmiyor)
            vx, vy, vz,  # m/s cinsinden hız komutları
            0, 0, 0,  # ivmeler (önemsenmiyor)
            0, 0  # yaw ve yaw_rate (önemsenmiyor)
        )

    def otonom_kalkis_ve_saldiri_baslat(self, hedef_irtifa=2.5):
        if not self.master:
            print("[HATA] İHA ile bağ kurulamadığı için kalkış reddedildi.")
            return

        print("[KASLAR] 1. Aşama: Güvenlik kilidi açılıyor (Force Arm)...")
        self.master.mav.command_long_send(
            self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0, 1, 21196, 0, 0, 0, 0, 0
        )
        time.sleep(1) # Sistemin kendine gelmesi için narin bir bekleme

        print(f"[KASLAR] 2. Aşama: {hedef_irtifa} metreye tırmanış (Takeoff)...")
        self.master.mav.command_long_send(
            self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0, 0, 0, 0, 0, 0, 0, hedef_irtifa
        )
        time.sleep(5) # İrtifaya ulaşması için şefkatli bir mühlet

        print("[KASLAR] Sinyal Köprüsü: Offboard kilidini açmak için ön sinyaller gönderiliyor...")
        # PX4'ün "notify negative" vermemesi için 1.5 saniye boyunca saniyede 10 kez sinyal basıyoruz
        for _ in range(15):
            self.hiz_komutu_gonder(0, 0, 0)
            time.sleep(0.1)

        print("[KASLAR] 3. Aşama: Otonom avlanma yetkisi devralınıyor (Offboard)...")
        self.master.mav.command_long_send(
            self.master.target_system, self.master.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE,
            0,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            6, 0, 0, 0, 0, 0
        )
        print("[KASLAR] Sistem tam bağımsız taarruza hazırdır!")

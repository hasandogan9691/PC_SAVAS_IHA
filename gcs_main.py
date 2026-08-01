import math
import socket
import json
import time
# ======= 3. Adım: Yer Kontrol ve Hakem Sunucusu Modülü (gcs_main.py)   =================
# ============================================================
# HAKEM SUNUCUSU VE COĞRAFİ KONUMLANDIRMA SABİTLERİ
# ============================================================
HAKEM_IP = "127.0.0.1"           # Hakem sunucusu IP adresi (Yarışma alanında verilecek)
HAKEM_PORT = 10000               # Hakem sunucusu UDP portu
TAKIM_ID = 1903                  # Teknofest Takım ID'miz


def hedef_gps_hesapla(drone_lat, drone_lon, drone_alt, heading_deg,
                      error_x, error_y, image_width, image_height,
                      h_fov_deg=60.0, v_fov_deg=45.0):
    """
    Kamera piksel sapmalarını ve İHA telemetrisini kullanarak
    hedefin dünya üzerindeki kesin GPS (Enlem/Boylam) koordinatını hesaplar.
    """
    h_aci_orani = h_fov_deg / image_width
    v_aci_orani = v_fov_deg / image_height

    yaw_sapma_aci = error_x * h_aci_orani
    pitch_sapma_aci = error_y * v_aci_orani

    # Kameraya göre (drone burnu = 0°) yerel offsetler
    mesafe_kamera_saga = drone_alt * math.tan(math.radians(yaw_sapma_aci))
    mesafe_kamera_ileri = drone_alt * math.tan(math.radians(pitch_sapma_aci))

    # Drone'un gerçek heading'ine göre kuzey/doğu eksenine döndür
    heading_rad = math.radians(heading_deg)
    mesafe_kuzey = mesafe_kamera_ileri * math.cos(heading_rad) - mesafe_kamera_saga * math.sin(heading_rad)
    mesafe_dogu = mesafe_kamera_ileri * math.sin(heading_rad) + mesafe_kamera_saga * math.cos(heading_rad)

    delta_lat = mesafe_kuzey / 111000.0
    delta_lon = mesafe_dogu / (111000.0 * math.cos(math.radians(drone_lat)))

    return drone_lat + delta_lat, drone_lon + delta_lon


class HakemHaberlesme:
    """
    Teknofest Hakem Sunucusu ile UDP üzerinden JSON tabanlı haberleşmeyi
    ve bağlantı ömrünü yöneten yardımcı sınıf.
    """
    def __init__(self, ip=HAKEM_IP, port=HAKEM_PORT, takim_id=TAKIM_ID):
        self.ip = ip
        self.port = port
        self.takim_id = takim_id
        self.soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"[GCS] Hakem Sunucusu iletişim ağı hazır ({self.ip}:{self.port})")

    def paket_gonder(self, hedef_lat, hedef_lon, kilitlenme_durum, kilitlenme_sure, ucus_durum):
        try:
            veri_paketi = {
                "takim_id": self.takim_id,
                "hedef_enlem": round(hedef_lat, 6),
                "hedef_boylam": round(hedef_lon, 6),
                "kilitlenme": int(kilitlenme_durum),
                "kilitlenme_suresi": round(kilitlenme_sure, 1),
                "gorev_durumu": ucus_durum,
                "zaman_damgasi": time.time()
            }
            paket_json = json.dumps(veri_paketi).encode('utf-8')
            self.soket.sendto(paket_json, (self.ip, self.port))
        except Exception:
            pass  # Olası ağ bağlantı hataları uçuş güvenliğini etkilememelidir

    def kapat(self):
        self.soket.close()
        print("[GCS] Hakem haberleşme soketi güvenli şekilde kapatıldı.")

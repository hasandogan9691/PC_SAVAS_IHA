import cv2
import numpy as np
import time
import math
import socket
import json
from multiprocessing import Process, Queue, Event
from pymavlink import mavutil

# ============================================================
# SABİTLER
# ============================================================
TOLERANS_PX = 30                 # Merkez kabul edilen piksel toleransı
GEREKLI_KILITLENME_SURESI = 4.0  # Saniye
HEDEF_KAYIP_SURESI = 1.0         # Hedef bu süre görünmezse "kaybedildi" say (titreşimi önler)
ARAMA_YAW_RATE = 0.15            # rad/s - hedef ararken yavaş tarama dönüş hızı
TAKIP_MAKS_YAW_RATE = 0.5        # rad/s
TAKIP_KATSAYI = 0.002
ARAMA_SALINIM_SURESI = 4.0       # Saniye - arama modunda tek yöne tarama yapacağı maksimum süre

# [YENİ] Teknofest Hakem Sunucusu Ayarları (Katman 1)
HAKEM_IP = "127.0.0.1"           # Hakem sunucusu IP adresi (Yarışma alanında verilecek)
HAKEM_PORT = 10000               # Hakem sunucusu UDP portu
HAKEM_GONDERIM_PERIYODU = 0.5    # Saniyede 2 kez (2 Hz) bildirim yap

# [YENİ] Dinamik Tolerans, 3D Takip ve Algılama Sabitleri (Katman 2, 3, 4, 5)
TOLERANS_ORANI = 0.05            # Ekran genişliğinin %5'i dinamik tolerans sayılır
HEDEF_IDEAL_YARICAP = 45.0       # Hedefle korunacak ideal piksel yarıçapı (Mesafe takibi)
ILERLEME_KATSAYISI = 0.015       # İleri/geri hız (vx) oransal katsayısı
DIKEY_KATSAYI = 0.003            # Aşağı/yukarı hız (vz) oransal katsayısı
MAKS_YATAY_HIZ = 1.5             # m/s cinsinden maksimum ileri/geri hız limit
MAKS_DIKEY_HIZ = 1.0             # m/s cinsinden maksimum tırmanma/alçalma limit
TESPIT_MODU = "HSV"              # "HSV" veya "YOLO" (YOLO modelinizi eğittiğinizde burayı değiştirebilirsiniz)

# type_mask: pozisyon+hız+ivme+yaw(mutlak) YOK SAY, sadece yaw_rate KULLAN
# (bit10=YAW_IGNORE=1, bit11=YAW_RATE_IGNORE=0)
YAW_RATE_MASK = 0b0000010111111111  # 1535

# [YENİ] 3D Hareket Maskesi: X, Y, Z Hızları ve Yaw Rate AKTİF (Katman 4)
# bit 0,1,2 (Pozisyon) = 1 | bit 3,4,5 (Hız) = 0 | bit 6,7,8 (İvme) = 1 | bit 10 (Yaw) = 1 | bit 11 (Yaw Rate) = 0
HIZ_VE_YAW_RATE_MASK = 0b0000010111000111  # 1479


# ============================================================
# GÖZ PROSESİ
# ============================================================
def kamera_islem_sureci(veri_kuyrugu, durdur_event):
    gst_pipeline = (
        "udpsrc port=5600 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=H264, payload=96\" ! "
        "rtpjitterbuffer ! "
        "rtph264depay ! "
        "h264parse ! "
        "avdec_h264 ! "
        "videoconvert ! "
        "appsink drop=1"
    )

    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("[GÖZ] Hata: GStreamer boru hattı açılamadı!")
        durdur_event.set()
        return

    print("[GÖZ] Kamera akışı başlatıldı.")

    while not durdur_event.is_set():
        ret, frame = cap.read()
        if not ret:
            continue

        height, width, _ = frame.shape
        center_x, center_y = int(width / 2), int(height / 2)

        cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
        cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 0), 2)

        # [YENİ] Katman 5: Yapay Zeka (YOLO) Hazırlık Altyapısı
        if TESPIT_MODU == "YOLO":
            # YOLO model ağırlıklarını entegre ettiğinizde çıkarım kodları burada çalışacak:
            # blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
            # ... yapay zeka tespit matrisi ...
            pass

        # HSV Renk Filtresi (Simülasyon testleri için ana algılayıcı ve fallback)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([0, 120, 70]), np.array([10, 255, 255]))
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)
        contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        veri = {"tespit": False, "error_x": 0, "error_y": 0, "radius": 0, "width": width, "height": height}

        if len(contours) > 0:
            c = max(contours, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            if radius > 10:
                cv2.circle(frame, (int(x), int(y)), int(radius), (0, 0, 255), 2)
                cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 255), -1)
                error_x = int(x) - center_x
                error_y = int(y) - center_y
                veri = {"tespit": True, "error_x": error_x, "error_y": error_y, "radius": radius, "width": width, "height": height}
                cv2.putText(frame, f"HEDEF: dx={error_x} dy={error_y} r={int(radius)}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        else:
            cv2.putText(frame, "Hedef araniyor...", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Kuyruk her zaman en güncel veriyi tutsun (race-condition'a dayanıklı)
        try:
            while True:
                veri_kuyrugu.get_nowait()
        except Exception:
            pass
        veri_kuyrugu.put(veri)

        cv2.imshow("Teknofest Otonom Göz Paneli", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            durdur_event.set()
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[GÖZ] Proses kapatıldı.")


# ============================================================
# GEOREFERENCING (heading + doğru FOV ile düzeltilmiş)
# ============================================================
def hedef_gps_hesapla(drone_lat, drone_lon, drone_alt, heading_deg,
                       error_x, error_y, image_width, image_height,
                       h_fov_deg=60.0, v_fov_deg=45.0):
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


# [YENİ] Katman 4: 3D Hareket ve Hız Komutu Gönderim Fonksiyonu
def hareket_komutu_gonder(master, vx=0.0, vy=0.0, vz=0.0, yaw_rate=0.0):
    master.mav.set_position_target_local_ned_send(
        0, master.target_system, master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED, HIZ_VE_YAW_RATE_MASK,
        0, 0, 0, vx, vy, vz, 0, 0, 0, 0, yaw_rate
    )


def yaw_hizi_gonder(master, yaw_rate):
    # Orijinal mimari uyumluluğu için sadece yaw_rate gönder, hızları sıfırla
    hareket_komutu_gonder(master, 0.0, 0.0, 0.0, yaw_rate)


# [YENİ] Katman 1: Hakem Sunucusuna UDP ile JSON Paketleme Modülü
def hakem_sunucusuna_bildir(soket_client, hedef_lat, hedef_lon, kilitlenme_durum, kilitlenme_sure, ucus_durum):
    try:
        veri_paketi = {
            "takim_id": 1903,
            "hedef_enlem": round(hedef_lat, 6),
            "hedef_boylam": round(hedef_lon, 6),
            "kilitlenme": int(kilitlenme_durum),  # 0: Yok, 1: Kilitlendi, 2: 4 Sn Tamamlandı
            "kilitlenme_suresi": round(kilitlenme_sure, 1),
            "gorev_durumu": ucus_durum,
            "zaman_damgasi": time.time()
        }
        paket_json = json.dumps(veri_paketi).encode('utf-8')
        soket_client.sendto(paket_json, (HAKEM_IP, HAKEM_PORT))
    except Exception:
        pass  # Olası ağ bağlantı hataları drone'un havada uçuşunu etkilememelidir


# ============================================================
# BEYİN PROSESİ (durum makinesi: ARA / TAKİP / KİLİTLENME)
# ============================================================
DURUM_ARAMA = "ARAMA_VE_DEVRIYE"
DURUM_TAKIP = "HEDEF_TAKIP"


def ucus_beyin_sureci(veri_kuyrugu, durdur_event):
    print("[BEYİN] MAVLink uçuş kontrolcüsüne bağlanılıyor...")
    try:
        master = mavutil.mavlink_connection('udpin:127.0.0.1:14540')
        master.wait_heartbeat()
        print(f"[BEYİN] Bağlantı Başarılı! Sistem ID: {master.target_system}")
    except Exception as e:
        print(f"[BEYİN] Bağlantı Hatası: {e}")
        durdur_event.set()
        return

    # [YENİ] Hakem sunucusu haberleşmesi için UDP soket istemcisi başlat
    hakem_soketi = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    son_hakem_gonderim = time.time()

    aktif_durum = DURUM_ARAMA
    kilitlenme_baslangic = None
    son_gorulme_zamani = None
    arama_yon = 1  # tarama yönü: 1 sağ, -1 sol
    arama_yon_degisim_zamani = time.time()

    drone_lat, drone_lon, drone_alt, heading = 47.397742, 8.545594, 2.5, 0.0
    h_lat, h_lon = 0.0, 0.0

    while not durdur_event.is_set():
        time.sleep(0.02)

        msg = master.recv_match(type=['GLOBAL_POSITION_INT', 'ATTITUDE'], blocking=False)
        if msg:
            if msg.get_type() == 'GLOBAL_POSITION_INT':
                drone_lat = msg.lat / 1e7
                drone_lon = msg.lon / 1e7
                drone_alt = msg.relative_alt / 1000.0
            elif msg.get_type() == 'ATTITUDE':
                heading = math.degrees(msg.yaw) % 360

        try:
            veri = veri_kuyrugu.get_nowait()
        except Exception:
            veri = None

        if veri is not None and veri["tespit"]:
            # ---- HEDEF GÖRÜLDÜ ----
            son_gorulme_zamani = time.time()
            if aktif_durum == DURUM_ARAMA:
                print("[BEYİN] Hedef tespit edildi! Arama modundan takibe geçiliyor.")
                aktif_durum = DURUM_TAKIP
                kilitlenme_baslangic = None

            error_x, error_y = veri["error_x"], veri["error_y"]
            radius, width, height = veri["radius"], veri["width"], veri["height"]

            h_lat, h_lon = hedef_gps_hesapla(drone_lat, drone_lon, drone_alt, heading,
                                             error_x, error_y, width, height)
            print(f"[GPS HEDEF] Enlem: {h_lat:.6f}, Boylam: {h_lon:.6f}")

            # [YENİ] Katman 3: Dinamik Oransal Nişangah Toleransı Hesaplama
            dinamik_tolerans = int(width * TOLERANS_ORANI)

            # [YENİ] Katman 4: Dikey (Z) ve İleri/Geri (X) Eksen Hız Takibi
            # Hedef uzaksa ileri (vx>0), yakınsa geri git (vx<0). Hedef yukarıdaysa tırman (vz<0)
            vx = max(min((HEDEF_IDEAL_YARICAP - radius) * ILERLEME_KATSAYISI, MAKS_YATAY_HIZ), -MAKS_YATAY_HIZ)
            vz = max(min(float(error_y) * DIKEY_KATSAYI, MAKS_DIKEY_HIZ), -MAKS_DIKEY_HIZ)

            if abs(error_x) <= dinamik_tolerans:
                if kilitlenme_baslangic is None:
                    kilitlenme_baslangic = time.time()
                gecen = time.time() - kilitlenme_baslangic
                print(f"[KİLİTLENME] {gecen:.1f}s / {GEREKLI_KILITLENME_SURESI}s")
                
                # [YENİ] Katman 2: 0.0 Hız Riskinin Çözümü -> Yumuşak sönümlü takip
                yumusak_yaw = -float(error_x) * (TAKIP_KATSAYI * 0.4)
                hareket_komutu_gonder(master, vx, 0.0, vz, yumusak_yaw)
                
                if gecen >= GEREKLI_KILITLENME_SURESI:
                    print("[BEYİN] GÖREV BAŞARILI: Kilitlenme tamamlandı.")
            else:
                kilitlenme_baslangic = None
                yaw_rate = max(min(-float(error_x) * TAKIP_KATSAYI, TAKIP_MAKS_YAW_RATE), -TAKIP_MAKS_YAW_RATE)
                hareket_komutu_gonder(master, vx, 0.0, vz, yaw_rate)

        else:
            # ---- HEDEF GÖRÜLMÜYOR (bu tur veri yok ya da tespit=False) ----
            if aktif_durum == DURUM_TAKIP:
                # Anlık kayıp mı yoksa gerçekten kayıp mı ayırt et (titreşim payı)
                if son_gorulme_zamani is not None and (time.time() - son_gorulme_zamani) < HEDEF_KAYIP_SURESI:
                    # Kısa süreli kopma - mevcut komutu koru, aniden arama moduna geçme
                    pass
                else:
                    print("[BEYİN] Hedef kaybedildi! Arama/devriye moduna dönülüyor.")
                    aktif_durum = DURUM_ARAMA
                    kilitlenme_baslangic = None
                    arama_yon_degisim_zamani = time.time()
                    yaw_hizi_gonder(master, 0.0)  # önce dur, sonra tarama başlasın

            if aktif_durum == DURUM_ARAMA:
                # Hedef yokken pasif beklemek yerine yavaş bir tarama (sweep) yap
                if time.time() - arama_yon_degisim_zamani > ARAMA_SALINIM_SURESI:
                    arama_yon *= -1
                    arama_yon_degisim_zamani = time.time()
                    yon_metin = "SAĞA" if arama_yon == 1 else "SOLA"
                    print(f"[ARAMA] Tarama yönü değiştirildi: {yon_metin} sektör taraması.")

                yaw_hizi_gonder(master, ARAMA_YAW_RATE * arama_yon)
                # Not: gerçek görevde burada önceden tanımlı devriye rotası
                # (waypoint listesi) izlenebilir; bu basit sweep bir güvenli varsayılandır.

        # [YENİ] Katman 1: Saniyede 2 Kez Hakem Sunucusuna Canlı Telemetri Bildirimi
        if time.time() - son_hakem_gonderim > HAKEM_GONDERIM_PERIYODU:
            k_durum = 0
            k_sure = 0.0
            if kilitlenme_baslangic is not None:
                k_sure = time.time() - kilitlenme_baslangic
                k_durum = 2 if k_sure >= GEREKLI_KILITLENME_SURESI else 1
            
            hakem_sunucusuna_bildir(hakem_soketi, h_lat, h_lon, k_durum, k_sure, aktif_durum)
            son_hakem_gonderim = time.time()

    yaw_hizi_gonder(master, 0.0)  # çıkışta güvenli dur
    hakem_soketi.close()
    print("[BEYİN] Proses kapatıldı.")


# ============================================================
if __name__ == '__main__':
    print("=== TEKNOFEST OTONOM İHA ANA KARARGAHI (TAM DONANIMLI) ===")

    veri_kuyrugu = Queue()
    durdur_event = Event()

    goz_prosesi = Process(target=kamera_islem_sureci, args=(veri_kuyrugu, durdur_event))
    beyin_prosesi = Process(target=ucus_beyin_sureci, args=(veri_kuyrugu, durdur_event))

    goz_prosesi.start()
    beyin_prosesi.start()

    goz_prosesi.join()
    beyin_prosesi.join()
    print("=== Sistem tamamen kapatıldı ===")

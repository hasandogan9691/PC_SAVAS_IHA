import cv2
import numpy as np
import time
from pymavlink import mavutil

# 1. MAVLink Bağlantısının Kurulması (PX4 SITL Yerel UDP Portu)
print("--- MAVLink Uçuş Kontrolcüsüne Bağlanılıyor... ---")
master = mavutil.mavlink_connection('udpin:127.0.0.1:14540')
master.wait_heartbeat()
print(f"Bağlantı Başarılı! Sistem ID: {master.target_system}, Komponent ID: {master.target_component}")

# GStreamer Canlı Görüntü Akışı Başlatılıyor
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
    print("Hata: GStreamer boru hattı açılamadı!")
    exit()

# Görev Durumları (State Machine)
DURUM_DEVRIYE = "ARAMA_VE_DEVRIYE"
DURUM_TAKIP = "HEDEF_KILITLENME"
aktif_durum = DURUM_DEVRIYE

kilitlenme_baslangic_zamani = None
GEREKLI_KILITLENME_SURESI = 4.0  # 4 saniye kesintisiz kilitlenme

def yaw_hizi_gonder(master, donus_hizi):
    """
    MAVLink üzerinden araca anlık Yaw hızı (dönüş hızı) komutu gönderir.
    donus_hizi: radyan/saniye cinsinden dönüş hızı (+ sağa, - sola)
    """
    # MAVLink SET_POSITION_TARGET_LOCAL_NED mesajı ile hız/yaw_rate komutu
    # //[EK] Bit maskesi '1479' (0b010111000111) olarak güncellendi. Bu maske; pozisyon ve ivme talimatlarını yoksayarken,
    # //[EK] aracın havada olduğu yerde sabit asılı kalması için (Hover) X, Y, Z hızlarını '0' olarak zorlar ve sadece
    # //[EK] bizim gönderdiğimiz 'yaw_rate' (dönüş hızı) komutunu otopilota saf bir şekilde iletir.
    master.mav.set_position_target_local_ned_send(
        0,  # time_boot_ms
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        1479,  # //[EK] Güvenli ve stabil Hover + Yaw Rate bit maskesi (0b010111000111)
        0, 0, 0,  # X, Y, Z pozisyonları (kullanılmıyor)
        0, 0, 0,  # X, Y, Z hızları (aracın yerinde sabit kalması için 0 tutulur)
        0, 0, 0,  # İvme (kullanılmıyor)
        0,        # yaw (açı yoksayılıyor)
        donus_hizi # yaw_rate (dönüş hızı rad/s)
    )

print("--- Otonom Devriye ve MAVLink Hedef Avcısı Aktif ---")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    height, width, _ = frame.shape
    center_x, center_y = int(width / 2), int(height / 2)

    # Merkez Nişangah Çizimi
    cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
    cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 0), 2)

    # Renk Tabanlı Hedef Tespiti (Kırmızı Hedef)
    # //[EK] Kırmızı renk HSV spektrumunda hem 0-10 hem de 170-180 derecelik iki uçta yer aldığından,
    # //[EK] sahadaki ışık değişimlerinde hedefin asla kaçırılmaması için çift aralıklı alt/üst maskeleme entegre edildi.
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2) # //[EK] İki kırmızı tonu tek bir güçlü maskede birleştirildi.

    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    hedef_tespit_edildi = False

    if len(contours) > 0:
        c = max(contours, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)

        if radius > 10:
            hedef_tespit_edildi = True
            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 0, 255), 2)
            cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 255), -1)

            # Yatay Sapma (Error X) Hesaplama
            error_x = int(x) - center_x
            
            if aktif_durum == DURUM_DEVRIYE:
                print("[BEYİN] Hedef tespit edildi! Devriye rotası askıya alındı, takibe geçiliyor.")
                aktif_durum = DURUM_TAKIP
                kilitlenme_baslangic_zamani = time.time()

            # Hedef Merkez Tolerans Alanında mı? (±30 piksel)
            tolerans = 30
            if abs(error_x) <= tolerans:
                gecen_sure = time.time() - kilitlenme_baslangic_zamani
                cv2.putText(frame, f"KILITLENME AKTIF: {gecen_sure:.1f}s", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                # Hedef tam merkezde, dönüşü durdur (0 hız)
                yaw_hizi_gonder(master, 0.0)

                if gecen_sure >= GEREKLI_KILITLENME_SURESI:
                    cv2.putText(frame, "GOREV BASARILI: 4 SN KILITLENME TAMAM!", (10, 90), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    # --- YENİ EKLENEN SÜREKLİ AVLANMA (MULTI-TARGET) TETİKLEYİCİSİ ---
                    print("[BEYİN] Hedef başarıyla avlandı! Yeni hedef aranıyor...")
                    aktif_durum = DURUM_DEVRIYE          # Tekrar arama moduna dön
                    kilitlenme_baslangic_zamani = None   # Sayacı sıfırla
                    time.sleep(1.0)                      # Yeni tur öncesi kısa bir es


            else:
                kilitlenme_baslangic_zamani = time.time()  # Merkezden saparsa süreyi sıfırla
                
                # P-Kontrolcü Mantığı: Sapma miktarına göre orantılı dönüş hızı üret
                # error_x pozitifse sağda (sağa dön), negatifse solda (sola dön)
                katsayi = 0.002  # Hassasiyet katsayısı
                # //[EK] KRİTİK DÜZELTME: Eksi (-) işareti kaldırıldı! PX4 NED koordinat sisteminde sağa dönüş pozitif (+) hıztır.
                # //[EK] Hedef sağdayken (error_x > 0), aracın sağa dönmesi için yaw_rate de pozitif olmalıdır.
                yaw_rate = float(error_x) * katsayi  # Piksel hatasını radyan/saniye hıza çevir
                
                # Dönüş hızını sınırla (maksimum ±0.5 rad/s)
                yaw_rate = max(min(yaw_rate, 0.5), -0.5)

                yaw_hizi_gonder(master, yaw_rate)

                yon = "saga" if error_x > 0 else "sola"
                cv2.putText(frame, f"Hedefe Yoneliniyor ({yon} sapma: {error_x}px)", (10, 60), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    if not hedef_tespit_edildi:
        if aktif_durum == DURUM_TAKIP:
            print("[BEYİN] Hedef kaybedildi! Devriye rotasına geri dönülüyor...")
            aktif_durum = DURUM_DEVRIYE
            kilitlenme_baslangic_zamani = None
            # Hedef kaybolunca drone dönüşü durdurur veya devriye rotasına döner
            # //[EK] Teknofest Doktrini: Hedef kaybedildiği an aracı havada kör gibi durdurmak yerine,
            # //[EK] saniyede ~11 derece (0.2 rad/s) hızla kendi etrafında yavaşça dönerek (Spin Search) aktif hedef araması yapmasını sağladık.
            yaw_hizi_gonder(master, 0.2)

        cv2.putText(frame, "Durum: Arama ve Devriye Rotasi Yurutuluyor...", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        # //[EK] Devriye modunda da aracın etrafını 360 derece taraması için sürekli arama dönüş hızı beslenir.
        yaw_hizi_gonder(master, 0.2)

    cv2.imshow("PX4 Otonom Avci ve Devriye Paneli", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        yaw_hizi_gonder(master, 0.0)  # Çıkışta güvenli olsun diye dönüşü sıfırla
        break

cap.release()
cv2.destroyAllWindows()

import os
import time
import math
from pymavlink import mavutil
# ======= 2. Adım: Uçuş Komut ve Kontrol Modülü (mavlink_commander.py) (236 satir dan 264 satir oldu) ===========

# ============================================================
# MAVLINK MASKELEME (BITMASK) SABİTLERİ
# ============================================================
# Sadece Yaw-Rate kullan (Pozisyon ve Hızları yoksay)
YAW_RATE_MASK = 0b0000010111111111  # 1535

# 3D Hareket Maskesi: X, Y, Z Hızları ve Yaw Rate AKTİF
# bit 0,1,2 (Pozisyon) = 1 | bit 3,4,5 (Hız) = 0 | bit 6,7,8 (İvme) = 1 | bit 10 (Yaw) = 1 | bit 11 (Yaw Rate) = 0
HIZ_VE_YAW_RATE_MASK = 0b0000010111000111  # 1479

# ============================================================
# ARDUPILOT DÖNER KANAT (COPTER) MOD EŞLEME SÖZLÜĞÜ
# ============================================================
ARDUPILOT_COPTER_MODLARI = {
    0: 'STABILIZE',
    1: 'ACRO',
    2: 'ALT_HOLD',
    3: 'AUTO',
    4: 'GUIDED',
    5: 'LOITER',
    6: 'RTL',
    7: 'CIRCLE',
    9: 'LAND',
    11: 'DRIFT',
    13: 'SPORT',
    14: 'FLIP',
    15: 'AUTOTUNE',
    16: 'POSHOLD',
    17: 'BRAKE',
    18: 'THROW',
    19: 'AVOID_ADSB',
    20: 'GUIDED_NOGPS',
    21: 'SMART_RTL',
    22: 'FLOWHOLD',
    23: 'FOLLOW',
    24: 'ZIGZAG',
    25: 'SYSTEMID',
    26: 'AUTOROTATE',
    27: 'AUTO_RTL'
}


def telemetri_akis_frekanslarini_ayarla(master):
    """
    1. İNCELİK (Stream Rate): Otopilotun varsayılan yavaş veri hızını ezip,
    yüksek otonomi için Attitude (50 Hz) ve GPS (10 Hz) akış hızlarını emreder.
    """
    print("[KOMUTAN] Yüksek hızlı telemetri akış frekansları emrediliyor...")
    
    # Attitude (Açı ve Yönelim) verisi -> Saniyede 50 kez (20 milisaniye aralıkla)
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
        mavutil.mavlink.MAVLINK_MSG_ID_ATTITUDE, 20000, 0, 0, 0, 0, 0
    )
    
    # Global Position (GPS ve İrtifa) verisi -> Saniyede 10 kez (100 milisaniye aralıkla)
    master.mav.command_long_send(
        master.target_system, master.target_component,
        mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
        mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT, 100000, 0, 0, 0, 0, 0
    )
    print("[KOMUTAN] Akış frekansları kilitlendi: Attitude=50Hz, GPS=10Hz.")


def saat_senkronizasyonu_baslat(master):
    """
    3. İNCELİK (TIMESYNC): Orange Pi işlemci saati ile Cube Orange+ saatinin
    milisaniye düzeyinde kilitlenmesi için ilk TIMESYNC sinyalini çakar.
    """
    try:
        su_an_ns = int(time.time() * 1e9)
        master.mav.timesync_send(0, su_an_ns)
        print("[KOMUTAN] Donanımlar arası saat senkronizasyonu (TIMESYNC) tetiklendi.")
    except Exception:
        pass  # Senkronizasyon isteği uçuş ana döngüsünü asla engellememelidir


def mavlink_baglantisi_kur(port='/dev/ttyTHS1', baud=921600, simulasyon=False):
    """
    Orange Pi üzerinden Cube Orange+ otopilotuna MAVLink bağlantısı kurar,
    donanım izinlerini denetler, tampon temizliği yapar ve 5 denemeli el sıkışma yapar.
    """
    # A) Donanım Portu Erişim, Varlık ve İzin Doğrulaması
    if not simulasyon and port.startswith('/dev/'):
        print(f"[KOMUTAN] Donanım portu varlığı kontrol ediliyor: {port}")
        if not os.path.exists(port):
            raise FileNotFoundError(f"[HATA] {port} yolu bulunamadı! Orange Pi - Cube kablo bağlantısını kontrol edin.")
        
        print("[KOMUTAN] Okuma/Yazma (R/W) izinleri test ediliyor...")
        if not os.access(port, os.R_OK | os.W_OK):
            raise PermissionError(f"[HATA] {port} portuna erişim izni yok! Terminalde 'sudo usermod -a -G dialout $USER' komutunu çalıştırarak yetki verin.")

    # B) Kütüphane Entegrasyonu ve UART Seri Port Yapılandırması (8N1 varsayılandır)
    print(f"[KOMUTAN] Bağlantı nesnesi başlatılıyor -> Port: {port}, Baud: {baud}")
    try:
        master = mavutil.mavlink_connection(port, baud=baud)
    except Exception as e:
        raise ConnectionError(f"[HATA] Seri port açılamadı: {e}")

    # 2. İNCELİK (Buffer Flushing): El sıkışmadan önce kablodaki eski çöp baytların temizlenmesi
    try:
        if hasattr(master, 'port') and hasattr(master.port, 'flushInput'):
            master.port.flushInput()
            master.port.flushOutput()
            print("[KOMUTAN] UART seri port tampon (buffer) hafızaları tahliye edilip temizlendi.")
    except Exception:
        pass  # UDP simülasyon bağlantılarında tampon temizliği atlanır

    # C) El Sıkışma (Handshake) ve Heartbeat Zaman Aşımı Döngüsü
    print("[KOMUTAN] Otopilot ile el sıkışma (Handshake) başlatılıyor...")
    basarili = False
    maks_deneme = 5
    deneme_zaman_asimi = 2.0  # 5 deneme * 2 saniye = 10 saniye toplam zaman aşımı limiti

    for deneme in range(1, maks_deneme + 1):
        print(f"[KOMUTAN] Heartbeat bekleniyor... (Deneme {deneme}/{maks_deneme})")
        msg = master.wait_heartbeat(blocking=True, timeout=deneme_zaman_asimi)
        
        if msg is not None:
            basarili = True
            break
        else:
            print(f"[UYARI] {deneme}. denemede otopilottan yanıt alınamadı.")

    if not basarili:
        print("[KOMUTAN] 10 saniyelik zaman aşımı süresince otopilottan sinyal alınamadı!")
        master.close()
        raise TimeoutError("[HATA] 5 deneme sonucunda Cube Orange+ ile el sıkışma başarılamadı. Port kapatıldı.")

    # D) Sistem Kimlik (ID) Çözümleme, Kayıt ve Bilgilendirme
    print("------------------------------------------------------------")
    print("[KOMUTAN] EL SIKIŞMA BAŞARILI! Otopilot sinyali alındı.")
    print(f"[KOMUTAN] Aktif Haberleşme Hızı : {baud} Baud (8N1)")
    print(f"[KOMUTAN] Eşleşen System ID     : {master.target_system}")
    print(f"[KOMUTAN] Eşleşen Component ID  : {master.target_component}")
    print("------------------------------------------------------------")

    # Yeni İnce Ayarların Devreye Alınması
    telemetri_akis_frekanslarini_ayarla(master)
    saat_senkronizasyonu_baslat(master)

    return master


def canli_mod_dinleyicisi_baslat(master):
    """
    ADIM 2: Cube Orange+ otopilotundan gelen HEARTBEAT paketlerini sonsuz
    döngüde dinler, custom_mode ve base_mode verilerini ayıklar, silahlanma
    ve acil durum analizlerini yapar, değişimleri zaman damgasıyla loglar.
    """
    print("[KOMUTAN] Canlı Uçuş Modu Dinleyicisi aktif! Mod ve durum değişimleri bekleniyor...")
    eski_mod = None
    eski_armed_durumu = None

    while True:
        try:
            # A) Mesaj Filtreleme & 2. İNCELİK (Timeout Zırhı): 3 saniye limitli bloklayıcı dinleme
            msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=3.0)
            
            if msg is None:
                zaman_damgasi = time.strftime("%H:%M:%S", time.localtime())
                print(f"[{zaman_damgasi}] [UYARI] Telemetri Akışı Kesildi! 3 saniyedir Heartbeat alınamıyor.")
                continue

            # 4. İNCELİK (MAV_TYPE Doğrulaması): Sadece uçağa/döner kanada ait sinyalleri işleme al (GCS/Tracker eleme)
            if msg.type not in [mavutil.mavlink.MAV_TYPE_QUADROTOR, mavutil.mavlink.MAV_TYPE_HEXAROTOR, mavutil.mavlink.MAV_TYPE_OCTOROTOR, mavutil.mavlink.MAV_TYPE_GENERIC]:
                continue

            # B) Ham Mod Verisi Ayıklama: custom_mode ve base_mode ayrıştırması
            ham_custom_mode = msg.custom_mode
            ham_base_mode = msg.base_mode
            
            # C) ArduPilot Mod Eşleme: Ham numarayı metin adına çevirme
            yeni_mod = ARDUPILOT_COPTER_MODLARI.get(ham_custom_mode, f"BILINMEYEN_MOD({ham_custom_mode})")
            
            # 1. İNCELİK (Armed/Disarmed Analizi): base_mode üzerinden motor silahlanma durumunu ayıklama
            yeni_armed_durumu = bool(ham_base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)

            # 3. İNCELİK (Failsafe ve Acil Durum Algılaması): system_status üzerinden kritik durum kontrolü
            durum_notu = ""
            if msg.system_status == mavutil.mavlink.MAV_STATE_CRITICAL:
                durum_notu = " [KRİTİK UYARI: Sistem Kritik Durumda!]"
            elif msg.system_status == mavutil.mavlink.MAV_STATE_EMERGENCY:
                durum_notu = " [ACİL DURUM: Sistem Acil İniş/Müdahale Modunda!]"
            elif msg.system_status == mavutil.mavlink.MAV_STATE_FAILSAFE:
                durum_notu = " [FAILSAFE: Hata Koruması Devrede!]"

            zaman_damgasi = time.strftime("%H:%M:%S", time.localtime())

            # D) Durum Güncelleme Tetikleyicisi (Mod Değişimi Loglama)
            if yeni_mod != eski_mod:
                print(f"[{zaman_damgasi}] Uçuş Modu Değişti: [{eski_mod}] -> [{yeni_mod}]{durum_notu}")
                eski_mod = yeni_mod

            # 1. İNCELİK (Silahlanma Değişimi Loglama)
            if yeni_armed_durumu != eski_armed_durumu:
                silah_metni = "System Armed (Motorlar Silahlandı)" if yeni_armed_durumu else "System Disarmed (Motorlar Kilitlendi)"
                print(f"[{zaman_damgasi}] [SİLAHLANMA DURUMU] -> {silah_metni}")
                eski_armed_durumu = yeni_armed_durumu
                    
        except KeyboardInterrupt:
            print("\n[KOMUTAN] Canlı mod dinleyicisi kullanıcı tarafından sonlandırıldı.")
            break
        except Exception as e:
            print(f"[KOMUTAN] Mod dinleme döngüsünde hata: {e}")
            time.sleep(0.5)


def bekci_ile_baglanti_denetle(master, son_heartbeat_zamani, port='/dev/ttyTHS1', baud=921600, simulasyon=False):
    """
    4. İNCELİK (Watchdog / Auto-Reconnect): Uçuş esnasında motor titreşimi veya kablo
    sarsıntısıyla haberleşme 3 saniyeden fazla koparsa, portu kapatıp yeniden açarak
    havada bağlantıyı kurtarır. Ana döngüde periyodik olarak çağrılmalıdır.
    """
    if time.time() - son_heartbeat_zamani > 3.0:
        print("[BEKÇİ UYARISI] 3 saniyedir otopilot sinyali yok! Bağlantı havada kurtarılıyor...")
        try:
            master.close()
        except Exception:
            pass
        
        try:
            yeni_master = mavlink_baglantisi_kur(port=port, baud=baud, simulasyon=simulasyon)
            print("[BEKÇİ] Bağlantı başarıyla onarıldı! Uçuşa devam ediliyor.")
            return yeni_master, time.time()
        except Exception as e:
            print(f"[BEKÇİ HATA] Yeniden bağlanma başarısız: {e}")
            return master, son_heartbeat_zamani
            
    return master, son_heartbeat_zamani


def hareket_komutu_gonder(master, vx=0.0, vy=0.0, vz=0.0, yaw_rate=0.0):
    """
    İHA'ya lokal eksende m/s cinsinden hız ve rad/s cinsinden
    açısal dönüş (yaw rate) komutu gönderir.
    """
    master.mav.set_position_target_local_ned_send(
        0,
        master.target_system,
        master.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
        HIZ_VE_YAW_RATE_MASK,
        0, 0, 0,          # Pozisyon (Yoksayıldı)
        vx, vy, vz,       # Hız bileşenleri (m/s)
        0, 0, 0,          # İvme (Yoksayıldı)
        0,                # Hedef Yaw Açısı (Yoksayıldı)
        yaw_rate          # Hedef Yaw Dönüş Hızı (rad/s)
    )


def yaw_hizi_gonder(master, yaw_rate):
    """
    Sadece açısal dönüş (yaw) yaptırır, X/Y/Z hızlarını güvenli
    şekilde sıfırlayarak sabiter. (Arama modu ve çıkışlar için ideal)
    """
    hareket_komutu_gonder(master, vx=0.0, vy=0.0, vz=0.0, yaw_rate=yaw_rate)

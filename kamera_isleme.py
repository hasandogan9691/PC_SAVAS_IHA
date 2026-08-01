import cv2
import numpy as np
import time

HSV_ALT_SINIR = np.array([0, 120, 70])
HSV_UST_SINIR = np.array([10, 255, 255])

def gstreamer_pipeline():
    """
    Gecikmeyi ve ilk kare kilitlenmesini önleyen max-buffers=1 ayarlı GStreamer boru hattı.
    """
    return (
        "udpsrc port=5600 ! "
        "application/x-rtp, payload=96 ! "
        "rtph264depay ! "
        "avdec_h264 ! "
        "videoconvert ! "
        "appsink max-buffers=1 drop=true sync=false"
    )

def kamera_islem_sureci(veri_kuyrugu, durdur_event):
    print("[GÖZ] Video boru hattı başlatılıyor...")

    cap = None
    for deneme in range(15):
        if durdur_event.is_set():
            return
        cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
        if cap.isOpened():
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                print(f"[GÖZ] Kamera akışı başarıyla yakalandı! (Deneme {deneme+1})")
                break
        if cap:
            cap.release()
            cap = None
        print(f"[GÖZ UYARI] Akış bekleniyor... (Deneme {deneme+1}/15)")
        time.sleep(1.0)

    if not cap or not cap.isOpened():
        print("[GÖZ HATA] Kamera akışına bağlanılamadı! Proses güvenle sonlandırılıyor.")
        durdur_event.set()
        return

    pencere_adi = "Teknofest Otonom Goz Paneli"
    pencere_acildi_mi = False

    print("[GÖZ] Kamera başarıyla bağlandı, av algılama başlıyor...")

    vurulan_hedefler_listesi = []

    try:
        while not durdur_event.is_set():
            ret, frame = cap.read()

            if not ret or frame is None:
                print("[GÖZ UYARI] Kamera akışından kare alınamadı! Güvenli çıkış yapılıyor...")
                break

            # Pencereyi ilk başarılı kareden SONRA açarak X11/GTK kilitlenmesini engelliyoruz
            if not pencere_acildi_mi:
                cv2.namedWindow(pencere_adi, cv2.WINDOW_NORMAL)
                cv2.resizeWindow(pencere_adi, 640, 480)
                pencere_acildi_mi = True

            height, width, _ = frame.shape
            merkez_x, merkez_y = width // 2, height // 2

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            maske = cv2.inRange(hsv, HSV_ALT_SINIR, HSV_UST_SINIR)

            kernel = np.ones((5, 5), np.uint8)
            maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, kernel)
            maske = cv2.morphologyEx(maske, cv2.MORPH_CLOSE, kernel)

            konturlar, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            tespit_verisi = {"tespit": False}

            cv2.line(frame, (merkez_x - 20, merkez_y), (merkez_x + 20, merkez_y), (0, 255, 0), 2)
            cv2.line(frame, (merkez_x, merkez_y - 20), (merkez_x, merkez_y + 20), (0, 255, 0), 2)

            if konturlar:
                en_iyi_kontur = None
                en_buyuk_alan = 100

                for kontur in konturlar:
                    alan = cv2.contourArea(kontur)
                    if alan > en_buyuk_alan:
                        ((kx, ky), _) = cv2.minEnclosingCircle(kontur)
                        
                        kara_listede_mi = False
                        for (bx, by) in vurulan_hedefler_listesi:
                            mesafe = np.sqrt((kx - bx)**2 + (ky - by)**2)
                            if mesafe < 70:
                                kara_listede_mi = True
                                break
                        
                        if not kara_listede_mi:
                            en_buyuk_alan = alan
                            en_iyi_kontur = kontur

                if en_iyi_kontur is not None:
                    ((x, y), radius) = cv2.minEnclosingCircle(en_iyi_kontur)

                    error_x = int(x - merkez_x)
                    error_y = int(y - merkez_y)

                    tespit_verisi = {
                        "tespit": True,
                        "x": float(x),
                        "y": float(y),
                        "error_x": error_x,
                        "error_y": error_y,
                        "radius": radius,
                        "width": width,
                        "height": height
                    }

                    cv2.circle(frame, (int(x), int(y)), int(radius), (0, 0, 255), 2)
                    cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 255), -1)
                    cv2.line(frame, (merkez_x, merkez_y), (int(x), int(y)), (255, 0, 0), 2)

            # HUD BİLGİ EKRANI (KIRMIZI/YEŞİL YAZILAR)
            # //[EK] Hedef durumuna göre ekrana durum tespiti görsel olarak yansıtılır.
            if tespit_verisi.get("tespit", False):
                cv2.putText(frame, ">> HEDEF KILITLENDI <<", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "-- HEDEF ARANIYOR --", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            try:
                while not veri_kuyrugu.empty():
                    veri_kuyrugu.get_nowait()
                veri_kuyrugu.put_nowait(tespit_verisi)
            except Exception:
                pass

            cv2.imshow(pencere_adi, frame)
            
            # Key event ile pencere kilitlenmesinin önüne geçiyoruz
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                print("[GÖZ] Kullanıcı pencereden çıkış komutu verdi.")
                durdur_event.set()
                break

            # Pencere çarpıdan kapatılırsa prosesi düzgünce sonlandır (yeni ekran açmasını engelle)
            if cv2.getWindowProperty(pencere_adi, cv2.WND_PROP_VISIBLE) < 1:
                print("[GÖZ] Pencere kapatıldı, göz prosesi sonlandırılıyor.")
                durdur_event.set()
                break

    except KeyboardInterrupt:
        print("[GÖZ] Klavye kesintisi algılandı.")
    except Exception as e:
        print(f"[GÖZ HATA] Beklenmeyen hata oluştu: {e}")
    finally:
        print("[GÖZ GÜVENLİK] Kamera bağlantısı kesiliyor ve pencereler temizleniyor...")
        if cap and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        print("[GÖZ] Proses tamamen kapandı.")

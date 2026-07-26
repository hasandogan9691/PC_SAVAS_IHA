import cv2
import numpy as np

# Doğrudan Gazebo'nun UDP 5600 portuna kilitlenen, gecikmesiz saf GStreamer boru hattı
gst_pipeline = (
    "udpsrc port=5600 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=H264, payload=96\" ! "
    "rtpjitterbuffer ! "
    "rtph264depay ! "
    "h264parse ! "
    "avdec_h264 ! "
    "videoconvert ! "
    "appsink drop=1"
)
# [EK] GStreamer boru hattı, Gazebo'dan gelen canlı H.264 video paketlerini donanım ve sistem seviyesinde doğrudan yakalar, ayrıştırır ve OpenCV'ye gecikmesiz (drop=1) bir şekilde iletir. Artık FFMPEG zaman aşımı yaşanmaz.

cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Hata: GStreamer boru hattı açılamadı! Simülasyonun (make px4_sitl gz_x500_mono_cam) açık olduğundan emin olun.")
    print("Not: QGroundControl açıksa video portunu kilitliyor olabilir. QGC üzerinden Video Source ayarını 'No Video' yapın veya QGC'yi kapatıp tekrar deneyin.")
    exit()

print("--- Kamera akışı başladı. Çıkmak için görüntü penceresi üzerindeyken 'q' tuşuna basın. ---")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Kare okunamıyor, bekleniyor...")
        continue

    # Ekran boyutlarını al
    height, width, _ = frame.shape
    center_x, center_y = int(width / 2), int(height / 2)

    # 1. Merkez Nişangahı Çizimi (Görsel Servoing / Hedefleme İçin)
    cv2.line(frame, (center_x - 20, center_y), (center_x + 20, center_y), (0, 255, 0), 2)
    cv2.line(frame, (center_x, center_y - 20), (center_x, center_y + 20), (0, 255, 0), 2)
    # [EK] Otonom İHA avcı veya takip algoritmalarında aracın kamerasının tam merkezi referans noktası (0,0) olarak kabul edilir.

    # 2. Örnek Görüntü İşleme: HSV formatına çevir ve kırmızı tonlarını tespit et
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    mask = cv2.inRange(hsv, lower_red, upper_red)
    # [EK] BGR renk uzayından HSV (Hue, Saturation, Value) uzayına geçiş yapmak, ışık değişimlerinden etkilenmeden belirli bir rengi (bu örnekte kırmızı) maskelemek için en stabil yöntemdir.

    # Gürültüyü azaltmak için morfolojik işlemler
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Konturları (nesne sınırlarını) bul
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        # En büyük konturu (en yakın/büyük hedefi) seç
        c = max(contours, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)

        # Hedef belirli bir büyüklüğün üzerindeyse işle
        if radius > 10:
            # Hedef etrafına çember çiz
            cv2.circle(frame, (int(x), int(y)), int(radius), (0, 0, 255), 2)
            cv2.circle(frame, (int(x), int(y)), 5, (0, 255, 255), -1)

            # Hedefin ekran merkezine göre sapma miktarını (Hata / Error) hesapla
            error_x = int(x) - center_x
            error_y = int(y) - center_y

            # Sapma değerlerini ekrana yazdır
            cv2.putText(frame, f"Hedef Kilitlendi! Sapma X: {error_x}, Y: {error_y}", 
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            # [EK] Hesaplanan bu error_x ve error_y değerleri, bir sonraki aşamada PID kontrolcüsüne beslenerek İHA'nın hedefe doğru yönelmesini (gimbal çevirme veya yaw/pitch açısı verme) sağlayacak olan temel telemetri girdileridir.
    else:
        cv2.putText(frame, "Hedef Araniyor...", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Görüntüleri ekrana bas
    cv2.imshow("PX4 Otonom Kamera Takip Penceresi", frame)

    # 'q' tuşuna basılırsa döngüden çık
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()


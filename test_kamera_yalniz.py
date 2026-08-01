import cv2

gst_pipeline = (
    "udpsrc port=5600 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=H264, payload=96\" ! "
    "rtpjitterbuffer ! "
    "rtph264depay ! "
    "h264parse ! "
    "avdec_h264 ! "
    "videoconvert ! "
    "appsink drop=1"
)

print("[TEST] Kamera bağlanıyor...")
cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("[HATA] GStreamer boru hattı açılamadı! Port kilitli veya GStreamer desteksiz.")
else:
    print("[BAŞARILI] Bağlantı kuruldu, kare bekleniyor...")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("[UYARI] Kare okunamadı, Gazebo yayın yapmıyor olabilir...")
            continue
        
        cv2.imshow("Kamera Test Penceresi", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()

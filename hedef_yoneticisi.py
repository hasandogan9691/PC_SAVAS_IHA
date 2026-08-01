import time
import random
import subprocess

def otomatik_hedef_uret_ve_salaya_birak():
    """
    #[EK] Arka planda rastgele zamanlarda Gazebo simülasyonuna yeni bir kırmızı hedef küre bırakır.
    #[EK] kirmizi_hedef_ekle.py betiğini tetikleyerek sahaya yeni bir av indirir.
    """
    try:
        subprocess.Popen(["python3", "kirmizi_hedef_ekle.py"])
        print("[HEDEF YÖNETİCİSİ] Sahneye yeni bir rastgele kırmızı hedef bırakıldı!")
    except Exception as e:
        print(f"[HEDEF YÖNETİCİSİ HATA] Hedef oluşturulamadı: {e}")

def hedef_yoneticisi_dongusu(durdur_event):
    """
    #[EK] Arka planda bağımsız çalışarak belirli aralıklarla otomatik hedef üretimini tetikler.
    #[EK] İlk hedefi bırakmadan önce drone'un arm olup tırmanışını bitirmesi için 20 saniye bekler.
    """
    print("[HEDEF YÖNETİCİSİ] Otomatik hedef üretim döngüsü başlatıldı.")
    print("[HEDEF YÖNETİCİSİ] İHA'nın kalkıp devriye irtifasına oturması için 20 saniye bekleniyor...")
    
    # Drone'un sensör hatasına girmeden kalkıp havada stabil hale gelmesi için güvenli pay
    time.sleep(20.0)
    
    # İlk hedefi sahaya bırakıyoruz
    if not durdur_event.is_set():
        otomatik_hedef_uret_ve_salaya_birak()
    
    while not durdur_event.is_set():
        # Bir sonraki hedef için sahayı çok boğmadan 10 ile 15 saniye arasında rastgele bekle
        bekleme_suresi = random.uniform(10.0, 15.0)
        baslangic = time.time()
        
        while time.time() - baslangic < bekleme_suresi:
            if durdur_event.is_set():
                print("[HEDEF YÖNETİCİSİ] Durdurma sinyali alındı, döngü kapatılıyor.")
                return
            time.sleep(0.5)
            
        if not durdur_event.is_set():
            otomatik_hedef_uret_ve_salaya_birak()

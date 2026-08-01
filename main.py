import time
import socket
import multiprocessing as mp

from ucus_kontrolcusu import UcusKontrolcusu
from kamera_isleme import kamera_islem_sureci
from hedef_yoneticisi import hedef_yoneticisi_dongusu

# ============================================================
# HAKEM SUNUCUSU (UDP BAĞLANTISI)
# ============================================================
HAKEM_IP = "127.0.0.1"
HAKEM_PORT = 10000
hakem_soketi = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def hakem_masasina_bildir(mesaj):
    try:
        hakem_soketi.sendto(mesaj.encode('utf-8'), (HAKEM_IP, HAKEM_PORT))
    except Exception:
        pass

# ============================================================
# ANA KARARGAH (BEYİN VE DURUM MAKİNESİ)
# ============================================================
def main():
    print("[BEYİN] Ana karargah uyandırılıyor, DİNAMİK AV döngüsü başlatılıyor...")

    ucus = UcusKontrolcusu()
    ucus.baglan()

    veri_kuyrugu = mp.Queue()
    durdur_event = mp.Event()

    goz_prosesi = mp.Process(target=kamera_islem_sureci, args=(veri_kuyrugu, durdur_event))
    goz_prosesi.daemon = True
    goz_prosesi.start()

    hedef_prosesi = mp.Process(target=hedef_yoneticisi_dongusu, args=(durdur_event,))
    hedef_prosesi.daemon = True
    hedef_prosesi.start()

    kalkis_yapildi_mi = False
    kilitlenme_baslangic_zamani = None
    kilitlenme_hedef_suresi = 4.0
    son_hedef_x = 320
    son_hedef_y = 240
    
    # //[EK] Dinamik hedef takibi için "Av Hafızası" değişkenleri eklendi.
    son_hedef_gorme_zamani = 0
    hafiza_suresi = 1.0  # Hedef kadrajdan çıkarsa 1 saniye boyunca aramaya devam et
    son_vx, son_vy, son_vz = 1.0, 0.0, 0.0

    print("[BEYİN] Otonom devriye ve avcı hafızası devrede...")

    try:
        while not durdur_event.is_set():
            
            if not kalkis_yapildi_mi:
                print("\n[BEYİN] Otonom kalkış gerçekleştiriliyor ve tarama moduna geçiliyor...")
                ucus.otonom_kalkis_ve_saldiri_baslat(hedef_irtifa=2.5)
                kalkis_yapildi_mi = True
                time.sleep(2.0)
                continue

            if veri_kuyrugu.empty():
                time.sleep(0.01)
                continue

            tespit_verisi = veri_kuyrugu.get()
            hedef_bulundu = tespit_verisi.get("tespit", False)
            su_an = time.time()

            if hedef_bulundu:
                # //[EK] Hedefi gördüğümüz son anı hafızaya kaydediyoruz.
                son_hedef_gorme_zamani = su_an

                if kilitlenme_baslangic_zamani is None:
                    kilitlenme_baslangic_zamani = su_an
                    print("\n[AVCI] Dinamik hedef tespit edildi, kilitleniliyor!")

                son_hedef_x = tespit_verisi.get("x", 320)
                son_hedef_y = tespit_verisi.get("y", 240)

                merkez_x = tespit_verisi.get("error_x", 0)
                merkez_y = tespit_verisi.get("error_y", 0)

                # //[EK] Hız ve reaksiyon katsayısı (0.005 -> 0.008) artırıldı, avcı daha agresif manevra yapacak.
                son_vx = 2.5               
                son_vy = merkez_x * 0.008    
                son_vz = merkez_y * 0.008    

                ucus.hiz_komutu_gonder(son_vx, son_vy, son_vz)

                gecen_sure = su_an - kilitlenme_baslangic_zamani
                durum_metni = f"[KİLİTLENME] {gecen_sure:.1f}s / {kilitlenme_hedef_suresi}s (Hız -> İleri: {son_vx}m/s, Yan: {son_vy:.1f}m/s)"
                print(durum_metni)
                hakem_masasina_bildir(durum_metni)

                if gecen_sure >= kilitlenme_hedef_suresi:
                    zafer_metni = f"[BEYİN] GÖREV BAŞARILI: Dinamik ({son_hedef_x:.1f}, {son_hedef_y:.1f}) hedef havada vuruldu!"
                    print(f"\n{zafer_metni}\n")
                    hakem_masasina_bildir(zafer_metni)
                    
                    ucus.hiz_komutu_gonder(0, 0, 0)
                    kilitlenme_baslangic_zamani = None
                    son_hedef_gorme_zamani = 0
                    time.sleep(1.0)

            else:
                # //[EK] HEDEF HAFIZASI: Hedef kaybolduysa ama henüz hafıza süresi (1.0s) dolmadıysa, sayacı sıfırlama!
                if (su_an - son_hedef_gorme_zamani) < hafiza_suresi:
                    # //[EK] Son bilinen hızı koruyarak avı körleme takip etmeye devam et
                    ucus.hiz_komutu_gonder(son_vx, son_vy, son_vz)
                else:
                    # //[EK] 1 Saniye geçti ve hedef dönmedi. Tamamen kaçtı, sayacı sıfırla ve devriyeye dön.
                    ucus.hiz_komutu_gonder(1.0, 0.0, 0.0)
                    if kilitlenme_baslangic_zamani is not None:
                        print("[AVCI] Hedefin izi tamamen kaybedildi! Sayaç sıfırlandı, devriyeye dönülüyor...")
                    kilitlenme_baslangic_zamani = None

    except KeyboardInterrupt:
        print("[BEYİN] Klavye kesintisi algılandı, sistem kapatılıyor.")
    finally:
        durdur_event.set()
        goz_prosesi.join(timeout=2.0)
        hedef_prosesi.join(timeout=2.0)
        print("[BEYİN] Ana karargah güvenle kapatıldı.")

if __name__ == "__main__":
    main()

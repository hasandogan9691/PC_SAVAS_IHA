import time

class DevriyeKesifYoneticisi:
    def __init__(self):
        self.devriye_aktif = True
        self.arama_sayaci = 0

    def saha_taramasi_yap(self):
        """
        Hedef henüz bulunamadığında uçağın sahada arama yapmasını 
        veya devriye tarama rotasını yürütmesini sağlar.
        """
        self.arama_sayaci += 1
        print(f"[KEŞİF] Saha taranıyor... Devriye turu: {self.arama_sayaci}")
        
        # Burada gerekirse otopilota küçük arama manevraları (yaw dönüşleri vb.) 
        # veya waypoint komutları verilebilir.
        time.sleep(0.5)
        
    def kesif_durumunu_sifirla(self):
        self.arama_sayaci = 0
        print("[KEŞİF] Hedef tespit edildi, keşif modu durduruluyor, taarruza geçiliyor!")


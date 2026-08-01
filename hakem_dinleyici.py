import socket

def hakem_sunucusu_baslat():
    IP = "127.0.0.1"
    PORT = 10000
    
    # UDP Soketini kur
    soket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    soket.bind((IP, PORT))
    
    print(f"\n[HAKEM MASASI] {IP}:{PORT} üzerinden canli dinlemede...")
    print("[HAKEM MASASI] İHA'dan gelecek kilitlenme raporları bekleniyor...\n" + "="*50)
    
    try:
        while True:
            veri, adres = soket.recvfrom(1024)
            mesaj = veri.decode('utf-8')
            print(f">> {mesaj}")
    except KeyboardInterrupt:
        print("\n[HAKEM MASASI] Sunucu kapatildi.")
        soket.close()

if __name__ == "__main__":
    hakem_sunucusu_baslat()

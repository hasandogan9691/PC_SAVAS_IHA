import requests
import json
import os

# Ollama'nın Karargah içindeki yerel iletişim adresi
OLLAMA_API_URL = "http://localhost:11434/api/chat"
DOKTRIN_DOSYASI = "subay_doktrin.txt"

def doktrin_oku():
    """Subayın kurallarını harici txt dosyasından okur."""
    try:
        with open(DOKTRIN_DOSYASI, "r", encoding="utf-8") as dosya:
            return dosya.read()
    except FileNotFoundError:
        print(f"KRİTİK HATA: {DOKTRIN_DOSYASI} bulunamadı! Subay kuralsız başlatılamaz.")
        exit()

def subayla_konus():
    print("="*60)
    print("🛡️ ÖZEL YAPAY ZEKA RİSK SUBAYI DEVREDE 🛡️")
    print(f"Kurallar '{DOKTRIN_DOSYASI}' dosyasından yüklendi.")
    print("Çıkmak ve subayı uyutmak için 'kapat' yazın.")
    print("="*60)

    # Kuralları dosyadan çek ve hafızaya yerleştir
    system_prompt = doktrin_oku()
    mesaj_gecmisi = [
        {"role": "system", "content": system_prompt}
    ]

    while True:
        kullanici_girdisi = input("\nMareşal: ")
        
        if kullanici_girdisi.lower() == 'kapat':
            print("\nSubay: Emredersiniz Komutanım. Nöbeti devrediyorum, yollarınız açık olsun.")
            break
            
        if not kullanici_girdisi.strip():
            continue

        mesaj_gecmisi.append({"role": "user", "content": kullanici_girdisi})

        payload = {
            "model": "llama3",
            "messages": mesaj_gecmisi,
            "stream": False
        }

        try:
            print("Subay Düşünüyor...", end="\r")
            response = requests.post(OLLAMA_API_URL, json=payload)
            response.raise_for_status()
            
            subay_cevabi = response.json()["message"]["content"]
            print(" "*20, end="\r") # Düşünüyor yazısını temizle
            print(f"Risk Subayı: {subay_cevabi}")
            
            # Subayın cevabını da hafızaya ekle ki sohbetin akışını unutmasın
            mesaj_gecmisi.append({"role": "assistant", "content": subay_cevabi})
            
        except requests.exceptions.RequestException as e:
            print(f"\nBağlantı Hatası: Karargah motoru (Ollama) yanıt vermiyor. Lütfen 'ollama list' ile motorun çalıştığını teyit edin. Detay: {e}")

if __name__ == "__main__":
    subayla_konus()

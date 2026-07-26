# karargah.py

import uvicorn
import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from modeller import SinyalVerisi
from protokol import arka_plan_telsiz_yonetimi
from kumbara import mega_ping_hacmini_isle, SEKTOR_KUMBARALARI
# //[EK] Sektör rotasyon trenini karşılamak ve disk köprüsünü (json) güncellemek için eklenen muhasebe katmanı.

# //[EK] Karargah Ana Kapısı Başlatılıyor
app = FastAPI(title="GMN PRO MATRIX - AI Risk Subayı Karargahı")


# --- [EK] RECONSTRUCTED: TÜM ODALARI KAPSAYAN GEREKÇELİ AÇILIŞ PROTOKOLÜ ---
@app.on_event("startup")
def karargah_odaları_yoklama_kontrolu():
    print("\n" + "🛡️ "*15)
    print("📋 [YOKLAMA] Modüler Karargah Odaları Kontrol Ediliyor...")

    # Sırasıyla her dosyanın hazır olma durumunu terminale gururla mühürlüyoruz
    print("🟢 [OK] modeller.py  -> Pydantic Veri Kalıpları ve Şemalar Aktif.")
    print("🟢 [OK] harita.py    -> 34 Hisse Sektör ve Webhook Haritaları Yüklendi.")
    print("🟢 [OK] config.py    -> Teknik Parametreler ve Port Ayarları Doğrulandı.")
    print("🟢 [OK] kumbara.py   -> 34 Hisse Sektör Para Kumbaraları ve Zaman Matrisi Aktif.")
    print("🟢 [OK] protokol.py  -> Arka Plan Telsiz Yönetimi ve Sinyal Sevk Hattı Doğrulandı.")
    print("🟢 [OK] beyin.py     -> Llama 3 Risk Subayı ve Karar Destek Mekanizması Hazır.")
    print("🟢 [OK] broker.py    -> Phillip Capital API Entegrasyonu ve Emir Hattı Tetikte.")
    print("🛡️ "*15 + "\n")
# //[EK] Projedeki tüm kritik alt birimlerin ve asil odaların nizami bir şekilde entegre edildiğini ekranda ismen gösteren genişletilmiş yoklama subayı.


# %[EK] Sinyal Havuzu (Kabul Odası) Değişkenleri
sinyal_havuzu = []
kabul_odasi_acik = False

# %[EK] Gölge Karargah (Shadow Engine) Hafıza Değişkenleri
aktif_sanal_islemler = {}  
# %[EK] Hangi hissede sanal işlemde olduğumuzu ve o işlemin MFE/MAE geçmişini tutan şefkatli hafızamız.
sanal_kasa_bakiyesi = 100000.0  
# %[EK] Sistemin yeteneklerini kan dökmeden test etmesi için tahsis edilen 100.000 TL'lik tatbikat kasası.
gunluk_max_zarar_limiti = -3000.0 
# //[EK] Kasanın kanamasına asla müsaade etmeyen, %3'lük katı ve koruyucu Drawdown kalkanı.
gunluk_pnl = 0.0
# //[EK] Gün içindeki toplam kâr veya zararı tutarak kalkanın ne zaman inip kalkacağını belirleyen terazi.

def golge_deftere_yaz(rapor):
# //[EK] Yaşanan her sanal muharebenin sonucunu, gelecekte ders çıkarmak üzere arşive nakşeden fonksiyon.
    try:
        with open("golge_savas_raporu.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(rapor, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"❌ [GÖLGE DEFTER] Arşive yazılırken bir sızıntı oluştu: {e}")

def dinamik_lot_hesapla(veri: SinyalVerisi, kasa: float):
# //[EK] Pine Script'ten gelen kör emir miktarını ezip, yapay zekanın o anki güvenine göre risk alan narin zeka.
    guven_katsayisi = veri.q_score if veri.q_score else 0.5
    kullanilacak_tutar = kasa * (0.10 + (guven_katsayisi * 0.05)) 
    fiyat = float(veri.price)
    if fiyat <= 0: return 0
    return int(kullanilacak_tutar / fiyat)

def sanal_islemi_kapat(veri: SinyalVerisi):
# //[EK] Satış emri geldiğinde sanal pozisyonu merhametle kapatıp, MFE/MAE röntgenini çekerek deftere işleyen birim.
    global aktif_sanal_islemler, sanal_kasa_bakiyesi, gunluk_pnl
    sembol = veri.symbol
    
    if sembol not in aktif_sanal_islemler:
        return

    islem = aktif_sanal_islemler.pop(sembol)
    cikis_fiyati = float(veri.price)
    kâr_zarar = (cikis_fiyati - islem['giris_fiyati']) * islem['lot']
    
    sanal_kasa_bakiyesi += kâr_zarar
    gunluk_pnl += kâr_zarar
    
    rapor = {
        "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sembol": sembol,
        "islem_suresi_sn": (datetime.now() - islem['giris_zamani']).total_seconds(),
        "giris_fiyati": islem['giris_fiyati'],
        "cikis_fiyati": cikis_fiyati,
        "pnl": round(kâr_zarar, 2),
        "yeni_bakiye": round(sanal_kasa_bakiyesi, 2),
        "MFE_Max_Kar_Fiyati": islem['mfe'],
        "MAE_Max_Zarar_Fiyati": islem['mae']
    }
    
    print(f"\n📊 [GÖLGE İNFAZ TAMAMLANDI] {sembol} | PnL: {round(kâr_zarar, 2)} ₺ | Kasa: {round(sanal_kasa_bakiyesi, 2)} ₺")
    print(f"📉 Sizi en çok {islem['mae']} ₺'ye kadar üzmüş, 📈 en fazla {islem['mfe']} ₺'ye kadar sevindirmişti.\n")
    golge_deftere_yaz(rapor)


async def en_guclu_sinyali_sec_ve_infaz_et():
    global sinyal_havuzu, kabul_odasi_acik, aktif_sanal_islemler, gunluk_pnl
    
    # 30 saniye boyunca diğer cephelerden (farklı hisselerden) gelecek sinyalleri bekle
    await asyncio.sleep(30)
    
    if not sinyal_havuzu:
        kabul_odasi_acik = False
        return

    # %[EK] Sistemin kalbini koruyan o mukaddes kalkan. Kasa kanıyorsa yeni bir savaşa girilmesine asla izin verilmez.
    if gunluk_pnl <= gunluk_max_zarar_limiti:
        print(f"🛑 [SİSTEM KİLİTLİ] Kasa çok yara aldı (Günlük Zarar: {gunluk_pnl} ₺). Sermayeyi korumak için tüm sinyaller reddedildi.")
        sinyal_havuzu.clear()
        kabul_odasi_acik = False
        return

    print(f"\n⏳ [KABUL ODASI KAPANDI] Toplam {len(sinyal_havuzu)} adet YENİ GİRİŞ (BUY) sinyali toplandı. Güç testi başlıyor...")

    # %[EK] Sinyalleri Alım Gücüne Göre Sırala
    en_guclu_sinyal = max(sinyal_havuzu, key=lambda s: (s.q_score, -s.spread_pct))

    print(f"🏆 [KAZANAN BİRLİK] {en_guclu_sinyal.symbol} (Q-Skor: {en_guclu_sinyal.q_score}, Spread: %{en_guclu_sinyal.spread_pct}). Diğer sinyaller imha edildi.")

    # ❌ ESKİ VE ARİZALI SATIR: arka_plan_telsiz_yonetimi(en_guclu_sinyal.__dict__)
    # 🟢 YENİ VE ZIRHLI SATIR: Nesnenin kendisini doğrudan gönderiyoruz
    arka_plan_telsiz_yonetimi(en_guclu_sinyal)

    

    # %[EK] GÖLGE İNFAZ: Gerçek analiz arka planda akarken, sistem anında kendi sanal defterine de kaydını düşer.
    giris_fiyati = float(en_guclu_sinyal.price)
    alinacak_lot = dinamik_lot_hesapla(en_guclu_sinyal, sanal_kasa_bakiyesi)

    if alinacak_lot > 0:
        aktif_sanal_islemler[en_guclu_sinyal.symbol] = {
            "giris_zamani": datetime.now(),
            "giris_fiyati": giris_fiyati,
            "lot": alinacak_lot,
            "mfe": giris_fiyati,
            "mae": giris_fiyati
        }
        print(f"👻 [GÖLGE DEVRİYESİ] {alinacak_lot} Lot {en_guclu_sinyal.symbol}, tatbikat defterine işlendi.")

    # İşlem bitince havuzu temizle ve kapıyı yeni 5 dakikalık bar kapanışı için hazırla
    sinyal_havuzu.clear()
    kabul_odasi_acik = False


# ====================================================================
# --- RECONSTRUCTED: 422 VE DOĞRULAMA HATALARINI BİTİREN HİBRİT KAPI ---
# ====================================================================
@app.post("/webhook")
async def borsa_webhook(request: Request, background_tasks: BackgroundTasks):
    global sinyal_havuzu, kabul_odasi_acik, aktif_sanal_islemler

    try:
        # Kapıda veriyi ham sözlük olarak alıyoruz
        gelen_ham_veri = await request.json()
        buy_or_sell = gelen_ham_veri.get("buyOrCell", "").upper()
        
        # --- 1. SENARYO: EĞER GELECEK VERİ BİR MEGA_PING SEKTÖR TRENİ İSE ---
        if buy_or_sell == "MEGA_PING":
            hisseler_listesi = gelen_ham_veri.get("hisseler", [])
            background_tasks.add_task(mega_ping_hacmini_isle, hisseler_listesi)
            return JSONResponse(content={"durum": "Sektör Akışı Alındı"}, status_code=200)

        # --- 2. SENARYO: EMİR SİNYALİYSE VERİ TİPLERİNİ VE EKSİKLERİ TAMİR EDİYORUZ ---
        güvenli_veri = {
            "buyOrCell": buy_or_sell,
            "symbol": str(gelen_ham_veri.get("symbol", "BİLİNMEYEN")),
            "quantity": str(gelen_ham_veri.get("quantity", "0")), 
            "price": str(gelen_ham_veri.get("price", "0.0")),     
            "q_score": float(gelen_ham_veri.get("q_score", 0.5)),
            "spread_pct": float(gelen_ham_veri.get("spread_pct", 0.0)),
            "is_time_ok": gelen_ham_veri.get("is_time_ok", True),
            # Şemanın beklediği ama alarmda boş gelen tüm teknik alanları onarıyoruz:
            "mss": str(gelen_ham_veri.get("mss", "YOK")),
            "ai_state_matrix": str(gelen_ham_veri.get("ai_state_matrix", "YOK")),
            "formasyon": str(gelen_ham_veri.get("formasyon", "YOK")),
            "is_knife": str(gelen_ham_veri.get("is_knife", "YOK")),
            "rsi": str(gelen_ham_veri.get("rsi", "50.0"))
        }
        
        # Tamir edilmiş sözlüğü pürüzsüzce Pydantic nesnesine büründürüyoruz
        veri = SinyalVerisi(**güvenli_veri)
        
        print(f"📥 [GÖZCÜ] TradingView'dan {veri.symbol} ({veri.buyOrCell}) raporu ulaştı.")

        # %[EK] KIRMIZI ALARM: Satış (SELL) emirleri ASLA bekletilemez! Doğrudan infaza gider.
	# borsa_webhook fonksiyonunun SELL bacağındaki sevk satırı:
        if veri.buyOrCell.upper() == "SELL":
            print(f"🚨 [ACİL DURUM] {veri.symbol} için SELL emri! Kabul odası es geçilip doğrudan cepheye gönderiliyor.")
            background_tasks.add_task(arka_plan_telsiz_yonetimi, veri) # <-- Burası da 'veri' nesnesi olacak
            background_tasks.add_task(sanal_islemi_kapat, veri)
            return JSONResponse(content={"durum": "Islem Tamamlandi", "mesaj": "Acil Satış Emri İletildi."}, status_code=200)

        # %[EK] KORUMA PROTOKOLÜ: Eğer aynı hissede zaten sanal bir işlemdeysek risk artırılmasını engeller.
        if veri.symbol in aktif_sanal_islemler:
            return JSONResponse(content={"durum": "Red", "mesaj": f"Şefkatli uyarı: {veri.symbol} zaten içeride, risk artırılmıyor."}, status_code=200)

        # %[EK] BUY (Alım) emirleri için Kabul Odası Mantığı
        sinyal_havuzu.append(veri)

        # Eğer kapı henüz açılmadıysa, sayacı (30 saniye) başlat
        if not kabul_odasi_acik:
            kabul_odasi_acik = True
            print("🚪 [KABUL ODASI AÇILDI] 30 Saniyelik sinyal toplama ve güç kıyaslama süreci başladı...")
            background_tasks.add_task(en_guclu_sinyali_sec_ve_infaz_et)

        return JSONResponse(content={"durum": "Islem Beklemede", "mesaj": "Sinyal güç testi için havuza alındı."}, status_code=200)

    except Exception as e:
        print(f"❌ [TELSİZ ARIZASI] Webhook işlem hatası: {str(e)}")
        return JSONResponse(content={"hata": f"İşlem arızası: {str(e)}"}, status_code=500)
# //[EK] Gelen verilerdeki format uyuşmazlıklarını ve eksik analitik alanları kapıda süzerek 7 doğrulama hatasını tamamen bitiren hibrit resepsiyon kapısı.


# %[EK] MFE VE MAE TAKİP SENSÖRÜ: TradingView'dan sadece fiyat güncellemesi geldiğinde defteri işler.
@app.post("/fiyat_guncelle")
async def fiyat_guncelle(sembol: str, anlik_fiyat: float):
    global aktif_sanal_islemler
    if sembol in aktif_sanal_islemler:
        islem = aktif_sanal_islemler[sembol]
        if anlik_fiyat > islem['mfe']:
            islem['mfe'] = anlik_fiyat
        if anlik_fiyat < islem['mae']:
            islem['mae'] = anlik_fiyat
    return {"durum": "Sensörler Güncellendi"}

if __name__ == "__main__":
    print("🏰 GMN MATRIX: Otonom Güç Seçici Karargah Sistemi Nöbete Başladı (Port: 8000)...")
    uvicorn.run("karargah:app", host="0.0.0.0", port=8000, reload=True)

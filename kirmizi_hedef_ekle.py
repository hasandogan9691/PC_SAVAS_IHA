import os
import subprocess
import time
import random

# ============================================================
# KIRMIZI HEDEF MODELİ (SDF - Simülasyon Tanım Formatı)
# ============================================================
# Kameramızın anında aşık olacağı kıpkırmızı, pürüzsüz bir küre modeli
# [EK] İkinci etap için model dinamik (hareketli) hale getirildi ve fiziksel kütle eklendi.
SDF_ICERIGI = """<?xml version="1.0" ?>
<sdf version="1.6">
  <model name="kirmizi_hedef">
    <static>false</static>
    <link name="link">
      <gravity>false</gravity>
      <inertial>
        <mass>0.5</mass>
        <inertia>
          <ixx>0.01</ixx>
          <iyy>0.01</iyy>
          <izz>0.01</izz>
        </inertia>
      </inertial>
      <pose>0 0 0 0 0 0</pose>
      <visual name="visual">
        <geometry>
          <sphere>
            <radius>0.35</radius>
          </sphere>
        </geometry>
        <material>
          <ambient>1 0 0 1</ambient>
          <diffuse>1 0 0 1</diffuse>
          <specular>0.1 0.1 0.1 1</specular>
        </material>
      </visual>
    </link>
  </model>
</sdf>
"""

def kirmizi_hedef_birak():
    print("=== OTONOM AV BIRAKMA PROSESİ (DİNAMİK) ===")

    # 1. SDF dosyasını işletim sisteminin geçici hafızasına yazıyoruz
    dosya_yolu = "/tmp/kirmizi_hedef.sdf"
    with open(dosya_yolu, "w") as f:
        f.write(SDF_ICERIGI)
    print(f"[1/4] Kırmızı hedef modeli oluşturuldu: {dosya_yolu}")

    # 2. İHA'nın tam ön görüş açısı (X: 3.0m ileri, Y: 0.0m merkez, Z: 1.2m yükseklik)
    # [EK] Hedefin sahaya ineceği Y ekseni (sağ/sol) artık rastgele belirleniyor.
    x = 4.0
    y = random.uniform(-3.0, 3.0)
    z = 1.2

    req_metni = f'sdf_filename: "{dosya_yolu}", pose: {{position: {{x: {x}, y: {y}, z: {z}}}}}, name: "kirmizi_hedef"'

    # Gazebo/Ignition dünyasının gerçek adını (default, empty vb.) otomatik buluyoruz
    print("[2/4] Çalışan Gazebo dünyası ve servisleri taranıyor...")

    araclar = [("gz", "gz.msgs.EntityFactory", "gz.msgs.Boolean"), ("ign", "ign.msgs.EntityFactory", "ign.msgs.Boolean")]
    basarili = False
    aktif_komut_adi = "gz"
    aktif_hedef_servis = ""

    for komut_adi, req_type, rep_type in araclar:
        try:
            # Çalışan servis listesini al ve '/world/.../create' servisini bul
            servis_listesi = subprocess.check_output([komut_adi, "service", "-l"], text=True, stderr=subprocess.STDOUT)

            hedef_servis = None
            for satir in servis_listesi.splitlines():
                if "/create" in satir and "/world/" in satir:
                    hedef_servis = satir.strip()
                    break

            if hedef_servis:
                print(f"-> Aktif dünya servisi otomatik tespit edildi: {hedef_servis} ({komut_adi} aracı ile)")
                # DÜZELTME: --repotype parametresi --reptype olarak düzeltildi
                komut = [komut_adi, "service", "-s", hedef_servis, "--reqtype", req_type, "--reptype", rep_type, "--timeout", "3000", "--req", req_metni]

                sonuc = subprocess.run(komut, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if sonuc.returncode == 0:
                    print("[3/4] BAŞARILI! Kıpkırmızı hedefimiz sahaya indirildi.")
                    basarili = True
                    aktif_komut_adi = komut_adi
                    aktif_hedef_servis = hedef_servis
                    break
                else:
                    print(f"[DETAYLI HATA] Servis komutu reddedildi: {sonuc.stderr or sonuc.stdout}")
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    if not basarili:
        print("\n[UYARI] Otomatik ekleme yapılamadı! Lütfen 1. Terminalde Gazebo'nun açık olduğundan emin olun.")
        print("Eğer Gazebo açıksa terminalde şu komutu çalıştırıp hata detayına bakabiliriz:")
        print(f"gz service -s /world/default/create --reqtype gz.msgs.EntityFactory --reptype gz.msgs.Boolean --req '{req_metni}'")
        return
    
    # [EK] 4. Aşama: Dinamik Hareket Motoru
    # Hedef sahaya indikten sonra sürekli hareket etmesi için pozisyon güncelleyen bir döngü.
    print("\n[4/4] Hedef hareket motoru ateşleniyor! Avımız artık kaçıyor...")
    
    dunya_adi = aktif_hedef_servis.split("/world/")[1].split("/")[0]
    set_pose_servis = f"/world/{dunya_adi}/set_pose"
    set_pose_req_type = f"{aktif_komut_adi}.msgs.Pose"
    set_pose_rep_type = f"{aktif_komut_adi}.msgs.Boolean"

    hareket_yonu = random.choice([-1, 1])
    hiz = 1.0  # Saniyede 1.0 metre hızla sağa/sola kaçacak

    print(f"-> Hedef şu an {('Sola' if hareket_yonu == -1 else 'Sağa')} doğru agresif manevralarla kaçıyor!")

    try:
        # [EK] Sonsuz ping-pong döngüsü. subprocess.Popen ile çağrıldığı için ana programı bloklamaz.
        while True:
            y += hareket_yonu * (hiz * 0.1)
            
            # Sağ ve sol sınırlar (-5 metre ile +5 metre arası)
            if y > 5.0 or y < -5.0:
                hareket_yonu *= -1

            pose_req = f'name: "kirmizi_hedef", position: {{x: {x}, y: {y}, z: {z}}}'
            komut_pose = [aktif_komut_adi, "service", "-s", set_pose_servis, "--reqtype", set_pose_req_type, "--reptype", set_pose_rep_type, "--req", pose_req]
            
            subprocess.run(komut_pose, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n[BİLGİ] Hedef hareketi durduruldu.")

if __name__ == "__main__":
    kirmizi_hedef_birak()

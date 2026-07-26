import random

class MockVisionProcessor:
    def __init__(self):
        # Ekran çözünürlük standartları: 640x480
        self.width = 640
        self.height = 480
        self.cam_center_x = 320
        self.cam_center_y = 240
        
        # Rakip İHA ilk başta ekranın sağ üst köşesinde başlasın
        self.mock_x = 500
        self.mock_y = 100
        self.frame_count = 0

    def get_target_coordinates(self, drone_moving=False, yaw_rate=0.0):
        self.frame_count += 1
        
        # Bizim drone hedefe doğru manevra yaptıkça, rakip kadraj merkezine yaklaşır
        if drone_moving:
            # Dönüş hızına (yaw_rate) göre hedefi matematiksel olarak merkeze çeken regülasyon
            self.mock_x -= int(yaw_rate * 300)
            self.mock_y += random.randint(-2, 2) # Atmosferik sarsıntı simülasyonu
        else:
            # Arama (Searching) modunda rakip gökyüzünde rastgele gezinsin
            self.mock_x += random.randint(-5, 5)
            self.mock_y += random.randint(-3, 3)

        # Kadraj sınırları koruması (Ekrandan tamamen çıkıp kaybolmasın)
        self.mock_x = max(50, min(590, self.mock_x))
        self.mock_y = max(50, min(430, self.mock_y))

        # Ekran merkezine olan uzaklık (Piksel Ofsetleri)
        offset_x = self.mock_x - self.cam_center_x
        offset_y = self.mock_y - self.cam_center_y
        
        detected = True
        return {
            "detected": detected,
            "offset_x": offset_x,
            "offset_y": offset_y,
            "area": 4500 # Sahte piksel alanı (Mesafe tahmini için)
        }

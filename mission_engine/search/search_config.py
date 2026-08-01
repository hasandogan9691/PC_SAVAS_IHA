from dataclasses import dataclass

@dataclass
class SearchConfig:
    altitude: float = 15.0    # Drone'un arama yaparken koruyacağı hedef uçuş irtifasını (metre cinsinden) Örneğin 2.5 değeri, drone'un yerden 2.5 metre yükseklikte uçarak tarama gerçekleştireceğini gösterir.
    speed: float = 5.0   #  Drone'un arama rotası üzerinde ilerlerken kullanacağı yatay uçuş hızını (metre/saniye cinsinden) belirtir. Örneğin 1.5 değeri, saniyede 1.5 metrelik bir hızla hareket edeceğini tanımlar.
    lawn_rows: int = 20    # Satır sayısı (Y eksenindeki şerit adımı)
    lawn_cols: int = 40    # Sütun sayısı (X eksenindeki geçiş sayısı)
    lawn_step: float = 30.0   # Adım aralığı (Ne çok dar ne çok kopuk, ideal şerit mesafesi)
    spiral_spacing: float = 0.5  #  Spiral arama deseninde (spiral), merkeze olan dönüşler arasındaki mesafe veya aralık katsayısını belirler.
    max_radius: float = 25.0     # Spiral veya dairesel arama desenlerinde drone'un merkezden dışarıya doğru açılacağı maksimum yarıçapı (metre cinsinden) ifade eder.
    square_size: float = 5.0     #  are arama deseninde (square), çizilecek karenin bir kenar uzunluğunu (metre cinsinden) tanımlar.

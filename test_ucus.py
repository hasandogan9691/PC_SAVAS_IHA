import asyncio
from mavsdk import System


async def run():
    # Dron nesnesini başlat
    drone = System()
    await drone.connect(system_address="udp://:14540")
    # [EK] PX4 simülasyonu, dışarıdan bağlanan Python (MAVSDK/MAVLink) scriptleri için varsayılan olarak UDP 14540 portunu dinler. QGroundControl ise 14550 portunu kullanır; bu sayede iki bağlantı çakışmaz.

    print("Drona bağlanmayı bekliyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("--- Drona başarılı bir şekilde bağlandı! ---")
            break

    print("GPS kilitlenmesi ve uçuş öncesi sağlık kontrolü bekleniyor...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("--- GPS kilitlendi, sistem uçuşa hazır! ---")
            break
    # [EK] Daha önce 'Preflight check FAILED' hatası almamıza sebep olan sağlık kontrolleri ve GPS kilitlenmesi burada kod tarafında otomatik olarak dinlenir. Sistem hazır olana kadar kod bir sonraki adıma geçmez.

    print("-- Motorlar çalıştırılıyor (Arm)...")
    await drone.action.arm()

    print("-- Otonom kalkış yapılıyor (Takeoff)...")
    await drone.action.takeoff()
    # [EK] Takeoff komutu, aracı varsayılan kalkış irtifasına (genellikle 2.5 metre) çıkarır ve sabit konumda tutar.

    print("Havada 25 saniye asılı bekleniyor (Hover)...")
    await asyncio.sleep(25)

    print("-- Otonom iniş yapılıyor (Land)...")
    await drone.action.land()


if __name__ == "__main__":
    # MAVSDK asenkron (asyncio) altyapısı ile çalışır
    asyncio.run(run())

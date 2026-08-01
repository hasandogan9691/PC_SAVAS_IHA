import asyncio
from mavsdk import System

async def run():
    drone = System()
    
    # PX4 simülasyonuna varsayılan porttan bağlanıyoruz
    await drone.connect(system_address="udp://:14540")

    print("[SİSTEM] Drone'a bağlanılıyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"[BAŞARILI] Drone keşfedildi!")
            break

    print("[SİSTEM] GPS kilidi bekleniyor...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("[BAŞARILI] GPS sinyali mükemmel!")
            break

    print("[GÖREV] Motorlar çalıştırılıyor (ARM)...")
    await drone.action.arm()

    print("[GÖREV] Havalanıyor (TAKEOFF)...")
    await drone.action.takeoff()

    # 10 saniye havada bekle
    await asyncio.sleep(10)

    print("[GÖREV] İniş yapılıyor (LAND)...")
    await drone.action.land()

if __name__ == "__main__":
    # Event loop'u başlatıyoruz
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

import time
import asyncio
from mavsdk import System
from mavsdk.offboard import VelocityNedYaw
from dataclasses import dataclass

from mission_engine.mission_state_machine import MissionStateMachine, MissionState
from mission_engine.mission_context import MissionContext
from mission_engine.search.search_planner import SearchPlanner
from mission_engine.search.search_config import SearchConfig
from mission_engine.target.target_manager import TargetManager
from mission_engine.target.target_events import TargetEvent
from mission_engine.target.target import TargetData
from mission_engine.navigation.navigation_planner import NavigationPlanner
from mission_engine.safety.safety_manager import SafetyManager


def on_failsafe_triggered(reason):
    print(f"\n[KARARGAH KONTROLÜ] Acil Durum Algılandı! Sebep: {reason}")


async def main():
    print("=" * 60)
    print(" AAFS - OTONOM GÖREV YÖNETİCİSİ BAŞLATILIYOR ")
    print("=" * 60)

    # MAVSDK Bağlantısı (Ruhun Bedene Entegrasyonu)
    drone = System()
    await drone.connect(system_address="udpin://127.0.0.1:14540")
    print("[SİSTEM] MAVSDK: Otopilota bağlantı bekleniyor...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("[SİSTEM] MAVSDK: Gerçek Drone'a Bağlanıldı!")
            break

    # 1. Altyapı ve Bağlam (Context) Kurulumu
    fsm = MissionStateMachine()
    ctx = MissionContext()

    # 2. Modüllerin Başlatılması
    search_planner = SearchPlanner(pattern="lawnmower", center_x=0.0, center_y=0.0, config=SearchConfig())
    target_manager = TargetManager(confidence_threshold=0.75, required_confirm_count=3, loss_timeout=1.0)
    nav_planner = NavigationPlanner(
        position_gain=0.8,
        max_horizontal_speed=5.0,     # 1.5 olan hızı arama hızıyla senkronize ettik
        max_vertical_speed=0.5,        # Drone'un 15 metreye biraz daha seri tırmanması için artırdık
        waypoint_tolerance=0.5,
        takeoff_altitude=15.0,        # <--- İrtifayı 2.5'ten 15.0'a çıkardık   
    )

    # Güvenlik Yöneticisini başlat (20Hz / 50ms arka plan denetimi)
    safety_manager = SafetyManager(callback_failsafe_trigger=on_failsafe_triggered, check_interval=0.05)
    safety_manager.start()

    # Simülasyon / Konum Değişkenleri
    current_x, current_y, current_z = 0.0, 0.0, 0.0
    active_waypoint = None
    dt = 0.2  # Döngü zaman aralığı (time.sleep ile uyumlu)
    previous_state = None  # Durum değişimlerini yakalamak için

    print("\n[SİSTEM] Ana Görev Döngüsü (Main Loop) Devreye Giriyor...\n")

    try:
        while fsm.current_state != MissionState.SHUTDOWN:

            # A. Güvenlik Denetimi Entegrasyonu
            if not safety_manager.is_safe():
                ctx.failsafe_active = True
                ctx.failsafe_reason = safety_manager.failsafe_reason

            # B. FSM Durum Güncellemesi
            fsm.update(ctx)

            # C. Navigasyon ve Görev Mantığı
            nav_command = None

            if fsm.current_state == MissionState.SEARCH:
                if active_waypoint is None and not search_planner.finished():
                    active_waypoint = search_planner.get_next_waypoint()

                nav_command = nav_planner.compute_command(
                    state=fsm.current_state,
                    current_x=current_x,
                    current_y=current_y,
                    current_z=current_z,
                    waypoint=active_waypoint
                )

                if nav_command.command_type == "WAYPOINT_REACHED":
                    print(f"[NAV] Waypoint'e ulaşıldı! Sonraki noktaya geçiliyor.")
                    search_planner.advance()
                    active_waypoint = search_planner.get_next_waypoint()
                elif nav_command.command_type == "SEARCH_COMPLETE":
                    print(f"[NAV] Arama rotası tamamlandı! RTL (Eve Dönüş) başlatılıyor.")
                    ctx.mission_done = True
                    fsm.current_state = MissionState.RTL  # FSM'i RTL'ye manuel geçiriyoruz
            elif fsm.current_state == MissionState.TRACK:
                dummy_detection = TargetData(track_id=101, confidence=0.88, x=0.2, y=-0.1, z=2.5)
                target_event = target_manager.update(dummy_detection)

                if target_event == TargetEvent.TARGET_CONFIRMED:
                    ctx.target_confirmed = True
                elif target_event == TargetEvent.TARGET_LOST:
                    ctx.target_lost_in_track = True

                nav_command = nav_planner.compute_command(state=fsm.current_state, current_z=current_z)

            else:
                nav_command = nav_planner.compute_command(
                    state=fsm.current_state,
                    current_z=current_z,
                    target_altitude=15.0       # <--- 2.5 yerine 15.0 yapıldı
                )

            # --- MAVSDK GERÇEK DRONE TETİKLEYİCİLERİ ---
            if fsm.current_state != previous_state:
                if fsm.current_state == MissionState.ARM:
                    print("Sistem sağlık kontrolleri ve GPS bekleniyor...")
                    async for health in drone.telemetry.health():
                        if health.is_global_position_ok and health.is_armable:
                            print("Drone kalkışa hazır!")
                            break
                    
                    await asyncio.sleep(2)
                    
                    try:
                        await drone.action.arm()
                        print("[BAŞARILI] Motorlar ateşlendi (ARM)!")
                    except Exception as e:
                        print(f"[DİKKAT] Otopilot ARM komutunu reddetti: {e}")
                        print("Sistemi toparlaması için 1-2 saniye bekleyip betiği tekrar çalıştırın.")
                        
                elif fsm.current_state == MissionState.TAKEOFF:
                    await drone.action.takeoff()
                elif fsm.current_state == MissionState.SEARCH:
                    await drone.offboard.set_velocity_ned(VelocityNedYaw(0.0, 0.0, 0.0, 0.0))
                    await drone.offboard.start()
                elif fsm.current_state == MissionState.RTL:
                    try: await drone.offboard.stop()
                    except: pass
                    await drone.action.return_to_launch()
                elif fsm.current_state == MissionState.LAND:
                    await drone.action.land()         
                
                previous_state = fsm.current_state

            if fsm.current_state == MissionState.SEARCH and nav_command:
                if hasattr(nav_command, 'vx') and hasattr(nav_command, 'vy'):
                    await drone.offboard.set_velocity_ned(VelocityNedYaw(nav_command.vx, nav_command.vy, 0.0, 0.0))
            # -------------------------------------------

            # D. Simülasyon Adımları ve Basit Fizik Entegrasyonu (Konum Güncelleme)
            if nav_command:
                # Hız vektörlerini konuma yansıt (Euler integrasyonu: pos += velocity * dt)
                current_x += getattr(nav_command, 'vx', 0.0) * dt
                current_y += getattr(nav_command, 'vy', 0.0) * dt

            if fsm.current_state == MissionState.INIT:
                ctx.sensor_ok = True
            elif fsm.current_state == MissionState.PRECHECK:
                safety_manager.update_status(gps_ok=True, imu_ok=True, baro_ok=True, camera_ok=True, offboard_ok=True)
            elif fsm.current_state == MissionState.ARM:
                ctx.is_armed = True
            elif fsm.current_state == MissionState.TAKEOFF:
                current_z += 0.2
                if current_z >= 15.0:             # <--- 2.5 yerine 15.0 metreye ulaşana kadar kalkış devam edecek
                    ctx.takeoff_completed = True
            elif fsm.current_state == MissionState.RTL:
                ctx.rtl_completed = True
            elif fsm.current_state == MissionState.LAND:
                current_z = max(0.0, current_z - 0.2)
                if current_z <= 0.05:
                    ctx.landing_completed = True

            # Döngü İçi Log Çıktısı (Konum bilgisiyle birlikte)
            wp_info = f"X:{current_x:.1f}, Y:{current_y:.1f}" if active_waypoint else "N/A"
            print(f"[DÖNGÜ] State: {fsm.current_state.name:<16} | Komut: {nav_command.command_type if nav_command else 'BEKLEME':<18} | Konum: ({wp_info}) | İrtifa: {current_z:.2f}m")

            await asyncio.sleep(dt)

    except KeyboardInterrupt:
        print("\n[UYARI] Kullanıcı tarafından manuel durdurma algılandı.")
    finally:
        safety_manager.stop()
        print("=" * 60)
        print(" GÖREV BAŞARIYLA SONLANDIRILDI VE GÜVENLE KAPATILDI ")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

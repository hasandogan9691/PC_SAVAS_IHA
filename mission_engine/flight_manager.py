import asyncio
from mavsdk import System
from mavsdk.action import ActionError
from mavsdk.telemetry import LandedState

class FlightManager:

    def __init__(self, ctx, system_address="udp://:14540"):
        # //[EK] Ortak hafızamızı (MissionContext) ve MAVSDK sistem nesnesini bağlıyoruz.
        self.ctx = ctx
        self.drone = System()
        self.system_address = system_address
        self.is_connected = False

    async def connect(self):
        """
        PX4 otopilotuna (SITL veya gerçek donanım) MAVSDK üzerinden bağlanır.
        """
        print(f"[FlightManager] Otopilota bağlanılıyor: {self.system_address} ...")
        await self.drone.connect(system_address=self.system_address)

        print("[FlightManager] Drone bağlantısı bekleniyor...")
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print("[FlightManager] Otopilot bağlantısı BAŞARILI!")
                self.is_connected = True
                self.ctx.health.px4_connected = True
                break

    async def telemetry_loop(self):
        """
        Arka planda sürekli çalışarak drone'dan gelen telemetri verilerini 
        bizim nested MissionContext yapımıza işler.
        """
        # Eşzamanlı (Concurrent) olarak farklı MAVSDK akışlarını dinliyoruz
        await asyncio.gather(
            self._watch_position(),
            self._watch_battery(),
            self._watch_health(),
            self._watch_flight_mode()
        )

    async def _watch_position(self):
        async for position in self.drone.telemetry.position():
            self.ctx.position.absolute_altitude = position.absolute_altitude_m
            self.ctx.position.relative_altitude = position.relative_altitude_m
            # İleride GPS koordinatları veya yerel konum dönüşümleri buraya eklenecek
            self.ctx.position.telemetry_timestamp = asyncio.get_event_loop().time()

    async def _watch_battery(self):
        async for battery in self.drone.telemetry.battery():
            self.ctx.battery.percentage = battery.remaining_percent * 100.0
            self.ctx.battery.voltage = battery.voltage_v
            self.ctx.battery.ok = self.ctx.battery.percentage > 15.0

    async def _watch_health(self):
        async for health in self.drone.telemetry.health():
            self.ctx.health.gps_ok = health.is_gps_ok
            self.ctx.health.imu_ok = health.is_accelerometer_ok and health.is_gyroscope_ok
            self.ctx.health.sensor_ok = health.is_armable

    async def _watch_flight_mode(self):
        async for flight_mode in self.drone.telemetry.flight_mode():
            # MAVSDK modlarını kendi FlightMode enum yapımıza eşliyoruz
            self.ctx.flight.mode = str(flight_mode)

    async def arm_and_takeoff(self, target_altitude=2.5):
        """
        Drone'u arm eder ve belirlenen irtifaya otomatik kalkış yapar.
        """
        print("[FlightManager] Arm (Motorlar çalıştırılıyor) komutu gönderiliyor...")
        try:
            await self.drone.action.arm()
            self.ctx.flight.armed = True
        except ActionError as e:
            print(f"[FlightManager] Arm hatası: {e}")
            return

        print(f"[FlightManager] Kalkış başlatılıyor. Hedef İrtifa: {target_altitude}m")
        try:
            await self.drone.action.takeoff()
            self.ctx.flight.takeoff_completed = True
        except ActionError as e:
            print(f"[FlightManager] Kalkış hatası: {e}")

    async def apply_velocity_command(self, vx, vy, vz):
        """
        MissionCoordinator'dan gelen hız vektörlerini (NED koordinat sistemi) 
        Offboard modu aracılığıyla MAVSDK'ye iletir.
        """
        try:
            # MAVSDK Offboard hız komutu (North, East, Down - m/s cinsinden)
            from mavsdk.offboard import OffboardError, VelocityNedYaw
            
            # Hız komutunu gönderirken yönü (yaw) mevcut koruyoruz
            await self.drone.offboard.set_velocity_ned(
                VelocityNedYaw(vx, vy, vz, 0.0)
            )
        except Exception as e:
            # Offboard modu aktif değilse veya henüz başlatılmadıysa burası yakalanır
            pass

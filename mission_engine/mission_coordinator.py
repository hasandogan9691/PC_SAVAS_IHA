import time
import math

from mission_engine.mission_context import MissionContext

from mission_engine.mission_state_machine import (
    MissionStateMachine,
    MissionState
)

from mission_engine.search.search_planner import SearchPlanner
from mission_engine.search.search_config import SearchConfig

from mission_engine.target.target_manager import TargetManager

from mission_engine.navigation.navigation_planner import NavigationPlanner

from mission_engine.safety.safety_manager import SafetyManager


class MissionCoordinator:

    def __init__(self):

        print("=" * 70)
        print("AAFS Mission Coordinator")
        print("=" * 70)

        ####################################################
        # Shared Context
        ####################################################
        # //[EK] Sistemdeki tüm modüllerin okuyup yazacağı ortak veri havuzu (Single Source of Truth) başlatılıyor.

        self.ctx = MissionContext()

        ####################################################
        # Mission State Machine
        ####################################################
        # //[EK] İnsansız hava aracının o anki görev durumunu (State) yönetecek ana karar mekanizması.

        self.fsm = MissionStateMachine()

        ####################################################
        # Search Planner
        ####################################################
        # //[EK] Arama rotasını (Lawnmower vb.) ve waypointleri üretecek olan planlayıcı.

        self.search_planner = SearchPlanner(

            pattern="lawnmower",

            center_x=0.0,

            center_y=0.0,

            config=SearchConfig()

        )

        ####################################################
        # Target Manager
        ####################################################
        # //[EK] Kameradan gelen ham tespitleri doğrulayacak ve takip (Track) kararı verecek olan yönetici.

        self.target_manager = TargetManager(

            confidence_threshold=0.75,

            required_confirm_count=3,

            loss_timeout=1.0

        )

        ####################################################
        # Navigation Planner
        ####################################################
        # //[EK] Hedef waypoint'e gitmek için gerekli X, Y, Z hız vektörlerini hesaplayan katman.

        self.navigation = NavigationPlanner(

            position_gain=0.8,

            max_horizontal_speed=1.5,

            max_vertical_speed=0.5,

            waypoint_tolerance=0.5,

            takeoff_altitude=2.5

        )

        ####################################################
        # Safety Manager
        ####################################################
        # //[EK] Sensörleri ve telemetriyi sürekli denetleyip gerektiğinde sistemi Failsafe'e alan güvenlik çemberi.

        self.safety = SafetyManager(

            callback_failsafe_trigger=self.on_failsafe_triggered,

            check_interval=0.05

        )

        ####################################################
        # Runtime
        ####################################################
        # //[EK] Döngü kontrol bayrağı ve çalışma frekansını (loop_rate) belirleyen değişkenler.

        self.is_running = False

        self.loop_rate = 0.1

        print("[Coordinator] Hazır.")


    ####################################################
    # FAILSAFE CALLBACK
    ####################################################
    # //[EK] Güvenlik modülü (SafetyManager) bir tehlike algıladığında durumu yeni nested Context'e yazar.

    def on_failsafe_triggered(self, reason):

        self.ctx.failsafe.active = True

        self.ctx.failsafe.reason = reason

        self.ctx.failsafe.timestamp = time.time()

        print()

        print("========== FAILSAFE ==========")

        print(reason)

        print("==============================")


    ####################################################
    # START
    ####################################################
    # //[EK] Sistemi ayağa kaldıran, güvenlik thread'ini başlatan ve görev zamanlayıcısını sıfırlayan ana tetikleyici.

    def start(self):

        if self.is_running:
            return

        print()

        print("[Coordinator] Başlatılıyor...")

        self.is_running = True

        self.safety.start()

        ####################################################
        # Mission
        ####################################################
        # //[EK] Görev başlangıç zamanını kaydediyoruz ki timer (kronometre) düzgün çalışabilsin.

        self.ctx.mission.mission_started = True

        self.ctx.mission.mission_completed = False

        self.ctx.mission.mission_start_timestamp = time.time()

        ####################################################
        # Home Position
        ####################################################

        self.ctx.home.x = 0.0
        self.ctx.home.y = 0.0
        self.ctx.home.z = 0.0

        print("[Coordinator] Başlatıldı.")


    ####################################################
    # STOP
    ####################################################
    # //[EK] Sistemi, güvenlik thread'ini ve görev döngüsünü güvenli bir şekilde kapatan fonksiyon.

    def stop(self):

        if not self.is_running:
            return

        self.is_running = False

        self.safety.stop()

        self.ctx.mission.mission_completed = True

        print()

        print("[Coordinator] Durduruldu.")


    ####################################################
    # HOME DISTANCE
    ####################################################
    # //[EK] 3B (Euclidean) mesafe ölçümü. İleride RTL (Eve Dönüş) durumunda İHA'nın dönüş hızını hesaplamak için kullanılır.

    def distance_to_home(self):

        dx = self.ctx.position.x - self.ctx.home.x

        dy = self.ctx.position.y - self.ctx.home.y

        dz = self.ctx.position.z - self.ctx.home.z

        return math.sqrt(

            dx * dx +

            dy * dy +

            dz * dz

        )


    ####################################################
    # UPDATE METHODS (FAZ 2)
    ####################################################

    def update_health(self):

        # //[EK] Sensör ve sistem sağlık durumlarını günceller. Şimdilik SITL simülasyonu için her şeyi sağlıklı (True) kabul ediyoruz.

        self.ctx.health.sensor_ok = True
        self.ctx.health.gps_ok = True
        self.ctx.health.imu_ok = True
        self.ctx.health.baro_ok = True
        self.ctx.health.camera_ok = True
        self.ctx.health.vision_ok = True
        self.ctx.health.telemetry_ok = True
        self.ctx.health.px4_connected = True
        self.ctx.health.offboard_ok = True

        self.ctx.battery.percentage = 100.0
        self.ctx.battery.voltage = 16.8
        self.ctx.battery.current = 1.5
        self.ctx.battery.ok = True


    def update_telemetry(self, dt):

        # //[EK] İHA'nın anlık konumunu ve hızını günceller. Şimdilik hız üzerinden basit bir fizik simülasyonu (Euler integrasyonu) yapıyoruz.

        self.ctx.position.telemetry_timestamp = time.time()

        self.ctx.position.x += self.ctx.position.vx * dt
        self.ctx.position.y += self.ctx.position.vy * dt
        self.ctx.position.z += self.ctx.position.vz * dt

        # //[EK] PX4 standartlarında Z ekseni aşağı doğru negatiftir. Göreceli irtifayı pozitif tutuyoruz.

        self.ctx.position.relative_altitude = abs(self.ctx.position.z)


    def update_mission_timer(self):

        # //[EK] Görev başladıysa geçen süreyi (kronometre) günceller.

        if self.ctx.mission.mission_started and not self.ctx.mission.mission_completed:
            self.ctx.mission.mission_elapsed_time = time.time() - self.ctx.mission.mission_start_timestamp


    def print_status(self):

        # //[EK] Terminal üzerinde sistemin anlık durumunu gösteren log çıktısı.

        state_name = self.fsm.current_state.name if hasattr(self.fsm, 'current_state') else "UNKNOWN"

        mode_name = self.ctx.flight.mode.name if hasattr(self.ctx.flight.mode, 'name') else str(self.ctx.flight.mode)

        px = self.ctx.position.x
        py = self.ctx.position.y
        alt = self.ctx.position.relative_altitude

        bat = self.ctx.battery.percentage
        timer = self.ctx.mission.mission_elapsed_time

        print(f"[STATUS] State: {state_name:<15} | Mode: {mode_name:<8} | Pos: (X:{px:.1f}, Y:{py:.1f}, Alt:{alt:.1f}m) | Bat: %{bat:.0f} | Time: {timer:.1f}s")


    ####################################################
    # PROCESS SEARCH (FAZ 3)
    ####################################################

    def process_search(self):

        # //[EK] Eğer sıradaki waypoint'e henüz ulaşmadıysak ve arama görevimiz bitmediyse yeni bir nokta talep ediyoruz.
        if not self.ctx.waypoint.reached and not self.ctx.search.completed:

            if self.ctx.waypoint.x is None:
                wp = self.search_planner.get_next_waypoint()
                if wp:
                    self.ctx.waypoint.x = wp.x
                    self.ctx.waypoint.y = wp.y

        # //[EK] Hedefe doğru süzülmek için navigasyon komutunu üretiyoruz. Tüm verileri yeni alt modellerden okuyoruz.
        nav_command = self.navigation.compute_command(
            state=self.fsm.current_state,
            current_x=self.ctx.position.x,
            current_y=self.ctx.position.y,
            current_z=self.ctx.position.z,
            waypoint_x=self.ctx.waypoint.x,
            waypoint_y=self.ctx.waypoint.y
        )

        # //[EK] Eğer hedefe ulaşıldıysa veya tüm arama bittiyse, bayrakları (flag) ortak hafızada güncelliyoruz.
        if nav_command.command_type == "WAYPOINT_REACHED":

            self.ctx.waypoint.reached = True
            self.search_planner.advance()

            wp = self.search_planner.get_next_waypoint()
            if wp:
                self.ctx.waypoint.x = wp.x
                self.ctx.waypoint.y = wp.y
                self.ctx.waypoint.reached = False

        elif nav_command.command_type == "SEARCH_COMPLETE":

            self.ctx.search.completed = True

        return nav_command


    ####################################################
    # PROCESS TRACK (FAZ 4)
    ####################################################

    def process_track(self):

        # //[EK] İleride kamera veya VisionTracker modülümüzden gelecek olan gerçek hedef verilerini temsil eden geçici (mock) veri yapısı.
        from mission_engine.target.target import TargetData
        dummy_detection = TargetData(
            track_id=1, 
            confidence=0.88, 
            x=self.ctx.position.x + 1.0, 
            y=self.ctx.position.y
        )

        # //[EK] Hedefi teyit etmesi için TargetManager'ın şefkatli kollarına bırakıyoruz.
        target_event = self.target_manager.update(dummy_detection)

        if target_event.name == "TARGET_CONFIRMED":
            self.ctx.target.confirmed = True
        elif target_event.name == "TARGET_LOST":
            self.ctx.target.lost = True

        # //[EK] Takip esnasında İHA'yı hedefin üzerine yönlendirecek hız vektörlerini hesaplıyoruz.
        nav_command = self.navigation.compute_command(
            state=self.fsm.current_state,
            current_z=self.ctx.position.z
        )

        return nav_command
    ####################################################
    # EXECUTE & STATUS (FAZ 5)
    ####################################################

    def execute_command(self, nav_command):

        # //[EK] Planlayıcılardan (Search, Track, RTL vb.) gelen soyut hız komutlarını, İHA'nın anlık hız vektörlerine çevirir.
        # İleride burası MAVSDK'nin "await drone.offboard.set_velocity_ned()" fonksiyonuna bağlanacak.

        if nav_command:
            self.ctx.position.vx = getattr(nav_command, 'vx', 0.0)
            self.ctx.position.vy = getattr(nav_command, 'vy', 0.0)
            self.ctx.position.vz = getattr(nav_command, 'vz', 0.0)
        else:
            self.ctx.position.vx = 0.0
            self.ctx.position.vy = 0.0
            self.ctx.position.vz = 0.0


    def update_flight_status(self):

        # //[EK] İHA'nın irtifasına ve FSM'nin o anki durumuna bakarak uçuş bayraklarını (takeoff_completed, landing_completed) günceller.

        current_state = getattr(self.fsm, 'current_state', None)

        if current_state == MissionState.ARM:
            self.ctx.flight.armed = True

        elif current_state == MissionState.TAKEOFF:
            # Kalkış irtifamızı 2.5 metre belirlemiştik, 2.4'e ulaştığında tamamlandı sayıyoruz.
            if self.ctx.position.relative_altitude >= 2.4:
                self.ctx.flight.takeoff_completed = True

        elif current_state == MissionState.LAND:
            # Yere 10 cm yaklaştığında inişi tamamlanmış kabul ediyoruz.
            if self.ctx.position.relative_altitude <= 0.1:
                self.ctx.flight.landing_completed = True

        elif current_state == MissionState.RTL:
            # Home pozisyonuna yatayda 1 metreden yakın ve yerde isek RTL bitmiştir.
            if self.distance_to_home() < 1.0 and self.ctx.position.relative_altitude <= 0.1:
                self.ctx.flight.rtl_completed = True


    ####################################################
    # MAIN LOOP / NABIZ (FAZ 6)
    ####################################################

    def run_step(self, dt=0.1):

        # //[EK] Sistemin saniyede 10 veya 20 kez çalışan ana nabzı. 
        # Oku -> Karar Ver -> Planla -> İcra Et sıralaması katı bir havacılık kuralıdır.

        if not self.is_running:
            return None

        # ---------------------------------------------------------
        # 1. READ (Veri ve Sensör Okuma)
        # ---------------------------------------------------------
        self.update_health()
        self.update_telemetry(dt)
        self.update_mission_timer()

        # (SafetyManager kendi bağımsız thread'inde çalıştığı için burada durumu kontrol etmemiz gerekmiyor, 
        # o zaten tehlike anında 'on_failsafe_triggered' üzerinden Context'i güncelliyor.)

        # ---------------------------------------------------------
        # 2. KARAR (FSM Güncellemesi)
        # ---------------------------------------------------------
        self.fsm.update(self.ctx)
        current_state = self.fsm.current_state

        nav_command = None

        # ---------------------------------------------------------
        # 3. PLANLAMA (Görev ve Rota Belirleme)
        # ---------------------------------------------------------
        if current_state == MissionState.SEARCH:
            nav_command = self.process_search()

        elif current_state == MissionState.TRACK:
            nav_command = self.process_track()

        else:
            # TAKEOFF, LAND, RTL veya HOLD durumlarında temel navigasyon matematiği devreye girer
            nav_command = self.navigation.compute_command(
                state=current_state,
                current_x=self.ctx.position.x,
                current_y=self.ctx.position.y,
                current_z=self.ctx.position.z,
                target_altitude=2.5 # Varsayılan kalkış hedef irtifası
            )

        # ---------------------------------------------------------
        # 4. İCRA (Kaslara Emir Verme)
        # ---------------------------------------------------------
        self.execute_command(nav_command)
        self.update_flight_status()

        # ---------------------------------------------------------
        # 5. EKRANA ÇIKTI VE GÜVENLİ KAPANIŞ
        # ---------------------------------------------------------
        self.print_status()

        if current_state == MissionState.SHUTDOWN:
            self.stop()

        return nav_command

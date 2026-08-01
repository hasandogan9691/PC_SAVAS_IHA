import time
from enum import Enum, auto

class MissionState(Enum):
    INIT = auto()
    PRECHECK = auto()
    READY = auto()
    ARM = auto()
    TAKEOFF = auto()
    HOVER = auto()
    SEARCH = auto()
    TARGET_CANDIDATE = auto()
    TARGET_CONFIRM = auto()
    TRACK = auto()
    MISSION_COMPLETE = auto()
    RTL = auto()
    LAND = auto()
    SHUTDOWN = auto()
    FAILSAFE = auto()

class MissionStateMachine:
    def __init__(self):
        self.current_state = MissionState.INIT
        self.state_start_time = time.time()
        print(f"[FSM] Başlatıldı -> {self.current_state.name}")

    def change_state(self, new_state):
        if new_state != self.current_state:
            print(f"[FSM GEÇİŞİ] {self.current_state.name} ---> {new_state.name}")
            self.current_state = new_state
            self.state_start_time = time.time()

    def elapsed(self):
        return time.time() - self.state_start_time

    def update(self, ctx):
        """
        MissionContext (ctx) nesnesini alarak saf mantık kurallarına göre durum değiştirir.
        Zaman aşımı ve fiziksel eylemler FSM içinde geciktirilmez; yalnızca koşullar sorgulanır.
        """

        # KURAL 1: FAILSAFE HER ZAMAN EN YÜKSEK ÖNCELİKTEDİR
        # Failsafe doğrudan LAND yapmaz; FAILSAFE state'inde kalır, karar Koordinatör/Sistemündedir.
        if getattr(ctx, 'failsafe_active', False):
            if self.current_state != MissionState.FAILSAFE:
                reason = getattr(ctx, 'failsafe_reason', 'Bilinmeyen Hata')
                print(f"[FAILSAFE] Kritik hata tetiklendi! Neden: {reason}")
                self.change_state(MissionState.FAILSAFE)
            return

        # NORMAL STATE MACHINE AKIŞI
        if self.current_state == MissionState.INIT:
            if getattr(ctx, 'sensor_ok', False):
                self.change_state(MissionState.PRECHECK)

        elif self.current_state == MissionState.PRECHECK:
            # KURAL 3: Gerçekçi ve kapsamlı bileşen kontrolleri
            all_systems_healthy = (
                getattr(ctx, 'gps_ok', True) and getattr(ctx, 'imu_ok', True) and getattr(ctx, 'baro_ok', True) and
                getattr(ctx, 'battery_ok', True) and getattr(ctx, 'camera_ok', True) and getattr(ctx, 'vision_ok', True)
            )
            if all_systems_healthy:
                self.change_state(MissionState.READY)
            else:
                ctx.failsafe_active = True
                ctx.failsafe_reason = "PRECHECK_FAILED"

        elif self.current_state == MissionState.READY:
            # KURAL 2: Doğrudan kalkış yok, hazır olunca ARM aşamasına geçilir
            self.change_state(MissionState.ARM)

        elif self.current_state == MissionState.ARM:
            # Motorlar kurulduysa kalkışa geç
            if getattr(ctx, 'is_armed', False):
                self.change_state(MissionState.TAKEOFF)

        elif self.current_state == MissionState.TAKEOFF:
            if getattr(ctx, 'takeoff_completed', False):
                self.change_state(MissionState.HOVER)

        elif self.current_state == MissionState.HOVER:
            if self.elapsed() >= 5.0:
                self.change_state(MissionState.SEARCH)

        elif self.current_state == MissionState.SEARCH:
            if getattr(ctx, 'target_found', False):
                self.change_state(MissionState.TARGET_CANDIDATE)
            elif getattr(ctx, 'mission_done', False):
                self.change_state(MissionState.MISSION_COMPLETE)

        elif self.current_state == MissionState.TARGET_CANDIDATE:
            if getattr(ctx, 'target_confirmed', False):
                self.change_state(MissionState.TARGET_CONFIRM)
            elif not getattr(ctx, 'target_found', False):
                self.change_state(MissionState.SEARCH)

        elif self.current_state == MissionState.TARGET_CONFIRM:
            # KURAL 4: Güçlü doğrulama (süre ve süreklilik kontrolü dışarıdan context ile beslenir)
            if getattr(ctx, 'target_visible_duration', 0) >= 3.0 and not getattr(ctx, 'target_lost_in_track', False):
                self.change_state(MissionState.TRACK)
            elif getattr(ctx, 'target_lost_in_track', False):
                self.change_state(MissionState.SEARCH)

        elif self.current_state == MissionState.TRACK:
            # KURAL 5: Takip sırasında hedef kaybolursa SEARCH'e dön
            if getattr(ctx, 'target_lost_in_track', False):
                print("[TRACK] Hedef kaybedildi! Arama (SEARCH) moduna dönülüyor.")
                # Durumu sıfırla ki tekrar arayabilelim
                ctx.target_lost_in_track = False
                ctx.target_confirmed = False
                ctx.target_found = False
                self.change_state(MissionState.SEARCH)
            elif getattr(ctx, 'mission_done', False):
                self.change_state(MissionState.MISSION_COMPLETE)

        elif self.current_state == MissionState.MISSION_COMPLETE:
            # KURAL 8: FSM içinde zaman gecikmesi (sleep vb.) yok, koşul sağlandığı an RTL istenir.
            # 2 saniye bekleme/loglama işi Coordinator/Logger tarafında yürütülür.
            self.change_state(MissionState.RTL)

        elif self.current_state == MissionState.RTL:
            if getattr(ctx, 'rtl_completed', False):
                self.change_state(MissionState.LAND)

        elif self.current_state == MissionState.LAND:
            if getattr(ctx, 'landing_completed', False):
                # KURAL 6: İniş bittikten sonra doğrudan kapanmak yerine SHUTDOWN state'ine geçilir.
                self.change_state(MissionState.SHUTDOWN)

        elif self.current_state == MissionState.SHUTDOWN:
            # Logger, Telemetri ve Video kaydedicilerin güvenle kapanması için son durak
            pass

        elif self.current_state == MissionState.FAILSAFE:
            # KURAL 1: Failsafe durumunda Koordinatör kararıyla güvenli inişe (LAND) yönlendirilebilir
            # veya otopilot RTL/Land tetikleyebilir.
            # Şimdilik otomatik LAND'a alalım.
            self.change_state(MissionState.LAND)

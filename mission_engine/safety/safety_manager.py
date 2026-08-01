import time
import threading
from dataclasses import dataclass


# ==========================================================
# SAFETY STATUS
# ==========================================================

@dataclass
class SafetyStatus:
    px4_connected: bool = True
    telemetry_active: bool = True
    battery_voltage_ok: bool = True
    sensors_healthy: bool = True
    vision_node_active: bool = True

    gps_ok: bool = True
    imu_ok: bool = True
    baro_ok: bool = True
    camera_ok: bool = True
    offboard_ok: bool = True


# ==========================================================
# SAFETY MANAGER
# ==========================================================

class SafetyManager:

    def __init__(
        self,
        callback_failsafe_trigger=None,
        check_interval=0.05,
    ):
        """
        callback_failsafe_trigger:
            Failsafe oluştuğunda çağrılacak callback.

        check_interval:
            Güvenlik kontrol periyodu.
            0.05 = 50 ms = 20 Hz
        """

        self.check_interval = check_interval

        self.callback_failsafe_trigger = (
            callback_failsafe_trigger
        )

        self.is_running = False

        self.failsafe_active = False

        self.failsafe_reason = None

        self.status = SafetyStatus()

        self.monitor_thread = None

        print(
            "[SAFETY MANAGER] "
            "Güvenlik yöneticisi hazır."
        )

    # ======================================================
    # START
    # ======================================================

    def start(self):

        if self.is_running:
            return

        self.is_running = True

        self.monitor_thread = threading.Thread(
            target=self._safety_loop,
            daemon=True,
            name="SafetyManager"
        )

        self.monitor_thread.start()

        print(
            "[SAFETY MANAGER] "
            "Bağımsız güvenlik denetçisi aktif. "
            "(50 ms / 20 Hz)"
        )

    # ======================================================
    # SAFETY LOOP
    # ======================================================

    def _safety_loop(self):

        while self.is_running:

            try:

                healthy, reason = (
                    self._check_all_systems()
                )

                if not healthy:

                    self._trigger_failsafe(
                        reason
                    )

                    # Failsafe bir kez tetiklendikten
                    # sonra loop çalışmaya devam edebilir.
                    #
                    # Burada thread'i öldürmüyoruz.
                    # Coordinator/FSM durumuna karar verir.

                time.sleep(
                    self.check_interval
                )

            except Exception as exc:

                self._trigger_failsafe(
                    f"SAFETY_MANAGER_EXCEPTION: {exc}"
                )

                time.sleep(
                    self.check_interval
                )

    # ======================================================
    # SYSTEM CHECK
    # ======================================================

    def _check_all_systems(self):

        if not self.status.px4_connected:
            return False, "PX4_CONNECTION_LOST"

        if not self.status.telemetry_active:
            return False, "TELEMETRY_LOST"

        if not self.status.battery_voltage_ok:
            return False, "BATTERY_LOW"

        if not self.status.sensors_healthy:
            return False, "SENSOR_FAILURE"

        if not self.status.gps_ok:
            return False, "GPS_FAILURE"

        if not self.status.imu_ok:
            return False, "IMU_FAILURE"

        if not self.status.baro_ok:
            return False, "BAROMETER_FAILURE"

        if not self.status.camera_ok:
            return False, "CAMERA_FAILURE"

        if not self.status.offboard_ok:
            return False, "OFFBOARD_LOST"

        return True, None

    # ======================================================
    # FAILSAFE
    # ======================================================

    def _trigger_failsafe(self, reason):

        # Aynı failsafe'i tekrar tekrar göndermeyi önle
        if self.failsafe_active:
            return

        self.failsafe_active = True

        self.failsafe_reason = reason

        print(
            "[SAFETY] FAILSAFE TETİKLENDİ!"
        )

        print(
            f"[SAFETY] Neden: {reason}"
        )

        if self.callback_failsafe_trigger:

            try:

                self.callback_failsafe_trigger(
                    reason
                )

            except Exception as exc:

                print(
                    "[SAFETY] "
                    f"Callback hatası: {exc}"
                )

    # ======================================================
    # STATUS UPDATE
    # ======================================================

    def update_sensor_status(
        self,
        key,
        status_bool,
    ):

        if not hasattr(
            self.status,
            key
        ):

            print(
                "[SAFETY] "
                f"Bilinmeyen status anahtarı: {key}"
            )

            return False

        setattr(
            self.status,
            key,
            bool(status_bool)
        )

        return True

    # ======================================================
    # BULK STATUS UPDATE
    # ======================================================

    def update_status(
        self,
        **kwargs
    ):

        for key, value in kwargs.items():

            self.update_sensor_status(
                key,
                value
            )

    # ======================================================
    # FAILSAFE RESET
    # ======================================================

    def clear_failsafe(self):

        healthy, reason = (
            self._check_all_systems()
        )

        if not healthy:

            print(
                "[SAFETY] "
                "Failsafe temizlenemedi."
            )

            print(
                f"[SAFETY] "
                f"Devam eden hata: {reason}"
            )

            return False

        self.failsafe_active = False

        self.failsafe_reason = None

        print(
            "[SAFETY] "
            "Failsafe durumu temizlendi."
        )

        return True

    # ======================================================
    # STATUS
    # ======================================================

    def is_safe(self):

        healthy, _ = (
            self._check_all_systems()
        )

        return (
            healthy
            and not self.failsafe_active
        )

    # ======================================================
    # STOP
    # ======================================================

    def stop(self):

        self.is_running = False

        if self.monitor_thread:

            self.monitor_thread.join(
                timeout=1.0
            )

        print(
            "[SAFETY MANAGER] "
            "Güvenlik denetçisi durduruldu."
        )


# ==========================================================
# SIMULATION TEST
# ==========================================================

if __name__ == "__main__":

    def failsafe_callback(reason):

        print(
            "[TEST] "
            f"Coordinator'a FAILSAFE bildirildi: "
            f"{reason}"
        )

    safety = SafetyManager(
        callback_failsafe_trigger=failsafe_callback,
        check_interval=0.05,
    )

    safety.start()

    print(
        "\n[TEST] Sistem güvenli:",
        safety.is_safe()
    )

    time.sleep(1)

    print(
        "\n[TEST] GPS arızası simüle ediliyor..."
    )

    safety.update_sensor_status(
        "gps_ok",
        False
    )

    time.sleep(0.2)

    print(
        "\n[TEST] Failsafe:",
        safety.failsafe_active
    )

    print(
        "[TEST] Sebep:",
        safety.failsafe_reason
    )

    safety.stop()

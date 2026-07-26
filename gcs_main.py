import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFont
from gui.udp_listener import UDPTelemetryListener
from gui.cmd_sender import GCSCommandSender

class GCSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        with open("config_gcs.json", "r") as f: 
            self.config = json.load(f)
            
        net = self.config["network_settings"]
        self.commander = GCSCommandSender(net["uav_ip"], net["command_port"])
        
        self.setWindowTitle(self.config["gui_settings"]["window_title"])
        self.resize(700, 450)
        self.setStyleSheet("QMainWindow { background-color: #1e1e24; }")

        cw = QWidget()
        self.setCentralWidget(cw)
        layout = QVBoxLayout(cw)

        # Başlık
        self.lbl_title = QLabel("TEKNOFEST Savaşan İHA - Canlı İzleme")
        self.lbl_title.setFont(QFont("Arial", 14, QFont.Bold))
        self.lbl_title.setStyleSheet("color: #ffffff; padding: 5px;")
        layout.addWidget(self.lbl_title)

        # Uçuş Modu ve Durum alanı
        self.lbl_mode = QLabel("MOD: BAĞLANTI BEKLENİYOR")
        self.lbl_mode.setFont(QFont("Arial", 14, QFont.Bold))
        self.lbl_mode.setStyleSheet("color: #ffcc00; background-color: #2a2a35; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.lbl_mode)

        # --- YENİ EKLENEN CANLI UÇUŞ VERİLERİ (İRTİFA VE GPS) ---
        self.lbl_flight_data = QLabel("İrtifa (Yükseklik): 0.0 metre\nEnlem: 0.000000\nBoylam: 0.000000")
        self.lbl_flight_data.setFont(QFont("Courier New", 13, QFont.Bold))
        self.lbl_flight_data.setStyleSheet("color: #00ffcc; background-color: #121214; padding: 15px; border-radius: 5px; line-height: 20px;")
        layout.addWidget(self.lbl_flight_data)

        # Pil Barı
        self.pbar = QProgressBar()
        self.pbar.setStyleSheet("QProgressBar { border: 1px solid grey; border-radius: 5px; text-align: center; color: white; }"
                                "QProgressBar::chunk { background-color: #05b04c; }")
        layout.addWidget(self.pbar)

        # Butonlar
        btn_layout = QHBoxLayout()
        self.btn_rtl = QPushButton("ACİL EVE DÖNDÜR (RTL)")
        self.btn_rtl.setStyleSheet("background-color: #d9534f; color: white; font-weight: bold; padding: 10px;")
        self.btn_rtl.clicked.connect(self.commander.send_force_rtl)
        btn_layout.addWidget(self.btn_rtl)
        layout.addLayout(btn_layout)

        # Dinleyiciyi Başlat
        self.listener = UDPTelemetryListener(net["listen_ip"], net["telemetry_port"])
        self.listener.telemetry_received.connect(self.handle_telem)
        self.listener.connection_lost.connect(self.handle_loss)
        self.listener.start()

    @pyqtSlot(dict)
    def handle_telem(self, data):
        # Durum ve Mod Güncelleme
        self.lbl_mode.setText(f"DURUM: AKTİF | MOD: {data['mode']}")
        self.lbl_mode.setStyleSheet("color: #00ff00; background-color: #2a2a35; padding: 10px; border-radius: 5px;")
        self.pbar.setValue(data["battery_percent"])
        
        # --- CANLI OLARAK İRTİFA, ENLEM VE BOYLANIN EKRANA YAZILMASI ---
        altitude = data.get("relative_alt", 0.0)
        lat = data.get("lat", 0.0)
        lon = data.get("lon", 0.0)
        
        self.lbl_flight_data.setText(
            f"🚀 İrtifa (Yükseklik): {altitude:.2f} metre\n"
            f"📍 Enlem (Latitude):   {lat:.6f}\n"
            f"📍 Boylam (Longitude): {lon:.6f}"
        )

    @pyqtSlot()
    def handle_loss(self): 
        self.lbl_mode.setText("BAĞLANTI KOPUK!")
        self.lbl_mode.setStyleSheet("color: white; background-color: #d9534f; padding: 10px; border-radius: 5px;")
        self.lbl_flight_data.setText("İrtifa (Yükseklik): ---\nEnlem: ---\nBoylam: ---")
        self.pbar.setValue(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = GCSWindow()
    w.show()
    sys.exit(app.exec_())


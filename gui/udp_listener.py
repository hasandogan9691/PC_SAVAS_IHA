import socket, json
from PyQt5.QtCore import QThread, pyqtSignal
class UDPTelemetryListener(QThread):
 telemetry_received = pyqtSignal(dict)
 connection_lost = pyqtSignal()
 def __init__(self, ip, port): super().__init__(); self.ip, self.port, self.running = ip, port, False
 def run(self):
  self.running = True; self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); self.sock.bind((self.ip, self.port)); self.sock.settimeout(2.0)
  while self.running:
   try: data, _ = self.sock.recvfrom(4096); self.telemetry_received.emit(json.loads(data.decode("utf-8")))
   except socket.timeout: self.connection_lost.emit()
   except Exception: pass
 def stop(self): self.running = False; self.sock.close(); self.wait()
import socket
class GCSCommandSender:
 def __init__(self, uav_ip, command_port): self.uav_ip, self.command_port = uav_ip, command_port; self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
 def send_force_rtl(self): self.sock.sendto(b"FORCE_RTL", (self.uav_ip, self.command_port))
 def send_force_land(self): self.sock.sendto(b"FORCE_LAND", (self.uav_ip, self.command_port))
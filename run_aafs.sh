#!/bin/bash

# ==============================================================================
# AAFS v2 - Otonom Uçuş Kontrol Merkezi Başlatıcı
# ==============================================================================
SESSION="AAFS_MISSION"

# Eski oturum varsa tamamen kapat
tmux kill-session -t $SESSION 2>/dev/null

killall -9 px4 python3 gz 2>/dev/null
sudo fuser -k 5600/udp 2>/dev/null
sleep 2

echo "[SİSTEM] AAFS Görev Kontrol Merkezi Başlatılıyor..."

# 1. Yeni tmux oturumunu sol panelde (Mission Runner) başlat
# 1. Yeni tmux oturumunu sol panelde (Mission Runner) başlat
tmux new-session -d -s $SESSION -n "AAFS_CONTROL"
tmux send-keys -t $SESSION:0.0 "source uav_env/bin/activate && echo '[SİSTEM] Otopilot bekleniyor (15sn)...' && sleep 15 && python3 mission_runner.py" C-m

# 2. Sağ tarafta simülasyon için yatay bölme oluştur (Sağ Üst Panel)
tmux split-window -h -t $SESSION:0.0
tmux send-keys -t $SESSION:0.1 "echo -e '\e[1;33m[OTOPİLOT EKRANI (Gazebo / SITL)]\e[0m'" C-m
tmux send-keys -t $SESSION:0.1 "cd ~/PX4-Autopilot 2>/dev/null || echo 'PX4 dizini bulunamadı'" C-m
tmux send-keys -t $SESSION:0.1 "make px4_sitl gz_x500_mono_cam" C-m


# 3. Sağ üst paneli dikey olarak böl (Sağ Alt Panel - Yer İstasyonu / Görüntü İşleme)
tmux split-window -v -t $SESSION:0.1
tmux send-keys -t $SESSION:0.2 "echo -e '\e[1;36m[GÖRÜNTÜ İŞLEME / YER İSTASYONU]\e[0m'" C-m
tmux send-keys -t $SESSION:0.2 "echo 'QGroundControl / Kamera akışı bekleniyor...'" C-m
tmux send-keys -t $SESSION:0.2 "cd ~ && ./QGroundControl.AppImage" C-m

# Panelleri eşit şekilde düzenle ve sol panele odaklan
tmux select-layout -t $SESSION:0 tiled
tmux select-pane -t $SESSION:0.0

# Oturuma bağlan
tmux attach-session -t $SESSION


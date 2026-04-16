#!/bin/bash
# DarkLead — install cockpit + evebox
set -e

echo "[1/3] Installing Cockpit..."
apt-get install -y cockpit
systemctl enable --now cockpit.socket
echo "Cockpit running on :9090"

echo "[2/3] Installing EveBox..."
EVEBOX_DEB="/tmp/evebox.deb"
if [[ ! -f "$EVEBOX_DEB" ]]; then
    curl -sL "https://evebox.org/files/release/latest/evebox-0.24.0-amd64.deb" -o "$EVEBOX_DEB"
fi
dpkg -i "$EVEBOX_DEB" || apt-get install -f -y
echo "EveBox installed at $(which evebox)"

echo "[3/3] Setting up EveBox systemd service..."
cat > /etc/systemd/system/evebox.service << 'EOF'
[Unit]
Description=EveBox Suricata Event Viewer
After=network.target

[Service]
Type=simple
User=w01f
ExecStart=/usr/bin/evebox server \
    --host 127.0.0.1 \
    --port 5636 \
    --sqlite \
    --no-auth \
    --data-directory /home/w01f/.local/share/evebox \
    /var/log/suricata/eve.json \
    /home/w01f/.local/share/suricata/eve.json
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now evebox
echo "EveBox service enabled"
echo ""
echo "Done! Services:"
echo "  Cockpit:  http://localhost:9090"
echo "  EveBox:   http://localhost:5636"
echo "  DarkLead: http://localhost:7860"

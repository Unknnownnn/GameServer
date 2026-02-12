#!/bin/bash
# GameServer DigitalOcean Droplet Setup Script
# Run this script on your fresh Ubuntu 22.04 droplet after first SSH login
# Usage: curl -sSL https://raw.githubusercontent.com/your-repo/main/setup-droplet.sh | bash

set -e  # Exit on error

echo "========================================"
echo "   GameServer Droplet Setup Script"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}[1/7] Updating system packages...${NC}"
apt update && apt upgrade -y

echo -e "${GREEN}[2/7] Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
    echo -e "${GREEN}✓ Docker installed successfully${NC}"
else
    echo -e "${YELLOW}✓ Docker already installed${NC}"
fi

echo -e "${GREEN}[3/7] Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    apt install -y docker-compose
    echo -e "${GREEN}✓ Docker Compose installed successfully${NC}"
else
    echo -e "${YELLOW}✓ Docker Compose already installed${NC}"
fi

echo -e "${GREEN}[4/7] Installing additional tools...${NC}"
apt install -y git curl wget nano htop net-tools

echo -e "${GREEN}[5/7] Configuring firewall (UFW)...${NC}"
if ! command -v ufw &> /dev/null; then
    apt install -y ufw
fi

# Configure UFW rules
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH access'
ufw allow 3306/tcp comment 'MySQL GameServer CTF'
ufw allow 5001/tcp comment 'GameServer Reset API'
ufw --force enable

echo -e "${GREEN}✓ Firewall configured${NC}"
ufw status verbose

echo -e "${GREEN}[6/7] Creating project directory...${NC}"
mkdir -p /opt/gameserver
cd /opt/gameserver

echo -e "${GREEN}[7/7] Setting up Docker log rotation...${NC}"
cat > /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Setup Complete! ✓${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Upload your GameServer files to /opt/gameserver/GameServer"
echo "   From your local machine run:"
echo "   ${GREEN}scp -r ./GameServer root@$(curl -s ifconfig.me):/opt/gameserver/${NC}"
echo ""
echo "2. Start GameServer:"
echo "   ${GREEN}cd /opt/gameserver/GameServer && docker-compose up -d${NC}"
echo ""
echo "3. Test the deployment:"
echo "   ${GREEN}curl http://$(curl -s ifconfig.me):5001/health${NC}"
echo ""
echo -e "${YELLOW}Your droplet's public IP: ${GREEN}$(curl -s ifconfig.me)${NC}"
echo ""
echo -e "${YELLOW}Installed versions:${NC}"
docker --version
docker-compose --version
echo ""
echo -e "${YELLOW}Firewall status:${NC}"
ufw status
echo ""
echo -e "${GREEN}All done! 🎉${NC}"

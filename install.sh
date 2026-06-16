#!/bin/bash
# ══════════════════════════════════════════════════
#  FBTools — Installer
#  Works on: Kali Linux | Termux | Ubuntu | Debian
# ══════════════════════════════════════════════════

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
BOLD='\033[1m'
RESET='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════╗"
echo "║       FBTools — Installing...            ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${RESET}"

# Detect environment
if [ -d "/data/data/com.termux" ]; then
    ENV="termux"
    echo -e "${YELLOW}[*] Detected: Termux${RESET}"
else
    ENV="linux"
    echo -e "${YELLOW}[*] Detected: Linux${RESET}"
fi

# Install Python dependencies
echo -e "${CYAN}[*] Installing Python packages...${RESET}"

if [ "$ENV" = "termux" ]; then
    pkg update -y && pkg install -y python python-pip
    pip install requests
else
    pip3 install requests --break-system-packages 2>/dev/null || pip3 install requests
fi

# Create directories
mkdir -p config logs
echo -e "${GREEN}[✔] Directories created.${RESET}"

# Make main script executable
chmod +x fbtools.py
echo -e "${GREEN}[✔] fbtools.py is executable.${RESET}"

# Create symlink (Linux only)
if [ "$ENV" = "linux" ]; then
    if [ -w "/usr/local/bin" ]; then
        ln -sf "$(pwd)/fbtools.py" /usr/local/bin/fbtools
        echo -e "${GREEN}[✔] Symlink created: fbtools command available globally.${RESET}"
    fi
fi

echo -e "${GREEN}${BOLD}"
echo "══════════════════════════════════════════"
echo "  Installation complete!"
echo ""
echo "  Run: python3 fbtools.py"
echo "   Or: python3 fbtools.py --login"
echo "   Or: python3 fbtools.py --status"
echo "══════════════════════════════════════════"
echo -e "${RESET}"

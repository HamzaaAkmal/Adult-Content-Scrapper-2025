#!/bin/bash

# NSFW Audio Scraper - VPS Setup Script
# Run this on your Ubuntu/Debian VPS to automatically set up everything

set -e  # Exit on any error

echo "======================================================================"
echo "NSFW Audio Scraper - Automated VPS Setup"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_info "Running as root"
else
   print_info "Running as non-root user (will use sudo)"
fi

# Step 1: Update system
print_info "Step 1/10: Updating system packages..."
sudo apt update -qq
sudo apt upgrade -y -qq
print_success "System updated"

# Step 2: Install Python 3.10+
print_info "Step 2/10: Installing Python..."
sudo apt install python3 python3-venv python3-pip -y -qq
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION installed"

# Step 3: Install FFmpeg
print_info "Step 3/10: Installing FFmpeg..."
sudo apt install ffmpeg -y -qq
FFMPEG_VERSION=$(ffmpeg -version | head -n 1 | cut -d' ' -f3)
print_success "FFmpeg $FFMPEG_VERSION installed"

# Step 4: Install Git
print_info "Step 4/10: Installing Git..."
sudo apt install git -y -qq
GIT_VERSION=$(git --version | cut -d' ' -f3)
print_success "Git $GIT_VERSION installed"

# Step 5: Install additional tools
print_info "Step 5/10: Installing additional tools (screen, curl)..."
sudo apt install screen curl -y -qq
print_success "Additional tools installed"

# Step 6: Clone repository (if not already cloned)
print_info "Step 6/10: Setting up repository..."
if [ -d "Adult-Content-Scrapper-2025" ]; then
    print_info "Repository already exists, pulling latest changes..."
    cd Adult-Content-Scrapper-2025
    git pull origin main
else
    print_info "Cloning repository..."
    git clone https://github.com/HamzaaAkmal/Adult-Content-Scrapper-2025.git
    cd Adult-Content-Scrapper-2025
fi
print_success "Repository ready"

# Step 7: Create virtual environment
print_info "Step 7/10: Creating Python virtual environment..."
if [ -d "venv" ]; then
    print_info "Virtual environment already exists"
else
    python3 -m venv venv
fi
print_success "Virtual environment ready"

# Step 8: Install Python dependencies
print_info "Step 8/10: Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
print_success "Python packages installed"

# Step 9: Set up environment file
print_info "Step 9/10: Configuring environment variables..."
if [ -f ".env" ]; then
    print_info ".env file already exists"
else
    cp .env.example .env
    print_info "Created .env file from template"
    echo ""
    echo "======================================================================"
    echo "IMPORTANT: You need to add your Groq API key!"
    echo "======================================================================"
    echo "1. Get your API key from: https://console.groq.com/keys"
    echo "2. Edit the .env file: nano .env"
    echo "3. Replace 'your_groq_api_key_here' with your actual key"
    echo ""
    read -p "Press Enter to open the .env file in nano editor..."
    nano .env
fi
print_success "Environment configured"

# Step 10: Create required directories
print_info "Step 10/10: Creating output directories..."
mkdir -p temp downloads clips metadata
print_success "Directories created"

# Configure firewall
print_info "Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 8501/tcp -qq 2>/dev/null || true
    print_success "Firewall configured (port 8501 opened)"
else
    print_info "UFW not installed, skipping firewall configuration"
fi

# Final summary
echo ""
echo "======================================================================"
echo "Setup Complete! 🎉"
echo "======================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Verify your Groq API key is set in .env:"
echo "   cat .env"
echo ""
echo "2. Test the scraper:"
echo "   source venv/bin/activate"
echo "   python test_immediate.py"
echo ""
echo "3. Run Streamlit app:"
echo "   streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
echo ""
echo "4. Access the app at:"
echo "   http://$(curl -s ifconfig.me):8501"
echo ""
echo "5. Or run in background with screen:"
echo "   screen -S scraper"
echo "   streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
echo "   # Press Ctrl+A then D to detach"
echo ""
echo "======================================================================"
echo "Documentation:"
echo "  - Full guide: cat VPS_DEPLOYMENT.md"
echo "  - Security fix: cat SECURITY_FIX.md"
echo "  - Main README: cat README.md"
echo "======================================================================"

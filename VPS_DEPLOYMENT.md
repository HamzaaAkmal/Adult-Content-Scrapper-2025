# VPS Deployment Guide - NSFW Audio Scraper

Complete step-by-step guide to deploy and run the scraper on a VPS (Ubuntu/Debian).

## Prerequisites

- VPS with Ubuntu 20.04+ or Debian 11+
- SSH access to your VPS
- Minimum 2GB RAM, 2 CPU cores
- 20GB+ storage (for video downloads and clips)

## Step 1: Connect to Your VPS

```bash
# From your local machine
ssh root@your-vps-ip-address
# Or with username
ssh username@your-vps-ip-address
```

## Step 2: System Updates

```bash
# Update package lists
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y
```

## Step 3: Install Python 3.10+

```bash
# Check Python version
python3 --version

# If Python < 3.10, install Python 3.10
sudo apt install python3.10 python3.10-venv python3-pip -y

# Set Python 3.10 as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
```

## Step 4: Install FFmpeg

```bash
# Install FFmpeg and FFprobe
sudo apt install ffmpeg -y

# Verify installation
ffmpeg -version
ffprobe -version
```

## Step 5: Install Git

```bash
# Install Git
sudo apt install git -y

# Verify installation
git --version
```

## Step 6: Clone the Repository

```bash
# Navigate to home directory
cd ~

# Clone your repository
git clone https://github.com/HamzaaAkmal/Adult-Content-Scrapper-2025.git

# Navigate to project directory
cd Adult-Content-Scrapper-2025
```

## Step 7: Set Up Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

## Step 8: Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

## Step 9: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your API key
nano .env
```

In the nano editor:
1. Replace `your_groq_api_key_here` with your actual Groq API key
2. Press `Ctrl + X`, then `Y`, then `Enter` to save

Your `.env` should look like:
```
GROQ_API_KEY=gsk_your_actual_api_key_here
```

## Step 10: Create Required Directories

```bash
# Create output directories
mkdir -p temp downloads clips metadata
```

## Step 11: Test the Setup

```bash
# Test with immediate download script
python test_immediate.py
```

If successful, you should see a video download!

## Step 12: Run Streamlit App

### Option A: Run in Foreground (for testing)

```bash
# Run Streamlit (will occupy the terminal)
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Access at: `http://your-vps-ip:8501`

### Option B: Run in Background (recommended)

```bash
# Install screen or tmux for background processes
sudo apt install screen -y

# Create a screen session
screen -S scraper

# Run Streamlit
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Detach from screen: Press Ctrl+A, then D

# To reattach later:
screen -r scraper
```

### Option C: Run as a Service (production)

Create a systemd service:

```bash
# Create service file
sudo nano /etc/systemd/system/nsfw-scraper.service
```

Add this content:
```ini
[Unit]
Description=NSFW Audio Scraper
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/Adult-Content-Scrapper-2025
Environment="PATH=/root/Adult-Content-Scrapper-2025/venv/bin"
ExecStart=/root/Adult-Content-Scrapper-2025/venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

Save and enable:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable nsfw-scraper

# Start the service
sudo systemctl start nsfw-scraper

# Check status
sudo systemctl status nsfw-scraper

# View logs
sudo journalctl -u nsfw-scraper -f
```

## Step 13: Configure Firewall

```bash
# Allow SSH (if not already allowed)
sudo ufw allow 22/tcp

# Allow Streamlit port
sudo ufw allow 8501/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Step 14: Access the Application

Open your browser and go to:
```
http://your-vps-ip-address:8501
```

## Step 15: Run Scraping Jobs

### Method 1: Via Streamlit UI

1. Navigate to `http://your-vps-ip:8501`
2. Upload a CSV file with URLs
3. Click "Start Scraping"
4. Download the ZIP file when complete

### Method 2: Via Command Line

```bash
# Activate virtual environment
source venv/bin/activate

# Run end-to-end test
python test_e2e.py

# Or test immediate download
python test_immediate.py
```

### Method 3: Create a Scraping Script

```bash
# Create a scraping script
nano run_scrape.py
```

Add this content:
```python
import asyncio
from scraper_pipeline import NSFWScraper

async def main():
    scraper = NSFWScraper()
    urls = ["https://hamsterix.today"]
    results = await scraper.scrape_from_urls(urls)
    print(f"Extracted {results['clips_extracted']} clips")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:
```bash
python run_scrape.py
```

## Optional: Set Up Nginx Reverse Proxy

For production, use Nginx to proxy Streamlit:

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx config
sudo nano /etc/nginx/sites-available/scraper
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Or your VPS IP

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and start:
```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/scraper /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

Now access at: `http://your-vps-ip` (port 80)

## Monitoring and Maintenance

### Check Application Logs
```bash
# If running as service
sudo journalctl -u nsfw-scraper -f

# If running in screen
screen -r scraper
```

### Check Disk Space
```bash
df -h
```

### Clean Up Old Files
```bash
# Remove old videos
rm -rf temp/*.mp4

# Remove old downloads
rm -rf downloads/*
```

### Update the Application
```bash
cd ~/Adult-Content-Scrapper-2025

# Pull latest changes
git pull origin main

# Restart service
sudo systemctl restart nsfw-scraper
```

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8501
sudo lsof -i :8501

# Kill the process
sudo kill -9 <PID>
```

### Can't Access from Browser
```bash
# Check if Streamlit is running
ps aux | grep streamlit

# Check firewall
sudo ufw status

# Check if port is listening
sudo netstat -tlnp | grep 8501
```

### FFmpeg Not Found
```bash
# Reinstall FFmpeg
sudo apt install --reinstall ffmpeg -y

# Verify installation
which ffmpeg
```

### Python Package Issues
```bash
# Activate venv
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Out of Disk Space
```bash
# Check space
df -h

# Clean up
rm -rf temp/* downloads/* clips/*

# Or increase VPS storage
```

## Security Best Practices

1. **Change Default SSH Port**
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Change Port 22 to something else
   sudo systemctl restart sshd
   ```

2. **Use SSH Keys Instead of Passwords**
   ```bash
   # On your local machine
   ssh-keygen -t rsa -b 4096
   ssh-copy-id user@vps-ip
   ```

3. **Keep API Keys Secure**
   - Never commit `.env` to git
   - Set proper file permissions: `chmod 600 .env`

4. **Regular Updates**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Performance Tips

1. **Increase Concurrent Scrapes** (if VPS has good resources):
   Edit `config.py`:
   ```python
   MAX_CONCURRENT_SCRAPES = 20  # Default is 10
   ```

2. **Use SSD Storage** for better I/O performance

3. **Monitor Resource Usage**:
   ```bash
   # Install htop
   sudo apt install htop -y
   htop
   ```

4. **Set Up Swap** (if low on RAM):
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

## Quick Reference Commands

```bash
# Start scraper
sudo systemctl start nsfw-scraper

# Stop scraper
sudo systemctl stop nsfw-scraper

# Restart scraper
sudo systemctl restart nsfw-scraper

# View logs
sudo journalctl -u nsfw-scraper -f

# Check status
sudo systemctl status nsfw-scraper

# Activate Python environment
source venv/bin/activate

# Update code
git pull origin main && sudo systemctl restart nsfw-scraper
```

## Support

If you encounter issues:
1. Check logs: `sudo journalctl -u nsfw-scraper -f`
2. Verify all dependencies are installed
3. Ensure `.env` file has valid API key
4. Check firewall settings
5. Verify FFmpeg is installed: `ffmpeg -version`

---

**Your NSFW Audio Scraper is now running on a VPS! 🚀**

Access it at: `http://your-vps-ip:8501`

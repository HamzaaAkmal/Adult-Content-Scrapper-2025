# Quick Start - VPS Deployment (5 Minutes)

## 🚀 Fastest Way to Deploy

### 1. Connect to Your VPS
```bash
ssh root@your-vps-ip
```

### 2. Run the Automated Setup Script
```bash
# Download and run the setup script
curl -sSL https://raw.githubusercontent.com/HamzaaAkmal/Adult-Content-Scrapper-2025/main/setup_vps.sh | bash
```

**OR** if you prefer manual control:

```bash
# Clone the repository
git clone https://github.com/HamzaaAkmal/Adult-Content-Scrapper-2025.git
cd Adult-Content-Scrapper-2025

# Run setup script
chmod +x setup_vps.sh
./setup_vps.sh
```

### 3. Add Your Groq API Key
The script will automatically open the `.env` file. Just:
- Replace `your_groq_api_key_here` with your actual key
- Save with `Ctrl+X`, `Y`, `Enter`

### 4. Start the Scraper
```bash
# Activate Python environment
source venv/bin/activate

# Run Streamlit in background
screen -S scraper
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Detach with Ctrl+A, then D
```

### 5. Access the App
Open your browser:
```
http://YOUR_VPS_IP:8501
```

## ✅ That's It!

You're ready to:
1. Upload a CSV with URLs
2. Start scraping
3. Download your NSFW audio clips

---

## Alternative: Run as System Service

If you want the scraper to start automatically on boot:

```bash
cd ~/Adult-Content-Scrapper-2025

# Copy service file
sudo cp nsfw-scraper.service /etc/systemd/system/

# If not using root user, edit the service file:
# sudo nano /etc/systemd/system/nsfw-scraper.service
# Change User=root and WorkingDirectory paths

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable nsfw-scraper
sudo systemctl start nsfw-scraper

# Check status
sudo systemctl status nsfw-scraper
```

---

## Troubleshooting

### Can't access the app?
```bash
# Check if it's running
ps aux | grep streamlit

# Check firewall
sudo ufw allow 8501/tcp
sudo ufw status

# Check logs
sudo journalctl -u nsfw-scraper -f
```

### Port already in use?
```bash
# Find and kill the process
sudo lsof -i :8501
sudo kill -9 <PID>
```

### Need to update?
```bash
cd ~/Adult-Content-Scrapper-2025
git pull origin main
sudo systemctl restart nsfw-scraper  # If using service
```

---

## Full Documentation

For detailed setup, security, and configuration:
- **Complete Guide**: `VPS_DEPLOYMENT.md`
- **Security Info**: `SECURITY_FIX.md`
- **Main README**: `README.md`

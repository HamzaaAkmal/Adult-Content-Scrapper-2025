# Automated FFmpeg Installer (No Admin Required)
# Run this script to install FFmpeg to your user directory

Write-Host "=" * 80
Write-Host "FFmpeg Installer for NSFW Audio Scraper"
Write-Host "=" * 80
Write-Host ""

# Configuration
$ffmpegDir = "C:\Users\Hamza\ffmpeg"
$downloadUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$zipFile = "$env:TEMP\ffmpeg.zip"

try {
    # Step 1: Create directory
    Write-Host "[1/5] Creating installation directory..."
    New-Item -ItemType Directory -Force -Path $ffmpegDir | Out-Null
    Write-Host "      ✅ Created: $ffmpegDir"
    
    # Step 2: Download
    Write-Host ""
    Write-Host "[2/5] Downloading FFmpeg (~70 MB)..."
    Write-Host "      This may take 1-2 minutes depending on your connection..."
    
    # Use .NET WebClient for progress
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $zipFile)
    
    Write-Host "      ✅ Downloaded to: $zipFile"
    
    # Step 3: Extract
    Write-Host ""
    Write-Host "[3/5] Extracting files..."
    Expand-Archive -Path $zipFile -DestinationPath $env:TEMP -Force
    
    # Find the extracted folder
    $extractedFolder = Get-ChildItem -Path $env:TEMP -Filter "ffmpeg-*-essentials_build" -Directory | 
                       Sort-Object LastWriteTime -Descending | 
                       Select-Object -First 1
    
    if (-not $extractedFolder) {
        throw "Could not find extracted FFmpeg folder"
    }
    
    $binPath = Join-Path $extractedFolder.FullName "bin"
    Write-Host "      ✅ Extracted files"
    
    # Step 4: Copy to permanent location
    Write-Host ""
    Write-Host "[4/5] Installing FFmpeg..."
    Copy-Item -Path "$binPath\*" -Destination $ffmpegDir -Force
    Write-Host "      ✅ Installed to: $ffmpegDir"
    
    # Step 5: Add to PATH
    Write-Host ""
    Write-Host "[5/5] Adding to system PATH..."
    
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    
    if ($userPath -notlike "*$ffmpegDir*") {
        $newPath = $userPath.TrimEnd(';') + ";$ffmpegDir"
        [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
        $env:Path = "$env:Path;$ffmpegDir"  # Update current session
        Write-Host "      ✅ Added to PATH"
    } else {
        Write-Host "      ✅ Already in PATH"
    }
    
    # Cleanup
    Write-Host ""
    Write-Host "Cleaning up temporary files..."
    Remove-Item $zipFile -Force -ErrorAction SilentlyContinue
    
    # Test installation
    Write-Host ""
    Write-Host "=" * 80
    Write-Host "Installation Complete!"
    Write-Host "=" * 80
    Write-Host ""
    
    # Test if ffmpeg works
    $ffmpegPath = Join-Path $ffmpegDir "ffmpeg.exe"
    if (Test-Path $ffmpegPath) {
        Write-Host "✅ FFmpeg installed successfully!"
        Write-Host ""
        Write-Host "Testing FFmpeg..."
        & $ffmpegPath -version | Select-Object -First 1
        Write-Host ""
        Write-Host "=" * 80
        Write-Host "Next Steps:"
        Write-Host "=" * 80
        Write-Host "1. Close this PowerShell window"
        Write-Host "2. Open a NEW PowerShell window (important for PATH to update)"
        Write-Host "3. Verify installation:"
        Write-Host "   ffmpeg -version"
        Write-Host ""
        Write-Host "4. Run the scraper test:"
        Write-Host "   cd 'C:\Users\Hamza\Desktop\NSFW Data Set\streamlit_scraper'"
        Write-Host "   python test_e2e.py"
        Write-Host ""
        Write-Host "5. Or launch the Streamlit app:"
        Write-Host "   streamlit run app.py"
        Write-Host "=" * 80
    } else {
        throw "Installation verification failed"
    }
    
} catch {
    Write-Host ""
    Write-Host "=" * 80
    Write-Host "❌ Installation Failed"
    Write-Host "=" * 80
    Write-Host "Error: $_"
    Write-Host ""
    Write-Host "Please try manual installation:"
    Write-Host "1. Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    Write-Host "2. Extract to: C:\Users\Hamza\ffmpeg"
    Write-Host "3. Add to PATH manually (see INSTALL_FFMPEG_NO_ADMIN.md)"
    Write-Host "=" * 80
    exit 1
}

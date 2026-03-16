# Simple FFmpeg Installation Script
Write-Host "Installing FFmpeg..." -ForegroundColor Green

# Download URL
$downloadUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$zipPath = "$env:USERPROFILE\Downloads\ffmpeg.zip"
$extractPath = "C:\ffmpeg"

Write-Host "Downloading FFmpeg to $zipPath..."
Write-Host "This may take a few minutes..."

try {
    # Download
    Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "Download complete!" -ForegroundColor Green

    # Create directory
    New-Item -ItemType Directory -Force -Path $extractPath | Out-Null

    # Extract
    Write-Host "Extracting to $extractPath..."
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

    Write-Host "Extraction complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "FFmpeg files are in: $extractPath" -ForegroundColor Cyan
    Write-Host "Look for a folder like 'ffmpeg-8.0.1-essentials_build'" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Manual steps needed:" -ForegroundColor Yellow
    Write-Host "1. Open: $extractPath" -ForegroundColor White
    Write-Host "2. Copy everything from the 'ffmpeg-x.x.x-essentials_build' folder" -ForegroundColor White
    Write-Host "3. Paste directly into C:\ffmpeg (merge folders)" -ForegroundColor White
    Write-Host "4. Add C:\ffmpeg\bin to your PATH environment variable" -ForegroundColor White
    Write-Host ""
    Write-Host "Or I can try to fix this automatically..." -ForegroundColor Cyan

} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

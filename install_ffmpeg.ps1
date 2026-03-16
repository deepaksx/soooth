# FFmpeg Installation Script for Windows
Write-Host "Installing FFmpeg..." -ForegroundColor Green

# Create directory for FFmpeg
$ffmpegDir = "C:\ffmpeg"
$ffmpegBinDir = "$ffmpegDir\bin"

if (Test-Path $ffmpegBinDir) {
    Write-Host "FFmpeg already installed at $ffmpegDir" -ForegroundColor Yellow
} else {
    Write-Host "Downloading FFmpeg..."

    # Download FFmpeg
    $downloadUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    $zipPath = "$env:TEMP\ffmpeg.zip"

    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing
        Write-Host "Download complete!" -ForegroundColor Green

        # Extract FFmpeg
        Write-Host "Extracting FFmpeg..."
        Expand-Archive -Path $zipPath -DestinationPath $env:TEMP -Force

        # Find the extracted folder (it has version number in name)
        $extractedFolder = Get-ChildItem "$env:TEMP\ffmpeg-*" | Select-Object -First 1

        # Move to C:\ffmpeg
        if ($extractedFolder) {
            New-Item -ItemType Directory -Force -Path $ffmpegDir | Out-Null
            Move-Item -Path "$($extractedFolder.FullName)\*" -Destination $ffmpegDir -Force
            Write-Host "FFmpeg installed to $ffmpegDir" -ForegroundColor Green
        }

        # Cleanup
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        Remove-Item $extractedFolder.FullName -Recurse -Force -ErrorAction SilentlyContinue

    } catch {
        Write-Host "Error downloading FFmpeg: $_" -ForegroundColor Red
        Write-Host "Please download manually from: https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Yellow
        exit 1
    }
}

# Add to PATH
Write-Host "Adding FFmpeg to system PATH..."
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$ffmpegBinDir*") {
    $newPath = "$currentPath;$ffmpegBinDir"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "FFmpeg added to PATH!" -ForegroundColor Green
    Write-Host ""
    Write-Host "IMPORTANT: Close and reopen your terminal for PATH changes to take effect" -ForegroundColor Yellow
} else {
    Write-Host "FFmpeg already in PATH" -ForegroundColor Green
}

# Test FFmpeg
Write-Host ""
Write-Host "Testing FFmpeg installation..."
try {
    $ffmpegExe = "$ffmpegBinDir\ffmpeg.exe"
    if (Test-Path $ffmpegExe) {
        & $ffmpegExe -version | Select-Object -First 1
        Write-Host ""
        Write-Host "SUCCESS! FFmpeg is installed and working!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Close this terminal window" -ForegroundColor White
        Write-Host "2. Close the backend server window" -ForegroundColor White
        Write-Host "3. Run start.bat again from D:\Dev\Soooth\soooth\" -ForegroundColor White
        Write-Host "4. Refresh your browser and try generating a video" -ForegroundColor White
    }
} catch {
    Write-Host "FFmpeg installed but not yet available in PATH" -ForegroundColor Yellow
    Write-Host "Please restart your terminal" -ForegroundColor Yellow
}

# Fix FFmpeg Installation
Write-Host "Fixing FFmpeg installation..." -ForegroundColor Green

$tempExtract = "$env:TEMP\ffmpeg_extract"
$downloadUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$zipPath = "$env:TEMP\ffmpeg-download.zip"
$finalDir = "C:\ffmpeg"

# Clean up old attempts
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Downloading FFmpeg (this may take 1-2 minutes)..."
Invoke-WebRequest -Uri $downloadUrl -OutFile $zipPath -UseBasicParsing

Write-Host "Extracting..."
Expand-Archive -Path $zipPath -DestinationPath $tempExtract -Force

# Find the extracted folder
$extractedFolder = Get-ChildItem "$tempExtract\ffmpeg-*" -Directory | Select-Object -First 1

if ($extractedFolder) {
    Write-Host "Moving files to $finalDir..."

    # Copy bin folder
    if (Test-Path "$($extractedFolder.FullName)\bin") {
        Copy-Item "$($extractedFolder.FullName)\bin" -Destination "$finalDir\bin" -Recurse -Force
        Write-Host "Copied bin folder" -ForegroundColor Green
    }

    # Copy other files if not already there
    if (!(Test-Path "$finalDir\LICENSE")) {
        Copy-Item "$($extractedFolder.FullName)\*" -Destination $finalDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    Write-Host ""
    Write-Host "SUCCESS! FFmpeg installed to $finalDir" -ForegroundColor Green

    # Test
    if (Test-Path "$finalDir\bin\ffmpeg.exe") {
        Write-Host ""
        & "$finalDir\bin\ffmpeg.exe" -version | Select-Object -First 1
        Write-Host ""
        Write-Host "FFmpeg is ready to use!" -ForegroundColor Green
    }
} else {
    Write-Host "Error: Could not find extracted folder" -ForegroundColor Red
}

# Cleanup
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $zipPath -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Close this terminal" -ForegroundColor White
Write-Host "2. Close all backend server windows" -ForegroundColor White
Write-Host "3. Open a NEW terminal" -ForegroundColor White
Write-Host "4. Run: cd D:\Dev\Soooth\soooth && start.bat" -ForegroundColor White
Write-Host "5. Try generating a video again" -ForegroundColor White

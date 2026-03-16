$pids = @(5512, 19712, 14876)
foreach ($procId in $pids) {
    try {
        Stop-Process -Id $procId -Force -ErrorAction Stop
        Write-Host "Killed process $procId"
    } catch {
        Write-Host "Process $procId not found or already stopped"
    }
}
Start-Sleep -Seconds 2
Write-Host "All backend processes stopped"

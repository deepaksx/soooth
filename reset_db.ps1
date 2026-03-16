# Stop all backend processes
Get-Process python,uvicorn -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*Soooth*backend*' } | Stop-Process -Force
Start-Sleep -Seconds 3

# Delete old database
Remove-Item D:\Dev\Soooth\soooth\backend\soooth.db -Force -ErrorAction SilentlyContinue
Write-Host "Database deleted. SQLAlchemy will create a fresh one with the new schema."

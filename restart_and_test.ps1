# PowerShell script to restart server and test
Write-Host "Stopping existing server processes..."
Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -like "*uvicorn*app.main*"} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

Write-Host "Starting server..."
cd C:\Users\sarve\OneDrive\Desktop\Web-Projects\aigis\server
Start-Process python -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000" -WindowStyle Hidden

Write-Host "Waiting for server to start..."
Start-Sleep -Seconds 5

Write-Host "Testing server..."
cd C:\Users\sarve\OneDrive\Desktop\Web-Projects\aigis
python test_endpoints.py

Write-Host "`nCreating test jobs..."
$clipBody = @{url="https://www.youtube.com/watch?v=jNQXAC9IVRw"} | ConvertTo-Json
$clipResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/jobs" -Method POST -Body $clipBody -ContentType "application/json" -UseBasicParsing
$clipJob = ($clipResponse.Content | ConvertFrom-Json).job_id
Write-Host "Clipping job created: $clipJob"

$genBody = @{topic="Amazing facts about the universe"} | ConvertTo-Json
$genResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/generate" -Method POST -Body $genBody -ContentType "application/json" -UseBasicParsing
$genJob = ($genResponse.Content | ConvertFrom-Json).job_id
Write-Host "Generation job created: $genJob"

Write-Host "`nWaiting 60 seconds for processing..."
Start-Sleep -Seconds 60

Write-Host "`nChecking job statuses..."
$clipStatus = (Invoke-WebRequest -Uri "http://localhost:8000/api/jobs/$clipJob" -UseBasicParsing).Content | ConvertFrom-Json
Write-Host "Clipping: Status=$($clipStatus.status), Progress=$($clipStatus.progress)%, Output=$($clipStatus.output_url)"

$genStatus = (Invoke-WebRequest -Uri "http://localhost:8000/api/generate/$genJob" -UseBasicParsing).Content | ConvertFrom-Json
Write-Host "Generation: Status=$($genStatus.status), Progress=$($genStatus.progress)%, Output=$($genStatus.output_url)"

Write-Host "`nChecking for output files..."
$outputs = Get-ChildItem "C:\Users\sarve\OneDrive\Desktop\Web-Projects\aigis\server\data\outputs\*.mp4" -ErrorAction SilentlyContinue
if ($outputs) {
    Write-Host "Found $($outputs.Count) video file(s):"
    $outputs | ForEach-Object { Write-Host "  $($_.Name) - $([math]::Round($_.Length/1MB,2)) MB" }
} else {
    Write-Host "No video files found yet"
}


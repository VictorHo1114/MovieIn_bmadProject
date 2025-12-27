# 壓力測試一鍵啟動腳本
Write-Host "`n MovieIn 壓力測試啟動器`n" -ForegroundColor Cyan

# 檢查後端
$backend = Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
if (-not $backend) {
    Write-Host " 後端未運行！請先啟動：" -ForegroundColor Red
    Write-Host "   uvicorn app.main:app --reload`n" -ForegroundColor Gray
    exit 1
}

Write-Host " 後端運行中" -ForegroundColor Green
Write-Host "`n選擇測試模式："
Write-Host "  [1] 快速測試 (~1分鐘)"
Write-Host "  [2] 完整測試 (~5分鐘)`n"

$choice = Read-Host "選項 (1/2)"

if ($choice -eq "1") {
    python scripts/stress_test.py quick
} elseif ($choice -eq "2") {
    python scripts/stress_test.py
} else {
    Write-Host "無效選項" -ForegroundColor Red
}

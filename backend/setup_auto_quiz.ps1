# 建立自動化任務腳本
$action = New-ScheduledTaskAction `
    -Execute "C:\Users\User\Desktop\bmad-method\backend\.venv\Scripts\python.exe" `
    -Argument "tools\generate_daily_quiz.py" `
    -WorkingDirectory "C:\Users\User\Desktop\bmad-method\backend"

$trigger = New-ScheduledTaskTrigger -Daily -At "01:00"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "MovieIn每日電影問答生成" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "每天凌晨1點自動生成當天的電影問答題目" `
    -Force

Write-Host " 自動化任務已建立！" -ForegroundColor Green
Write-Host "任務名稱: MovieIn每日電影問答生成" -ForegroundColor Cyan
Write-Host "執行時間: 每天凌晨 1:00" -ForegroundColor Cyan
Write-Host "" 
Write-Host "查看任務:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName '\'MovieIn每日電影問答生成'\'" -ForegroundColor Gray
Write-Host ""
Write-Host "測試執行:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName '\'MovieIn每日電影問答生成'\'" -ForegroundColor Gray
Write-Host ""
Write-Host "刪除任務:" -ForegroundColor Yellow
Write-Host "  Unregister-ScheduledTask -TaskName '\'MovieIn每日電影問答生成'\' -Confirm:`$false" -ForegroundColor Gray

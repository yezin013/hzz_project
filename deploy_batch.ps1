$services = @("core", "content", "chatbot", "stats", "ocr")
foreach ($svc in $services) {
    Write-Host "🚀 Deploying $svc..."
    Set-Location "d:\final_project\source\backend\services\$svc"
    # serverless deploy가 실패해도 계속 진행하도록 try-catch 또는 에러 무시 설정은 안 함 (중요하니까)
    # 하지만 cmd /c 로 실행하여 PowerShell 세션 보호
    cmd /c "serverless deploy --stage dev"
}
Write-Host "✅ All remaining services deployed!"

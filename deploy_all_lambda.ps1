# Deploy All Lambda Services Script
# Usage: .\deploy_all_lambda.ps1

$services = @("core", "search", "recommend", "content", "chatbot", "ocr", "stats")
$baseDir = "d:\final_project\source\backend\services"

Write-Host "🚀 Starting deployment for all 7 Lambda services..." -ForegroundColor Cyan

foreach ($svc in $services) {
    Write-Host "`n--------------------------------------------------"
    Write-Host "📦 Deploying Service: [$svc]" -ForegroundColor Yellow
    Write-Host "--------------------------------------------------"
    
    $svcPath = Join-Path $baseDir $svc
    if (Test-Path $svcPath) {
        Push-Location $svcPath
        
        # Execute Serverless Deploy
        # 'cmd /c' is used to ensure the command runs cleanly in the current shell context
        cmd /c "serverless deploy --stage dev"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "❌ Failed to deploy $svc" -ForegroundColor Red
        } else {
            Write-Host "✅ Successfully deployed $svc" -ForegroundColor Green
        }
        
        Pop-Location
    } else {
        Write-Host "⚠️  Directory not found: $svcPath" -ForegroundColor Red
    }
}

Write-Host "`n🎉 All deployments completed!" -ForegroundColor Cyan

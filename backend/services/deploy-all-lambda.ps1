# 7개 백엔드 서비스 Lambda 배포 스크립트
# 각 서비스를 순차적으로 배포합니다.

$services = @("content", "chatbot", "core", "ocr", "recommend", "search", "stats")
$baseDir = "d:\final_project\source\backend\services"

foreach ($service in $services) {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "Deploying $service service..." -ForegroundColor Yellow
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Set-Location "$baseDir\$service"
    
    # npm 패키지 설치 (처음만)
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing npm packages..." -ForegroundColor Gray
        npm install --save-dev serverless-python-requirements
    }
    
    # 배포
    npx sls deploy --stage dev
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ $service deployed successfully!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ $service deployment failed!" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "All services deployment completed!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

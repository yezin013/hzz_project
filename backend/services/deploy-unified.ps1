#!/usr/bin/env pwsh
# 7개 Lambda 서비스를 통합 API Gateway로 배포하는 스크립트

$services = @("chatbot", "content", "core", "ocr", "recommend", "search", "stats")
$region = "ap-northeast-2"
$stage = "dev"

Write-Host "=== 통합 API Gateway로 Lambda 서비스 배포 시작 ===" -ForegroundColor Cyan
Write-Host "API Gateway: jumak-unified-api (5p1of4jt04)" -ForegroundColor Yellow
Write-Host "Endpoint: https://5p1of4jt04.execute-api.ap-northeast-2.amazonaws.com`n" -ForegroundColor Green

foreach ($service in $services) {
    Write-Host "`n[$service] 배포 중..." -ForegroundColor Yellow
    Set-Location -Path ".\$service"
    
    serverless deploy --stage $stage --region $region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[$service] 배포 완료 ✅" -ForegroundColor Green
    } else {
        Write-Host "[$service] 배포 실패 ❌" -ForegroundColor Red
        Write-Host "Error code: $LASTEXITCODE"
    }
    
    Set-Location -Path ".."
}

Write-Host "`n=== 배포 완료 ===" -ForegroundColor Cyan
Write-Host "모든 서비스가 통합 API Gateway를 사용합니다." -ForegroundColor Green
Write-Host "`nVercel 환경변수를 업데이트하세요:" -ForegroundColor Yellow
Write-Host "NEXT_PUBLIC_SERVERLESS_API_URL=https://5p1of4jt04.execute-api.ap-northeast-2.amazonaws.com" -ForegroundColor Cyan

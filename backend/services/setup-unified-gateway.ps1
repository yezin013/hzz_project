# Unified API Gateway Setup Script
# 모든 Lambda 함수를 하나의 API Gateway에 연결합니다

$region = "ap-northeast-2"
$accountId = "799336795082"

# 1. 통합 API Gateway ID 조회
Write-Host "=== Step 1: Getting Unified API Gateway ID ===" -ForegroundColor Cyan
$apis = aws apigatewayv2 get-apis --region $region --no-paginate 2>&1 | ConvertFrom-Json
$unifiedApi = $apis.Items | Where-Object { $_.Name -eq "jumak-unified-api" } | Select-Object -First 1
$apiId = $unifiedApi.ApiId
Write-Host "API ID: $apiId"
Write-Host "Endpoint: $($unifiedApi.ApiEndpoint)"

if (-not $apiId) {
    Write-Host "Error: jumak-unified-api not found!" -ForegroundColor Red
    exit 1
}

# 2. Lambda 함수 목록 및 경로
$lambdaConfigs = @(
    @{ Name = "jumak-content-dev-api"; Paths = @("/api/python/board", "/api/python/board/{proxy+}", "/api/python/notes", "/api/python/notes/{proxy+}") },
    @{ Name = "jumak-chatbot-dev-api"; Paths = @("/api/python/chatbot", "/api/python/chatbot/{proxy+}") },
    @{ Name = "jumak-core-dev-api"; Paths = @("/api/python/fair", "/api/python/fair/{proxy+}", "/api/python/brewery", "/api/python/brewery/{proxy+}") },
    @{ Name = "jumak-ocr-dev-api"; Paths = @("/api/python/ocr", "/api/python/ocr/{proxy+}") },
    @{ Name = "jumak-recommend-dev-api"; Paths = @("/api/python/hansang", "/api/python/hansang/{proxy+}", "/api/python/cocktail", "/api/python/cocktail/{proxy+}") },
    @{ Name = "jumak-search-dev-api"; Paths = @("/api/python/search", "/api/python/search/{proxy+}") },
    @{ Name = "jumak-stats-dev-api"; Paths = @("/api/python/weather", "/api/python/weather/{proxy+}", "/api/python/chatbot/metrics", "/api/python/chatbot/metrics/{proxy+}") }
)

# Health check 추가
$lambdaConfigs += @{ Name = "jumak-content-dev-api"; Paths = @("/api/python/health") }

Write-Host "`n=== Step 2: Creating Integrations and Routes ===" -ForegroundColor Cyan

foreach ($config in $lambdaConfigs) {
    $lambdaName = $config.Name
    $lambdaArn = "arn:aws:lambda:${region}:${accountId}:function:${lambdaName}"
    
    Write-Host "`nProcessing: $lambdaName" -ForegroundColor Yellow
    
    # Integration 생성
    $integrationUri = "arn:aws:apigateway:${region}:lambda:path/2015-03-31/functions/${lambdaArn}/invocations"
    
    $integration = aws apigatewayv2 create-integration `
        --api-id $apiId `
        --integration-type AWS_PROXY `
        --integration-uri $integrationUri `
        --payload-format-version "2.0" `
        --region $region `
        --no-paginate 2>&1 | ConvertFrom-Json
    
    $integrationId = $integration.IntegrationId
    Write-Host "  Integration ID: $integrationId"
    
    # Lambda Permission 추가
    foreach ($path in $config.Paths) {
        $routeKey = "ANY $path"
        
        # Route 생성
        aws apigatewayv2 create-route `
            --api-id $apiId `
            --route-key $routeKey `
            --target "integrations/$integrationId" `
            --region $region `
            --no-paginate 2>&1 | Out-Null
        
        Write-Host "  Route: $routeKey" -ForegroundColor Green
        
        # Lambda Permission 추가 (API Gateway가 Lambda 호출 가능하도록)
        $statementId = "apigateway-$([guid]::NewGuid().ToString().Substring(0,8))"
        aws lambda add-permission `
            --function-name $lambdaName `
            --statement-id $statementId `
            --action lambda:InvokeFunction `
            --principal apigateway.amazonaws.com `
            --source-arn "arn:aws:execute-api:${region}:${accountId}:${apiId}/*" `
            --region $region `
            --no-paginate 2>&1 | Out-Null
    }
}

# 3. Stage 생성 및 배포
Write-Host "`n=== Step 3: Creating Stage and Deploying ===" -ForegroundColor Cyan

# $default stage 생성 (auto-deploy)
aws apigatewayv2 create-stage `
    --api-id $apiId `
    --stage-name '$default' `
    --auto-deploy `
    --region $region `
    --no-paginate 2>&1 | Out-Null

Write-Host "`n=== DONE ===" -ForegroundColor Green
Write-Host "Unified API Gateway URL: $($unifiedApi.ApiEndpoint)" -ForegroundColor Cyan
Write-Host "`nSet this as NEXT_PUBLIC_API_URL in Amplify!"

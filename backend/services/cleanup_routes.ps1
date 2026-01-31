$apiId = "5p1of4jt04"
Write-Host "Fetching routes for API $apiId..."
$routes = aws apigatewayv2 get-routes --api-id $apiId --no-cli-pager | ConvertFrom-Json

# 지워야 할 라우트 패턴 (실패한 서비스들)
$patterns = @(
    "/api/python/chatbot",
    "/api/python/notes",
    "/api/python/board",
    "/api/python/favorites",
    "/api/python/fair",
    "/api/python/brewery",
    "/api/python/ocr",
    "/api/python/health",  # Common health endpoint (might conflict)
    "/api/python/search"   # Search service
)

# 보존해야 할 라우트 (성공한 서비스들)
$preserve = @(
    "/api/python/hansang",
    "/api/python/cocktail",
    "/api/python/weather",
    "/api/python/chatbot/metrics",
    "/api/python/search/top-searches"
)

foreach ($item in $routes.Items) {
    $key = $item.RouteKey # e.g. "ANY /api/python/ocr/{proxy+}"
    
    # 1. Check if it matches delete patterns
    $shouldDelete = $false
    foreach ($p in $patterns) {
        if ($key -match [Regex]::Escape($p)) {
            $shouldDelete = $true
            break
        }
    }

    # 2. Check if it matches preserve patterns (Override)
    if ($shouldDelete) {
        foreach ($p in $preserve) {
            if ($key -match [Regex]::Escape($p)) {
                $shouldDelete = $false
                Write-Host "Preserving: $key" -ForegroundColor Green
                break
            }
        }
    }

    # 3. Delete if valid target
    if ($shouldDelete) {
        Write-Host "Deleting conflicting route: $key ($($item.RouteId))" -ForegroundColor Red
        aws apigatewayv2 delete-route --api-id $apiId --route-id $item.RouteId --no-cli-pager
    }
}
Write-Host "Cleanup complete."

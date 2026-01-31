Write-Host "=== Chatbot Deployment Update Start ($args[0]) ===" -ForegroundColor Cyan
$tag = "v3.171"
$repo = "799336795082.dkr.ecr.ap-northeast-2.amazonaws.com/hzz/backend-chatbot"
$image = "$repo`:$tag"

# 1. Push Image
Write-Host "Pushing Docker Image: $image"
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin 799336795082.dkr.ecr.ap-northeast-2.amazonaws.com
docker push $image
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# 2. Update Manifest
$manifestRoot = "d:\final_project\source\jumak-app-manifests"
$kustomizeFile = "$manifestRoot\overlays\aws-eks\backend-chatbot\kustomization.yaml"

Write-Host "Updating manifest: $kustomizeFile"
(Get-Content $kustomizeFile) -replace "newTag: .*", "newTag: '$tag'" | Set-Content $kustomizeFile -Encoding UTF8

# 3. Git Push
Set-Location $manifestRoot
git pull aws main --rebase
git add .
git commit -m "chore(chatbot): update image to $tag (fix logic)"
git push aws main
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Git push failed. Trying force..." 
    git push aws main --force
}

# 4. ArgoCD Sync
Write-Host "Triggering ArgoCD Sync..."
kubectl patch app backend-common -n argocd --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}'

Write-Host "=== Deployment Triggered ===" -ForegroundColor Green

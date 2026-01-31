# Environment Variables for Multi-Environment Deployment

## Overview
This project supports deployment to three environments:
- **Local K8s** (Development)
- **AWS EKS** (Production K8s)
- **AWS Amplify** (Serverless)

## Environment Variable Configuration

### For K8s Deployments (Local & EKS)
Set these in Kubernetes ConfigMaps/Secrets:

```bash
K8S_ENV=true
NEXTAUTH_URL=https://hanzanzu.cloud
NEXTAUTH_SECRET=<your-secret>
COGNITO_CLIENT_ID=<cognito-client-id>
COGNITO_CLIENT_SECRET=<cognito-client-secret>
COGNITO_ISSUER=<cognito-issuer-url>
```

### For Amplify Deployment
Set these in Amplify Console → Environment Variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `AMPLIFY_BUILD` | `true` | Enables Amplify build mode (disables standalone) |
| `NEXT_PUBLIC_API_URL` | `https://your-api-gateway-url.amazonaws.com/prod` | API Gateway base URL |
| `NEXTAUTH_URL` | `https://main.xxxxx.amplifyapp.com` | Your Amplify domain |
| `NEXTAUTH_SECRET` | `<same-as-k8s>` | NextAuth encryption secret |
| `COGNITO_CLIENT_ID` | `<same-as-k8s>` | Cognito client ID |
| `COGNITO_CLIENT_SECRET` | `<same-as-k8s>` | Cognito client secret |
| `COGNITO_ISSUER` | `<same-as-k8s>` | Cognito issuer URL |

## How It Works

### API URL Resolution
The frontend automatically detects which environment it's running in:

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/python';
```

- **K8s**: Uses `/api/python` (proxied by Ingress to backend pods)
- **Amplify**: Uses `NEXT_PUBLIC_API_URL` (direct call to API Gateway)

### Build Mode Selection
```typescript
// next.config.ts
...(process.env.AMPLIFY_BUILD !== 'true' && { output: "standalone" })
```

- **K8s**: `standalone` mode (self-contained Docker image)
- **Amplify**: Standard SSR mode (Lambda@Edge)

## Deployment Instructions

### Deploy to Amplify
1. Go to AWS Amplify Console
2. Create new app from Git repository
3. Set **Build settings**:
   - Build command: `npm run build`
   - Base directory: `frontend`
4. Add environment variables (see table above)
5. Deploy!

### Deploy to K8s (Already Working!)
```bash
# Local K8s
docker build -t frontend:latest ./frontend
kubectl apply -k overlays/on-premise/frontend

# AWS EKS
git push aws main  # GitLab CI/CD + ArgoCD auto-deploy
```

## Verification

### Test Amplify Build Locally
```bash
cd frontend
export AMPLIFY_BUILD=true
export NEXT_PUBLIC_API_URL=https://your-api-url
npm run build
npm start
```

### Test K8s Build Locally
```bash
cd frontend
export K8S_ENV=true
npm run build
npm start
```

## Backend Lambda (Future)
When you deploy backend to Lambda:
1. Create API Gateway
2. Set `NEXT_PUBLIC_API_URL` to API Gateway URL
3. Update Amplify environment variables

**For now**: Backend runs on K8s, accessible at `https://hanzanzu.cloud/api/python`

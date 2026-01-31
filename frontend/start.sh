#!/bin/sh

# 1. IP 감지 (Kubernetes Downward API를 통해 주입된 HOST_IP 사용 우선)
if [ -z "$HOST_IP" ]; then
    # HOST_IP가 없으면 컨테이너의 IP 가져오기 (단, 이건 내부 IP일 확률 높음)
    HOST_IP=$(hostname -i)
    echo "⚠️  HOST_IP not set, using container IP: $HOST_IP"
else
    echo "✅ Using provided HOST_IP: $HOST_IP"
fi

# 2. 포트 설정 (기본값: 3000 - Standard Next.js)
PORT=${PORT:-3000}

# 3. NEXTAUTH_URL 동적 설정 (이미 설정되어 있으면 건너뜀)
if [ -z "$NEXTAUTH_URL" ]; then
    export NEXTAUTH_URL="https://${HOST_IP}:${PORT}"
    echo "🚀 Auto-configured NEXTAUTH_URL: $NEXTAUTH_URL"
else
    echo "ℹ️  NEXTAUTH_URL is already set: $NEXTAUTH_URL"
fi

# 4. 서버 실행 (Standalone mode in Docker, standard Next.js in other envs)
# Dockerfile copies standalone files, so we run the standalone server
exec node server.js

"""
AWS Secrets Manager 통합 모듈
Lambda와 로컬/EKS 환경 모두에서 동작

사용법:
    from app.utils.secrets import get_secret, load_secrets_to_env
    
    # 특정 시크릿 값 가져오기
    mongo_password = get_secret("MONGODB_PASSWORD")
    
    # 모든 시크릿을 환경변수로 로드 (앱 시작 시)
    load_secrets_to_env()
"""

import os
import json
import boto3
from functools import lru_cache
from typing import Optional, Dict

# 시크릿 캐시 (Lambda Cold Start 최적화)
_secrets_cache: Optional[Dict[str, str]] = None


def _get_secrets_from_aws() -> Dict[str, str]:
    """
    AWS Secrets Manager에서 시크릿을 가져옵니다.
    Lambda 환경에서만 실행됩니다.
    """
    secret_name = os.getenv("AWS_SECRET_NAME", "jumak/backend/prod")
    region = os.getenv("AWS_REGION", "ap-northeast-2")
    
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response.get("SecretString", "{}")
        return json.loads(secret_string)
    except Exception as e:
        print(f"⚠️ Secrets Manager 접근 실패: {e}")
        return {}


def is_lambda_environment() -> bool:
    """Lambda 환경인지 확인"""
    return os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None


def get_secrets() -> Dict[str, str]:
    """
    모든 시크릿을 가져옵니다.
    - Lambda: Secrets Manager에서 로드
    - 로컬/EKS: 환경변수 사용
    """
    global _secrets_cache
    
    if _secrets_cache is not None:
        return _secrets_cache
    
    if is_lambda_environment():
        print("🔐 Lambda 환경 - Secrets Manager에서 시크릿 로드 중...")
        _secrets_cache = _get_secrets_from_aws()
        print(f"✅ {len(_secrets_cache)}개의 시크릿 로드 완료")
    else:
        # 로컬/EKS 환경에서는 환경변수를 그대로 사용
        _secrets_cache = {}
    
    return _secrets_cache


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    특정 시크릿 값을 가져옵니다.
    우선순위: 환경변수 > Secrets Manager > 기본값
    """
    # 1. 환경변수 우선 확인
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    
    # 2. Secrets Manager에서 확인
    secrets = get_secrets()
    if key in secrets:
        return secrets[key]
    
    # 3. 기본값 반환
    return default


def load_secrets_to_env() -> None:
    """
    Secrets Manager의 모든 시크릿을 환경변수로 로드합니다.
    """
    if not is_lambda_environment():
        print("📍 로컬/EKS 환경 - 환경변수 사용")
        return
    
    secrets = get_secrets()
    loaded_count = 0
    
    for key, value in secrets.items():
        if os.getenv(key) is None:
            os.environ[key] = str(value)
            loaded_count += 1
    
    print(f"🔐 {loaded_count}개의 시크릿을 환경변수로 로드함")

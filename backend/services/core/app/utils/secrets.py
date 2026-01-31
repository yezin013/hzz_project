"""
AWS Secrets Manager 통합 모듈
"""
import os
import json
import boto3
from typing import Optional, Dict

_secrets_cache: Optional[Dict[str, str]] = None

def _get_secrets_from_aws() -> Dict[str, str]:
    secret_name = os.getenv("AWS_SECRET_NAME", "jumak/backend/prod")
    region = os.getenv("AWS_REGION", "ap-northeast-2")
    try:
        client = boto3.client("secretsmanager", region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response.get("SecretString", "{}"))
    except Exception as e:
        print(f"⚠️ Secrets Manager 접근 실패: {e}")
        return {}

def is_lambda_environment() -> bool:
    return os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

def get_secrets() -> Dict[str, str]:
    global _secrets_cache
    if _secrets_cache is not None:
        return _secrets_cache
    if is_lambda_environment():
        _secrets_cache = _get_secrets_from_aws()
    else:
        _secrets_cache = {}
    return _secrets_cache

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    env_value = os.getenv(key)
    if env_value is not None:
        return env_value
    secrets = get_secrets()
    return secrets.get(key, default)

def load_secrets_to_env() -> None:
    if not is_lambda_environment():
        return
    secrets = get_secrets()
    for key, value in secrets.items():
        if os.getenv(key) is None:
            os.environ[key] = str(value)

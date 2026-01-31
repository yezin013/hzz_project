"""AWS Secrets Manager 통합 모듈"""
import os, json, boto3
from typing import Optional, Dict

_secrets_cache: Optional[Dict[str, str]] = None

def _get_secrets_from_aws() -> Dict[str, str]:
    try:
        client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "ap-northeast-2"))
        response = client.get_secret_value(SecretId=os.getenv("AWS_SECRET_NAME", "jumak/backend/prod"))
        return json.loads(response.get("SecretString", "{}"))
    except Exception as e:
        print(f"⚠️ Secrets Manager 접근 실패: {e}")
        return {}

def is_lambda_environment() -> bool:
    return os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

def get_secrets() -> Dict[str, str]:
    global _secrets_cache
    if _secrets_cache is None:
        _secrets_cache = _get_secrets_from_aws() if is_lambda_environment() else {}
    return _secrets_cache

def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    return os.getenv(key) or get_secrets().get(key, default)

def load_secrets_to_env() -> None:
    if not is_lambda_environment():
        return
    for key, value in get_secrets().items():
        if os.getenv(key) is None:
            os.environ[key] = str(value)

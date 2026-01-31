"""
Lambda Handler for Chatbot Service
"""
try:
    from app.utils.secrets import load_secrets_to_env
    load_secrets_to_env()
except Exception as e:
    print(f"⚠️ Failed to load secrets: {e}")

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="auto")

import os
import urllib.parse
from motor.motor_asyncio import AsyncIOMotorClient

# Secrets Manager 통합 모듈 사용
try:
    from app.utils.secrets import get_secret, get_mongodb_config, load_secrets_to_env
    # Lambda 환경에서 시크릿 로드
    load_secrets_to_env()
except ImportError:
    # 폴백: 환경변수 직접 사용
    def get_secret(key, default=None):
        return os.getenv(key, default)
    def get_mongodb_config():
        return {}

class MongoDB:
    client: AsyncIOMotorClient = None

db = MongoDB()

async def get_database():
    try:
        return db.client.get_database("myapp_db")
    except Exception:
        return db.client.get_database("myapp_db")

async def connect_to_mongo():
    """
    MongoDB Replica Set에 연결합니다.
    Primary가 다운되면 자동으로 Secondary로 failover됩니다.
    Replica Set 연결 실패 시 단일 노드로 fallback합니다.
    """
    # Secrets Manager 또는 환경변수에서 설정 로드
    mongo_url = get_secret("MONGO_URL")
    
    hosts = get_secret("MONGODB_HOSTS", "localhost")
    port = get_secret("MONGODB_PORT", "27017")
    user = get_secret("MONGODB_USER", "root")
    password = get_secret("MONGODB_PASSWORD", "pass123#")
    db_name = get_secret("MONGODB_DB", "admin")
    replica_set = get_secret("MONGODB_REPLICA_SET", "rs0")
    
    # Lambda 환경 감지 - 더 짧은 타임아웃 사용
    is_lambda = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
    server_timeout = 10000 if is_lambda else 30000  # 10초 vs 30초
    connect_timeout = 8000 if is_lambda else 20000  # 8초 vs 20초
    
    # Password URL encoding
    encoded_password = urllib.parse.quote_plus(password)
    
    # 여러 호스트를 파싱
    host_list = [host.strip() for host in hosts.split(",")]
    
    # 먼저 Replica Set으로 연결 시도
    if mongo_url:
        replica_url = mongo_url
        print(f"🔍 MongoDB 연결 시도 (URL 사용): {mongo_url.split('@')[-1]}")  # 비밀번호 노출 방지
    else:
        hosts_string = ",".join([f"{host}:{port}" for host in host_list])
        replica_url = f"mongodb://{user}:{encoded_password}@{hosts_string}/{db_name}?replicaSet={replica_set}&authSource=admin"
        env_type = "Lambda" if is_lambda else "Local/EKS"
        print(f"🔍 MongoDB 연결 시도 ({env_type}): {host_list}")
    

    
    try:
        db.client = AsyncIOMotorClient(
            replica_url,
            serverSelectionTimeoutMS=server_timeout,
            connectTimeoutMS=connect_timeout,
            retryWrites=True,
            maxPoolSize=10 if is_lambda else 50  # Lambda에서 풀 크기 축소
        )
        
        # 연결 테스트
        await db.client.admin.command('ping')
        
        # 연결된 서버 정보 출력
        server_info = await db.client.server_info()
        
        print("=" * 60)
        print("✅ MongoDB Replica Set 연결 성공!")
        print(f"📦 MongoDB 버전: {server_info.get('version', 'Unknown')}")
        
        # Replica Set 상태 확인
        try:
            replica_status = await db.client.admin.command('replSetGetStatus')
            members = replica_status.get('members', [])
            
            print(f"🖥️  Replica Set: {replica_set}")
            print(f"🔗 총 멤버 수: {len(members)}")
            print("\n📋 Replica Set 멤버 목록:")
            
            for member in members:
                state_str = member.get('stateStr', 'Unknown')
                health = '✅' if member.get('health') == 1 else '❌'
                primary_mark = '⭐ (PRIMARY)' if state_str == 'PRIMARY' else ''
                host = member.get('name', 'Unknown')
                
                print(f"  {health} {host} | {state_str} {primary_mark}")
                
        except Exception as e:
            print(f"⚠️  Replica Set 상태 확인 불가: {e}")
        
        print("=" * 60)
        return
        
    except Exception as replica_error:
        print(f"⚠️  Replica Set 연결 실패: {replica_error}")
        print("🔄 단일 노드 연결로 fallback 시도 중...")
        
        # Fallback: 각 호스트에 직접 연결 시도
        for host in host_list:
            try:
                single_url = f"mongodb://{user}:{encoded_password}@{host}:{port}/{db_name}?authSource=admin"
                print(f"  📍 {host}:{port} 연결 시도...")
                
                db.client = AsyncIOMotorClient(
                    single_url,
                    serverSelectionTimeoutMS=20000,  # 20 seconds for fallback
                    connectTimeoutMS=15000,  # 15 seconds for fallback connection
                    maxPoolSize=50
                )
                
                # 연결 테스트
                await db.client.admin.command('ping')
                server_info = await db.client.server_info()
                
                print("=" * 60)
                print(f"✅ MongoDB 단일 노드 연결 성공!")
                print(f"📍 연결된 호스트: {host}:{port}")
                print(f"📦 MongoDB 버전: {server_info.get('version', 'Unknown')}")
                print("=" * 60)
                return
                
            except Exception as single_error:
                print(f"  ❌ {host} 연결 실패: {single_error}")
                if db.client:
                    db.client.close()
                    db.client = None
                continue
        
        # 모든 연결 시도 실패
        print("=" * 60)
        print("❌ MongoDB 연결 완전 실패 - 모든 호스트 연결 불가")
        print(f"   시도한 호스트: {host_list}")
        print("=" * 60)
        print(f"⚠️  MongoDB 연결 실패: 모든 호스트({host_list})에 연결할 수 없습니다")
        print("⚠️  서버는 제한된 기능으로 시작됩니다.")
        return

async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")

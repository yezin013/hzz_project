from elasticsearch import Elasticsearch
import os

import time

def get_connected_node_info(es):
    """현재 연결된 Elasticsearch 노드 정보를 반환하고 로그 출력"""
    try:
        # 클러스터 정보 가져오기
        info = es.info()
        node_name = info.get('name', 'Unknown')
        cluster_name = info.get('cluster_name', 'Unknown')
        version = info.get('version', {}).get('number', 'Unknown')
        
        # 클러스터의 모든 노드 정보
        nodes_info = es.cat.nodes(format='json')
        
        print("=" * 60)
        print("✅ Elasticsearch 연결 성공!")
        print(f"📍 현재 연결된 노드: {node_name}")
        print(f"🔗 클러스터 이름: {cluster_name}")
        print(f"📦 Elasticsearch 버전: {version}")
        print(f"🖥️  클러스터 전체 노드 수: {len(nodes_info)}")
        
        # 모든 노드 정보 출력
        if nodes_info:
            print("\n📋 클러스터 노드 목록:")
            for node in nodes_info:
                role = node.get('node.role', 'unknown')
                master = '⭐ (master)' if node.get('master') == '*' else ''
                print(f"  - {node.get('name', 'unknown')} | IP: {node.get('ip', 'N/A')} | Role: {role} {master}")
        
        print("=" * 60)
        
        return {
            'node_name': node_name,
            'cluster_name': cluster_name,
            'version': version,
            'all_nodes': nodes_info
        }
    except Exception as e:
        print(f"❌ 노드 정보 확인 실패: {e}")
        return None

def get_es_client(max_retries=5, retry_delay=2):
    # Load env variables inside function to ensure dotenv has loaded
    ES_HOSTS = os.getenv("ELASTICSEARCH_HOSTS")
    ES_PORT = os.getenv("ELASTICSEARCH_PORT", "9200")
    ES_USERNAME = os.getenv("ELASTICSEARCH_USERNAME")
    ES_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
    
    # Validate required env variables
    if not ES_HOSTS:
        raise ValueError("ELASTICSEARCH_HOSTS environment variable is required")
    if not ES_USERNAME or not ES_PASSWORD:
        raise ValueError("ELASTICSEARCH_USERNAME and ELASTICSEARCH_PASSWORD are required")
    
    # Parse multiple hosts from comma-separated string
    hosts = [f"https://{host.strip()}:{ES_PORT}" for host in ES_HOSTS.split(",")]
    
    print(f"🔍 Attempting to connect to Elasticsearch cluster at: {hosts}")
    print(f"🔍 Username: {ES_USERNAME}")
    
    retries = 0
    while retries < max_retries:
        try:
            # Use basic_auth with HTTPS and disable SSL verification
            es = Elasticsearch(
                hosts, 
                basic_auth=(ES_USERNAME, ES_PASSWORD),
                verify_certs=False,
                ssl_show_warn=False
            )
                
            if es.ping():
                # 연결 성공 시 노드 정보 출력
                get_connected_node_info(es)
                return es
            else:
                print(f"Elasticsearch ping failed. Retrying ({retries+1}/{max_retries})...")
                try:
                    print(es.info())
                except Exception as e:
                    print(f"Debug Info: {e}")
        except Exception as e:
            print(f"Error connecting to Elasticsearch: {e}. Retrying ({retries+1}/{max_retries})...")
        
        retries += 1
        time.sleep(retry_delay)
    
    print("Could not connect to Elasticsearch after multiple attempts.")
    return None

def create_index_if_not_exists(es, index_name="liquors"):
    if not es.indices.exists(index=index_name):
        es.indices.create(
            index=index_name,
            body={
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "nori_analyzer": {
                                "tokenizer": "nori_tokenizer"
                            },
                            "hangul_to_latin": {
                                "tokenizer": "standard",
                                "filter": ["icu_transform_hangul_latin", "lowercase"]
                            }
                        },
                        "filter": {
                            "icu_transform_hangul_latin": {
                                "type": "icu_transform",
                                "id": "Hangul-Latin; NFD; [:Nonspacing Mark:] Remove; NFC" 
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "name": {
                            "type": "text", 
                            "analyzer": "nori_analyzer",
                            "fields": {
                                "romanized": {
                                    "type": "text",
                                    "analyzer": "hangul_to_latin"
                                }
                            }
                        }, 
                        "description": {"type": "text", "analyzer": "nori_analyzer"},
                        "intro": {"type": "text", "analyzer": "nori_analyzer"},
                        "tags": {"type": "keyword"},
                        "image_url": {"type": "keyword"},
                        "url": {"type": "keyword"},
                        "pairing_food": {"type": "text", "analyzer": "nori_analyzer"},
                        "detail": {
                            "properties": {
                                "기타": {"type": "text"},
                                "수상내역": {"type": "text"},
                                "알콜도수": {"type": "keyword"},
                                "용량": {"type": "keyword"},
                                "원재료": {"type": "text"},
                                "종류": {"type": "keyword"}
                            }
                        },
                        "brewery": {
                            "properties": {
                                "name": {"type": "text", "analyzer": "nori_analyzer"},
                                "address": {"type": "text"},
                                "contact": {"type": "keyword"},
                                "homepage": {"type": "keyword"}
                            }
                        }
                    }
                }
            }
        )
        print(f"Index '{index_name}' created with ICU analyzer.")

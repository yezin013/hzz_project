from fastapi import APIRouter
from app.utils.es_client import get_es_client, get_connected_node_info

router = APIRouter()

@router.get("/health")
async def health_check():
    """기본 헬스 체크 엔드포인트"""
    return {"status": "ok", "service": "backend"}

@router.get("/es-info")
async def get_elasticsearch_info():
    """
    현재 연결된 Elasticsearch 노드 정보를 반환합니다.
    
    Returns:
        - connected_node: 현재 연결된 노드 이름
        - cluster_name: 클러스터 이름
        - version: Elasticsearch 버전
        - all_nodes: 클러스터의 모든 노드 정보 리스트
    """
    try:
        es = get_es_client()
        if not es:
            return {
                "status": "error",
                "message": "Elasticsearch 연결 실패"
            }
        
        node_info = get_connected_node_info(es)
        
        if node_info:
            return {
                "status": "connected",
                "connected_node": node_info['node_name'],
                "cluster_name": node_info['cluster_name'],
                "version": node_info['version'],
                "total_nodes": len(node_info['all_nodes']),
                "all_nodes": node_info['all_nodes']
            }
        else:
            return {
                "status": "error",
                "message": "노드 정보를 가져올 수 없습니다"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@router.get("/es-cluster-health")
async def get_cluster_health():
    """
    Elasticsearch 클러스터 헬스 상태를 반환합니다.
    
    Returns:
        클러스터 헬스 정보 (green/yellow/red)
    """
    try:
        es = get_es_client()
        if not es:
            return {"status": "error", "message": "Elasticsearch 연결 실패"}
        
        health = es.cluster.health()
        
        return {
            "status": "ok",
            "cluster_health": health['status'],
            "cluster_name": health['cluster_name'],
            "number_of_nodes": health['number_of_nodes'],
            "active_shards": health['active_shards'],
            "relocating_shards": health['relocating_shards'],
            "initializing_shards": health['initializing_shards'],
            "unassigned_shards": health['unassigned_shards']
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

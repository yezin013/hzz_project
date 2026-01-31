# Ragas 평가 스크립트 (AWS Bedrock 연동)
import json
import os
from datasets import Dataset

# Ragas 메트릭 (새로운 import 방식)
from ragas import evaluate
from ragas.metrics import Faithfulness, ResponseRelevancy

# Bedrock LLM 래퍼
from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings

def load_evaluation_data():
    """evaluation_results.json에서 데이터 로드"""
    with open('evaluation_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    # Ragas 형식으로 변환
    data = {
        "user_input": [],
        "response": [],
        "retrieved_contexts": [],
    }
    
    for r in results:
        if r.get('answer'):
            data["user_input"].append(r.get('question', ''))
            data["response"].append(r.get('answer', ''))
            data["retrieved_contexts"].append(["전통주 데이터베이스에서 검색된 정보"])
    
    return Dataset.from_dict(data)


def run_ragas_evaluation():
    """Ragas 평가 실행"""
    print("📊 Ragas RAG 평가 시작...")
    
    # AWS Bedrock 설정
    llm = ChatBedrock(
        model_id="amazon.nova-lite-v1:0",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        model_kwargs={"temperature": 0.0}
    )
    
    embeddings = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v1",
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    
    # 데이터 로드
    dataset = load_evaluation_data()
    print(f"✅ 테스트 데이터 {len(dataset)}개 로드 완료")
    
    # Ragas 평가 실행
    metrics = [
        Faithfulness(),
        ResponseRelevancy(),
    ]
    
    result = evaluate(
        dataset=dataset,
        metrics=metrics,
        llm=llm,
        embeddings=embeddings
    )
    
    # 결과 출력
    print("\n" + "="*50)
    print("📊 Ragas 평가 결과")
    print("="*50)
    
    # 새로운 결과 처리 방식
    print(result)
    
    # DataFrame으로 저장
    df = result.to_pandas()
    df.to_csv('ragas_results.csv', index=False, encoding='utf-8')
    print("\n📁 결과 저장: ragas_results.csv")
    
    return result


if __name__ == "__main__":
    run_ragas_evaluation()

# 업데이트 가이드: Nori 플러그인 설치

한국어 텍스트 분석을 지원하기 위해 전용 서버에 `analysis-nori` 플러그인을 설치해야 합니다.

## 1단계: Dockerfile 생성

**전용 서버**에서 `docker-compose.yaml` 파일이 있는 폴더로 이동한 후:

1.  `Dockerfile`이라는 이름으로 새 파일을 만드세요.
2.  아래 내용을 복사해서 붙여넣으세요:

    ```dockerfile
퍄 
    ```

## 2단계: docker-compose.yaml 수정

**전용 서버**에서 `docker-compose.yaml` 파일을 열고 `elasticsearch` 서비스 부분을 수정하세요.

**변경 전:**
```yaml
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.10.4
    # ... 다른 설정들 ...
```

**변경 후:**
```yaml
  elasticsearch:
    build: .  # <--- 'image' 대신 'build'를 사용합니다
    # image: ... (이 줄은 지우거나 주석 처리하세요)
    container_name: es01
    # ... 다른 설정들(environment, ports, volumes)은 그대로 두세요 ...
```

## 3단계: 다시 빌드하고 재시작

아래 명령어를 실행해서 플러그인이 포함된 이미지를 새로 만들고 컨테이너를 재시작하세요:

```bash
퍄 애 ```

## 4단계: 확인

재시작이 완료되면, 서버에서 아래 명령어를 실행(또는 개발 컴퓨터에서 curl 사용)해서 플러그인이 잘 설치되었는지 확인하세요:

```bash
curl -u elastic:pass123 http://localhost:9200/_cat/plugins?v
```
목록에 `analysis-nori`가 보이면 성공입니다.

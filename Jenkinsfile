pipeline {
    // 빌드 에이전트 설정 (184 서버) - Force Rebuild for Nginx
    agent { label 'app-184' }

    environment {
        // Harbor 주소 및 프로젝트 설정
        REGISTRY = 'harbor.local.net'
        PROJECT = 'charlie'

        // 이미지 이름 (Docker Build에 사용)
        IMAGE_NAME_STRING = 'frontend,backend,nginx'

        // Harbor에 로그인할 자격 증명 ID
        CREDENTIAL_ID = 'harbor-login'

        // SonarQube 서버 정보
        SONARQUBE_URL = 'http://192.168.0.181:9000'
        // Jenkins Credentials Binding을 사용하여 주입하거나 환경주입 설정 필요
        SONARQUBE_TOKEN = credentials('sonarqube-token')

        // Jenkins 시스템 설정에서 정의한 SonarQube 서버 이름
        SONARQUBE_SERVER_ID = 'sonarqube-local'

        // IMAGE_TAG를 빌드 번호를 사용하여 직접 정의 (v1.110 형식)
        IMAGE_TAG = "v1.${BUILD_NUMBER}"
    }

    stages {
        stage('Check Changes') {
            steps {
                script {
                    echo "--- Checking for Code Changes ---"
                    // Get list of changed files between current and previous commit
                    // Fallback to checking uncommitted changes if HEAD^ fails (e.g. first commit)
                    def changedFiles = ""
                    try {
                        changedFiles = sh(script: "git diff --name-only HEAD^ HEAD", returnStdout: true).trim()
                    } catch (Exception e) {
                        echo "⚠️ git diff failed (first commit?), assuming everything changed."
                        changedFiles = "frontend/ backend/ Jenkinsfile"
                    }
                    
                    echo "📝 Changed Files:\n${changedFiles}"
                    
                    def targets = []
                    
                    // If Jenkinsfile changes, build everything safely
                    if (changedFiles.contains("Jenkinsfile")) {
                        echo "⚡ Jenkinsfile changed. Rebuilding EVERYTHING."
                        targets = ['frontend', 'backend', 'nginx']
                    } else {
                        if (changedFiles.contains("frontend/")) {
                            targets.add('frontend')
                        }
                        if (changedFiles.contains("backend/")) {
                            targets.add('backend')
                        }
                        if (changedFiles.contains("nginx/")) {
                            targets.add('nginx')
                        }
                    }
                    
                    // If nothing relevant changed (only README?), skip or inform
                    if (targets.isEmpty()) {
                        echo "🛑 No relevant code changes detected (frontend/backend). Skipping build."
                    } else {
                        echo "🎯 Build Targets: ${targets.join(', ')}"
                    }
                    
                    // Save to env for other stages (as comma-separated string)
                    env.TARGET_IMAGES = targets.join(',')
                }
            }
        }

        stage('SCM') {
            steps {
                echo "--- 1. Git Repository Checkout ---"
                checkout scm
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    echo "--- 2. SonarQube Code Analysis Started ---"
                    withEnv(['JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64']) {
                        withSonarQubeEnv(env.SONARQUBE_SERVER_ID) {
                            def scannerHome = tool 'SonarScanner'
                            sh "export JAVA_HOME=${JAVA_HOME} && ${scannerHome}/bin/sonar-scanner -Dsonar.projectKey=charlie-monorepo -Dsonar.sources=."
                        }
                    }
                }
            }
        }

        stage("Quality Gate Check") {
            steps {
                script {
                    echo "--- 3. Waiting for SonarQube Quality Gate Result (Max 5 mins) ---"
                    timeout(time: 5, unit: 'MINUTES') {
                        // Quality Gate 실패 시에도 파이프라인 중단하지 않음 (abortPipeline: false)
                        waitForQualityGate abortPipeline: false
                    }
                }
            }
        }

        stage('Integration Test') {
            when { expression { return env.TARGET_IMAGES.contains('frontend') } }
            steps {
                echo "--- 4. Integration Tests Started (API/E2E Test) ---"
                sh "cd frontend && npm install && npm test"
                echo "✅ Integration Tests Passed."
            }
        }
        
        // Calculate Version 스테이지 제거됨 (environment 변수로 대체)

        stage('Build, Scan & Push') {
            steps {
                script {
                    if (env.TARGET_IMAGES == "") {
                         echo "⏭️ No targets to build. Skipping stage."
                         return
                    }
                    
                    echo "--- 5. Build, Scan with Trivy, and Push to Harbor ---"
                    def images = env.TARGET_IMAGES.split(',')

                    images.each { image ->
                        def fullImageName = "${REGISTRY}/${PROJECT}/${image}:${env.IMAGE_TAG}"

                        // 5-1. Docker 이미지 빌드
                        if (image == 'frontend') {
                            echo "Creating temporary frontend.env for build..."
                            // API_URL을 상대 경로(/api/python)로 설정
                            sh "echo 'NEXT_PUBLIC_API_URL=/api/python' > ./${image}/frontend.env"
                        }

                        sh "docker build -t ${fullImageName} ./${image}"

                        // 5-2. 🚀 Trivy 보안 스캔
                        echo "--- Trivy Security Scan for ${image} Started ---"
                        def trivyImage = "${fullImageName}"
                        def scan_command = "trivy image --severity CRITICAL --exit-code 1 --format table ${trivyImage}"

                        try {
                            sh scan_command
                            echo "✅ Trivy Scan Passed for ${image}. Security Gate is GREEN."
                        } catch (e) {
                            error "🚨 Trivy Scan Failed for ${image}: CRITICAL vulnerabilities detected. Fix Dockerfile and redeploy."
                        }

                        // 5-3. Docker 로그인 및 푸시
                        withCredentials([usernamePassword(credentialsId: CREDENTIAL_ID, usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                            sh "docker login ${REGISTRY} -u \$USER -p \$PASS"
                            sh "docker push ${fullImageName}"
                        }
                        echo "✅ ${fullImageName} 푸시 완료"
                    }
                }
            }
        }

        stage('Deploy to Dev') {
            steps {
                script {
                    if (env.TARGET_IMAGES == "") {
                         echo "⏭️ No targets to deploy. Skipping stage."
                         return
                    }

                    echo "--- 6. Deploy to Dev Server (184) ---"
                    def images = env.TARGET_IMAGES.split(',')

                    images.each { image ->
                        def fullImageName = "${REGISTRY}/${PROJECT}/${image}:${env.IMAGE_TAG}"

                        // 1. 기존 컨테이너 삭제 (충돌 방지)
                        sh "docker rm -f ${image}-server || true"

                        // 2. 이미지 풀
                        sh "docker pull ${fullImageName}"

                        // 3. 컨테이너 실행 (184 환경변수 주입)
                        if (image == 'frontend') {
                             // Frontend needs Cognito secrets (in frontend.env on host)
                             sh "docker run -d --network host --env-file /home/kevin/frontend.env -e NEXTAUTH_URL=https://192.168.0.184 --name ${image}-server ${fullImageName}"
                        } else if (image == 'backend') {
                             // Backend needs env vars (DB, API Keys) which are in a file on the host
                             // + OpenTelemetry settings for Host Network (localhost:4319) and Public IP (184)
                             sh "docker run -d --network host --env-file /home/kevin/backend.env -e NODE_IP=192.168.0.184 -e OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4319 --name ${image}-server ${fullImageName}"
                        } else {
                             // Nginx: Use Host Network mode (replace service names with 127.0.0.1 via entrypoint)
                             sh "docker run -d --network host -e USE_HOST_NETWORK=true --name ${image}-server ${fullImageName}"
                        }

                        echo "🚀 ${image} 배포 완료 (Dev Server: 192.168.0.184)"
                    }
                }
            }
        }

        stage('Deploy to Production') {
            steps {
                script {
                    if (env.TARGET_IMAGES == "") {
                         return
                    }

                    // 수동 승인 단계 (운영 배포 전 관리자 확인)
                    timeout(time: 1, unit: 'HOURS') {
                        input message: 'QA 및 개발 배포 테스트 완료! Production 배포를 승인하시겠습니까?', submitter: 'admin'
                    }

                    echo "--- 7. Deploy to Production Server ---"
                    def images = env.TARGET_IMAGES.split(',')

                    images.each { image ->
                        def fullImageName = "${REGISTRY}/${PROJECT}/${image}:${env.IMAGE_TAG}"
                        echo "🚀 ${image} 배포 준비 완료 (Production Server)"
                    }
                }
            }
        }
    }
}

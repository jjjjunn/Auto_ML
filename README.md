# 🤖 Auto ML Platform

사용자가 CSV 파일을 업로드하여 자동으로 머신러닝 모델을 학습시키고, RAG 기반 챗봇과 대화할 수 있는 종합적인 AI 플랫폼입니다.

## 📋 주요 기능

### 🔐 소셜 로그인
- Google, Kakao, Naver 계정으로 간편 로그인
- 로그인 없이도 체험 가능 (제한된 기능)
- JWT 기반 안전한 인증 시스템

### 📊 자동 머신러닝
- **분류 모델**: 범주형 데이터 예측 (스팸 분류, 고객 등급 등)
- **회귀 모델**: 연속형 수치 예측 (가격 예측, 매출 예측 등)
- **군집 분석**: 데이터 그룹화 (고객 세분화, 상품 분류 등)
- **추천 시스템**: 개인화된 추천 (상품 추천, 콘텐츠 추천 등)
- **시계열 예측**: 시간에 따른 변화 예측 (주가, 수요 예측 등)

### 💬 RAG 기반 AI 챗봇
- 업로드한 데이터에 대한 질문 답변
- 모델 선택 및 최적화 조언
- 머신러닝 개념 설명 (비전문가도 쉽게 이해)
- 실시간 대화형 인터페이스

### ⚡ 비동기 작업 처리
- Celery + Redis를 통한 백그라운드 모델 학습
- 실시간 학습 진행률 모니터링
- 대용량 데이터셋 처리 지원

## 🚀 설치 및 실행 방법

### 1️⃣ 요구사항
- Python 3.9+
- Redis (Celery 작업 큐용)
- Git

### 2️⃣ 설치
```bash
# 프로젝트 클론
git clone <repository-url>
cd Auto_ML

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 의존성 설치
cd backend
pip install -r requirements.txt
```

### 3️⃣ 환경 설정
```bash
# 환경 변수 파일 복사
cp .env.example .env.local

# .env.local 파일을 편집하여 필요한 설정 입력
# - 소셜 로그인 키 (Google, Kakao, Naver)
# - 데이터베이스 URL
# - JWT 시크릿 키 등
```

### 4️⃣ 실행

#### 🚀 간편 실행 (권장)
```bash
# 프로젝트 루트에서 모든 서비스를 한번에 실행
start_all.bat  # Windows
./start_all.sh # Linux/macOS
```

#### 개별 실행
**백엔드 API 서버**
```bash
cd backend
python main.py
```
→ http://localhost:8001 에서 실행
→ API 문서: http://localhost:8001/docs

**Celery 워커 (비동기 작업 처리)**
```bash
# Redis 서버 실행 (별도 터미널)
redis-server

# Celery 워커 실행 (별도 터미널)
cd backend
python celery_start.py worker
```

**프론트엔드 (Streamlit)**
```bash
streamlit run app.py
```
→ http://localhost:8501 에서 실행

## 🎯 사용 방법

### 1️⃣ 로그인
- 웹 브라우저에서 http://localhost:8501 접속
- Google, Kakao, Naver 중 원하는 소셜 계정으로 로그인
- 또는 "로그인 없이 체험하기" 선택

### 2️⃣ 데이터 업로드
- "데이터 & 모델" 탭에서 CSV 파일 업로드
- 자동으로 데이터 분석 및 미리보기 제공
- 데이터 통계 정보 확인

### 3️⃣ 모델 학습
- 적절한 모델 유형 선택 (분류/회귀/군집/추천/시계열)
- 타겟 변수와 특성 변수 선택
- "모델 학습 시작" 클릭
- 실시간 진행률 확인

### 4️⃣ AI 챗봇 대화
- "AI 챗봇" 탭에서 질문 입력
- 데이터나 모델에 대한 궁금증 해결
- 머신러닝 개념 설명 요청

### 5️⃣ 모델 관리
- "모델 관리" 탭에서 학습된 모델 목록 확인
- 성능 지표 및 상세 정보 조회
- 새로운 데이터로 예측 수행

## 🔧 기술 스택

### 백엔드 API
- **FastAPI**: 고성능 웹 API 프레임워크 + 자동 문서화
- **SQLAlchemy**: ORM 데이터베이스 관리 (SQLite 기본)
- **Celery**: 비동기 작업 큐 시스템
- **Redis**: 메시지 브로커 및 캐시 저장소
- **PyCaret**: 자동화된 머신러닝 라이브러리

### 프론트엔드
- **Streamlit**: 빠른 웹 앱 개발 프레임워크
- **Plotly**: 인터랙티브 데이터 시각화
- **Pandas**: 데이터 처리 및 분석
- **Requests**: API 통신

### 인공지능 & ML
- **ChromaDB**: 벡터 데이터베이스 (RAG용)
- **Sentence Transformers**: 텍스트 임베딩
- **LangChain**: RAG 파이프라인 구축
- **Scikit-learn**: 전통적인 머신러닝 알고리즘

### 인증 시스템
- **OAuth 2.0**: 소셜 로그인 (Google, Kakao, Naver)
- **JWT**: 토큰 기반 안전한 인증
- **Authlib**: 인증 처리 라이브러리

## 📁 프로젝트 구조

```
Auto_ML/
├── 📁 backend/                 # 백엔드 API 서버
│   ├── main.py                # FastAPI 애플리케이션 진입점  
│   ├── config.py              # 설정 관리
│   ├── tasks.py               # Celery 비동기 작업
│   ├── celery_start.py        # Celery 워커 시작 스크립트
│   ├── start_dev.py           # 개발 서버 시작 스크립트
│   ├── 📁 database/            # 데이터베이스 관련
│   │   ├── database.py        # DB 연결 및 초기화
│   │   └── models.py          # SQLAlchemy 모델 정의
│   ├── 📁 models/              # Pydantic 스키마
│   │   └── schemas.py         # API 요청/응답 스키마
│   ├── 📁 routes/              # API 라우터 (✅ 라우트 문제 해결 완료)
│   │   ├── auth_routes.py     # 일반 인증 (JWT)
│   │   ├── data_routes.py     # 데이터 업로드/관리 (/upload 추가)
│   │   ├── ml_routes.py       # 머신러닝 모델 (/models 추가)
│   │   ├── chat_routes.py     # RAG 챗봇
│   │   ├── task_routes.py     # 비동기 작업 상태
│   │   └── user_log_routes.py # 사용자 활동 로그
│   ├── 📁 services/            # 비즈니스 로직
│   │   ├── auto_ml.py         # 자동 ML 파이프라인
│   │   ├── ml_service.py      # 머신러닝 서비스
│   │   ├── rag_service.py     # RAG 챗봇 서비스  
│   │   ├── data_service.py    # 데이터 처리 서비스
│   │   ├── ai_recommendation_service.py # AI 추천
│   │   ├── report_service.py  # PDF 보고서 생성
│   │   └── user_log_service.py # 활동 로그 서비스
│   ├── 📁 controllers/         # 컨트롤러 로직
│   │   └── users_controllers.py # 사용자 관리
│   ├── 📁 oauth/               # 소셜 로그인
│   │   └── social_auth.py     # OAuth 처리 (Google, Kakao, Naver)
│   ├── 📁 utils/               # 유틸리티
│   │   ├── env_loader.py      # 환경변수 로더
│   │   ├── logger.py          # 로깅 설정  
│   │   └── utils.py           # 공통 유틸리티
│   ├── requirements.txt       # Python 의존성
│   ├── .env.example          # 환경변수 예시 파일
│   ├── .env.local            # 로컬 환경변수 (git 무시)
│   ├── Dockerfile            # Docker 컨테이너 설정
│   └── docker-compose.yml    # 멀티컨테이너 오케스트레이션
├── 📁 frontend/               # 프론트엔드 (Streamlit)
│   ├── app.py               # 메인 Streamlit 앱
│   ├── 📁 pages/             # 페이지 컴포넌트들
│   │   ├── _login.py        # 로그인 페이지
│   │   ├── data_visualize.py # 데이터 시각화
│   │   ├── ml_model_training.py # 모델 학습
│   │   └── user_logs.py     # 사용자 로그
│   ├── 📁 components/        # 재사용 가능한 컴포넌트
│   │   └── ml_tips.py       # ML 팁 컴포넌트
│   └── requirements.txt     # 프론트엔드 의존성
├── 📁 scripts/               # 유틸리티 스크립트
├── app.py                   # Streamlit 진입점
├── run.bat                  # Windows 실행 스크립트
├── start_all.bat           # 모든 서비스 시작 (Windows)
├── README.md               # 📖 프로젝트 문서 (현재 파일)
└── .gitignore              # Git 무시 파일 목록
```

## 🔐 환경 변수 설정

`.env.local` 파일에서 다음 설정을 변경하세요:

```bash
# 보안 키 (반드시 변경!)
JWT_SECRET_KEY=your-super-secret-jwt-key-here
SESSION_SECRET_KEY=your-session-secret-key-here

# 소셜 로그인 설정
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

KAKAO_CLIENT_ID=your_kakao_client_id
KAKAO_CLIENT_SECRET=your_kakao_client_secret

NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# 데이터베이스 (기본값: SQLite)
DATABASE_URL=sqlite:///./automl.db

# Redis (기본값: 로컬)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🌐 소셜 로그인 설정

### Google OAuth 설정
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. OAuth 2.0 클라이언트 ID 생성
4. 승인된 리디렉션 URI: `http://localhost:8001/auth/google/callback`

### Kakao OAuth 설정
1. [Kakao Developers](https://developers.kakao.com) 접속
2. 애플리케이션 생성
3. 플랫폼 설정에서 Web 플랫폼 추가
4. Redirect URI: `http://localhost:8001/auth/kakao/callback`

### Naver OAuth 설정
1. [네이버 개발자센터](https://developers.naver.com) 접속
2. 애플리케이션 등록
3. 서비스 URL: `http://localhost:8501`
4. Callback URL: `http://localhost:8001/auth/naver/callback`

## 📊 지원하는 데이터 형식

### 입력 데이터
- **파일 형식**: CSV (UTF-8 인코딩 권장)
- **최대 크기**: 100MB
- **데이터 타입**: 수치형, 범주형, 날짜형 모두 지원

### 모델별 데이터 요구사항
- **분류**: 범주형 타겟 변수 (예: A, B, C 또는 0, 1, 2)
- **회귀**: 수치형 타겟 변수 (예: 가격, 점수)
- **군집**: 타겟 변수 불필요 (특성 변수만 사용)
- **추천**: 사용자-아이템 매트릭스 형태
- **시계열**: 날짜/시간 컬럼 + 수치형 데이터

## 🤝 기여하기

1. Fork 프로젝트
2. 새 기능 브랜치 생성 (`git checkout -b feature/새기능`)
3. 커밋 (`git commit -am 'Add 새기능'`)
4. 브랜치에 Push (`git push origin feature/새기능`)
5. Pull Request 생성

## 🛠️ API 엔드포인트

### 📊 데이터 관리
- `POST /api/data/upload` - CSV 파일 업로드 (✅ 새로 추가)
- `POST /api/data/upload-csv/` - CSV 파일 업로드 (기존)
- `GET /api/data/data-info/{file_name}` - 데이터 정보 조회
- `GET /api/data/correlation-matrix/{file_name}` - 상관관계 분석
- `POST /api/data/feature-importance/` - 특성 중요도 계산
- `POST /api/data/generate-report/` - PDF 보고서 생성
- `POST /api/data/send-email/` - 보고서 이메일 발송

### 🤖 머신러닝
- `GET /api/ml/models` - 저장된 모델 목록 조회 (✅ 새로 추가)
- `POST /api/ml/train-model/` - 모델 학습 시작
- `POST /api/ml/predict/` - 모델 예측 수행
- `DELETE /api/ml/models/{model_name}` - 모델 삭제 (✅ 새로 추가)

### 💬 RAG 챗봇
- `POST /api/chat/chat/` - AI 챗봇과 대화

### 🔐 인증 시스템
- `GET /auth/google/login` - Google 로그인
- `GET /auth/kakao/login` - Kakao 로그인  
- `GET /auth/naver/login` - Naver 로그인
- `POST /auth/logout` - 로그아웃
- `GET /auth/me` - 현재 사용자 정보
- `GET /auth/status` - 로그인 상태 확인

### ⚙️ 시스템
- `GET /` - API 상태 확인
- `GET /health` - 헬스 체크
- `GET /docs` - API 문서 (Swagger)

## 🐛 문제 해결

### 일반적인 문제들

**Q: 404 Not Found 에러 (라우트 문제)**
✅ **해결됨**: 최신 버전에서 모든 라우트가 정상 작동합니다
```bash
# API 상태 확인
curl http://localhost:8001/health
curl http://localhost:8001/docs  # API 문서 확인
```

**Q: Database import 오류**
✅ **해결됨**: 순환 import 문제가 해결되었습니다
- `from database import models` → `from database.models import Model` 형태로 수정 완료

**Q: Redis 연결 오류**
```bash
# Redis 설치 및 실행
# Windows: https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Ubuntu: sudo apt-get install redis-server
redis-server
```

**Q: 포트 충돌 오류**
```bash
# 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # macOS/Linux

# 프로세스 종료 후 재실행
```

**Q: 소셜 로그인 실패**
- OAuth 클라이언트 ID/Secret 확인
- 리디렉션 URI 정확히 설정했는지 확인
- 각 플랫폼의 개발자 콘솔에서 앱 상태 확인

**Q: 모델 학습 실패**
- Celery 워커가 실행 중인지 확인
- 업로드한 데이터에 null 값이 너무 많지 않은지 확인
- 타겟 변수와 특성 변수가 올바르게 선택되었는지 확인

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 👨‍💻 개발자 정보

프로젝트에 대한 문의사항이나 제안사항이 있으시면 언제든 연락해주세요!
niceqjawns@naver.com

---

⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!
#!/usr/bin/env python3
"""
개발 환경을 쉽게 시작할 수 있는 스크립트

이 스크립트는 Auto ML 플랫폼의 모든 필요한 서비스를 자동으로 시작합니다:
1. Redis 서버 확인/시작
2. 데이터베이스 초기화
3. FastAPI 서버 시작
4. 선택적으로 Celery 워커 시작

사용법:
  python start_dev.py              # API 서버만 시작
  python start_dev.py --celery     # API 서버 + Celery 워커
  python start_dev.py --all        # 모든 서비스 시작
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
import threading

def print_banner():
    """시작 배너 출력"""
    banner = """
    ╭─────────────────────────────────────────────────────╮
    │                                                     │
    │    🤖 Auto ML Platform - Development Server        │
    │                                                     │
    │    ✨ 머신러닝을 쉽게, 누구나 사용할 수 있게      │
    │                                                     │
    ╰─────────────────────────────────────────────────────╯
    """
    print(banner)

def check_redis():
    """Redis 서버 상태 확인"""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        print("✅ Redis 서버가 이미 실행 중입니다.")
        return True
    except ImportError:
        print("⚠️ redis-py 패키지가 설치되지 않았습니다.")
        print("   pip install redis 로 설치해주세요.")
        return False
    except Exception:
        print("❌ Redis 서버에 연결할 수 없습니다.")
        return False

def start_redis():
    """Redis 서버 시작 시도"""
    print("🔄 Redis 서버 시작을 시도합니다...")
    
    # 다양한 Redis 실행 방법 시도
    redis_commands = [
        "redis-server",
        "docker run -d -p 6379:6379 --name auto_ml_redis redis:alpine",
        "/usr/local/bin/redis-server",
        "/opt/homebrew/bin/redis-server"
    ]
    
    for cmd in redis_commands:
        try:
            if "docker" in cmd:
                print("🐳 Docker를 사용하여 Redis 시작을 시도합니다...")
                subprocess.run(cmd.split(), check=True, capture_output=True)
                time.sleep(3)  # Docker 컨테이너가 시작될 때까지 대기
            else:
                print(f"📡 {cmd} 명령으로 Redis 시작을 시도합니다...")
                subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2)
            
            # 연결 테스트
            if check_redis():
                return True
                
        except subprocess.CalledProcessError:
            continue
        except FileNotFoundError:
            continue
    
    return False

def check_dependencies():
    """필요한 의존성 확인"""
    print("🔍 의존성을 확인하는 중...")
    
    missing_deps = []
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'celery', 
        'pandas', 'scikit-learn', 'streamlit'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_deps.append(package)
    
    if missing_deps:
        print(f"⚠️ 누락된 패키지: {', '.join(missing_deps)}")
        print("   다음 명령으로 설치해주세요:")
        print(f"   pip install {' '.join(missing_deps)}")
        return False
    
    print("✅ 모든 의존성이 설치되어 있습니다.")
    return True

def setup_environment():
    """환경 설정"""
    print("🔧 환경을 설정하는 중...")
    
    # 환경변수 파일 확인
    env_files = ['.env.local', '.env.dev', '.env']
    env_found = False
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"✅ 환경변수 파일을 찾았습니다: {env_file}")
            env_found = True
            break
    
    if not env_found:
        print("⚠️ 환경변수 파일을 찾을 수 없습니다.")
        if os.path.exists('.env.example'):
            print("📋 .env.example을 .env.local로 복사합니다...")
            import shutil
            shutil.copy('.env.example', '.env.local')
            print("✅ .env.local 파일이 생성되었습니다.")
            print("🔐 소셜 로그인을 사용하려면 .env.local 파일에서 API 키를 설정해주세요.")
        else:
            print("❌ .env.example 파일도 찾을 수 없습니다.")
            return False
    
    # 필요한 디렉토리 생성
    directories = ['uploads', 'models', 'vectordb', 'logs']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 디렉토리 생성: {directory}")
    
    return True

def init_database():
    """데이터베이스 초기화"""
    print("🗄️ 데이터베이스를 초기화하는 중...")
    try:
        from database.database import init_db
        init_db()
        print("✅ 데이터베이스 초기화 완료")
        return True
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {e}")
        return False

def start_api_server():
    """FastAPI 서버 시작"""
    print("🚀 FastAPI 서버를 시작합니다...")
    print("📍 서버 주소: http://localhost:8001")
    print("📍 API 문서: http://localhost:8001/docs")
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 FastAPI 서버가 중단되었습니다.")

def start_celery_worker():
    """Celery 워커 시작"""
    print("⚙️ Celery 워커를 시작합니다...")
    
    def run_celery():
        try:
            subprocess.run([
                sys.executable, "-m", "celery",
                "-A", "tasks",
                "worker",
                "--loglevel=info",
                "--pool=solo"
            ])
        except KeyboardInterrupt:
            print("\n🛑 Celery 워커가 중단되었습니다.")
    
    # 별도 스레드에서 실행
    celery_thread = threading.Thread(target=run_celery, daemon=True)
    celery_thread.start()
    
    return celery_thread

def start_flower():
    """Flower 모니터링 시작"""
    print("🌸 Flower 모니터링을 시작합니다...")
    print("📍 Flower 주소: http://localhost:5555")
    
    def run_flower():
        try:
            subprocess.run([
                sys.executable, "-m", "celery",
                "-A", "tasks",
                "flower",
                "--port=5555"
            ])
        except KeyboardInterrupt:
            print("\n🛑 Flower가 중단되었습니다.")
    
    # 별도 스레드에서 실행
    flower_thread = threading.Thread(target=run_flower, daemon=True)
    flower_thread.start()
    
    return flower_thread

def print_instructions():
    """사용 방법 안내"""
    instructions = """
    🎯 다음 단계로 진행하세요:
    
    1. 새 터미널에서 Streamlit 프론트엔드 시작:
       cd ..
       streamlit run app.py
       
    2. 웹 브라우저에서 접속:
       🌐 http://localhost:8501 (Streamlit 프론트엔드)
       🔧 http://localhost:8001/docs (API 문서)
       🌸 http://localhost:5555 (Flower 모니터링)
    
    3. 소셜 로그인 사용하려면:
       📝 .env.local 파일에서 OAuth 클라이언트 설정
    
    💡 팁: Ctrl+C 로 서버를 중단할 수 있습니다.
    """
    print(instructions)

def main():
    parser = argparse.ArgumentParser(description="Auto ML 개발 서버 시작")
    parser.add_argument("--celery", action="store_true", help="Celery 워커도 함께 시작")
    parser.add_argument("--flower", action="store_true", help="Flower 모니터링도 함께 시작") 
    parser.add_argument("--all", action="store_true", help="모든 서비스 시작")
    parser.add_argument("--skip-redis", action="store_true", help="Redis 확인 건너뛰기")
    
    args = parser.parse_args()
    
    if args.all:
        args.celery = True
        args.flower = True
    
    print_banner()
    
    # 1. 의존성 확인
    if not check_dependencies():
        sys.exit(1)
    
    # 2. 환경 설정
    if not setup_environment():
        sys.exit(1)
    
    # 3. Redis 확인/시작 (Celery 사용하는 경우에만)
    if args.celery and not args.skip_redis:
        if not check_redis():
            print("🔄 Redis 서버를 시작하려고 합니다...")
            if not start_redis():
                print("❌ Redis 서버를 시작할 수 없습니다.")
                print("수동으로 Redis를 시작하거나 --skip-redis 옵션을 사용하세요.")
                sys.exit(1)
    
    # 4. 데이터베이스 초기화
    if not init_database():
        print("⚠️ 데이터베이스 초기화에 실패했지만 계속 진행합니다...")
    
    # 5. 서비스 시작
    threads = []
    
    if args.celery:
        celery_thread = start_celery_worker()
        threads.append(celery_thread)
        time.sleep(2)  # Celery 워커가 시작될 시간
    
    if args.flower:
        flower_thread = start_flower()
        threads.append(flower_thread)
        time.sleep(1)  # Flower가 시작될 시간
    
    # 6. 사용 방법 안내
    print_instructions()
    
    # 7. FastAPI 서버 시작 (메인 프로세스)
    try:
        start_api_server()
    except KeyboardInterrupt:
        print("\n🛑 모든 서비스를 종료하는 중...")
        # 스레드들이 daemon이므로 자동으로 종료됨

if __name__ == "__main__":
    main()
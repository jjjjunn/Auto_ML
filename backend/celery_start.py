"""
Celery 워커를 시작하기 위한 스크립트

로컬 개발 환경에서 Celery 워커를 쉽게 시작할 수 있도록 도와주는 스크립트입니다.
"""
import subprocess
import sys
import os
from pathlib import Path

def check_redis():
    """Redis 서버가 실행 중인지 확인"""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        client.ping()
        print("✅ Redis 서버 연결 성공")
        return True
    except Exception as e:
        print(f"❌ Redis 서버 연결 실패: {e}")
        print("Redis 서버를 시작해주세요:")
        print("  - Windows: Redis 설치 후 redis-server 실행")
        print("  - Docker: docker run -d -p 6379:6379 redis:alpine")
        return False

def start_celery_worker():
    """Celery 워커 시작"""
    if not check_redis():
        return False
    
    print("🚀 Celery 워커 시작 중...")
    try:
        # Windows에서는 --pool=solo 옵션 필요
        cmd = [
            sys.executable, "-m", "celery",
            "-A", "tasks",
            "worker",
            "--loglevel=info",
            "--pool=solo"  # Windows 호환성
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Celery 워커가 중단되었습니다.")
    except Exception as e:
        print(f"❌ Celery 워커 시작 실패: {e}")
        return False
    
    return True

def start_flower():
    """Celery 모니터링 도구 Flower 시작"""
    if not check_redis():
        return False
    
    print("🌸 Flower 모니터링 시작 중...")
    try:
        cmd = [
            sys.executable, "-m", "celery",
            "-A", "tasks",
            "flower",
            "--port=5555"
        ]
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Flower가 중단되었습니다.")
    except Exception as e:
        print(f"❌ Flower 시작 실패: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Celery 서비스 시작")
    parser.add_argument(
        'service', 
        choices=['worker', 'flower', 'check'],
        help='시작할 서비스 선택'
    )
    
    args = parser.parse_args()
    
    if args.service == 'worker':
        start_celery_worker()
    elif args.service == 'flower':
        start_flower()
    elif args.service == 'check':
        check_redis()
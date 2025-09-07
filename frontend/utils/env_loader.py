import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def load_environment_variables():
    """
    환경 변수를 로드합니다.
    프로젝트 루트에 있는 .env 파일을 로드하여 환경 변수를 설정합니다.
    """
    # Streamlit 앱이 실행되는 위치에 따라 .env 파일 경로를 조정해야 할 수 있습니다.
    # 일반적으로 Streamlit 앱은 프로젝트 루트에서 실행되므로, .env 파일도 루트에 있어야 합니다.
    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env')
    
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
        logger.info(f"✅ 환경 변수 로드 완료: {dotenv_path}")
    else:
        logger.warning(f"⚠️ .env 파일을 찾을 수 없습니다: {dotenv_path}. 환경 변수가 설정되지 않을 수 있습니다.")

# 앱 시작 시 자동으로 환경 변수를 로드하도록 호출
if __name__ == "__main__":
    load_environment_variables()

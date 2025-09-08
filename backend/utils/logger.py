import logging
from config import settings

def setup_logging():
    log_level = logging.INFO if settings.APP_ENV == "local" else logging.WARNING
    
    # UTF-8 인코딩으로 파일 핸들러 생성
    file_handler = logging.FileHandler("app.log", encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # 스트림 핸들러도 UTF-8로 설정
    import sys
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    
    # 포맷터 설정
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    
    # 로거 설정
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logging.getLogger(__name__)

logger = setup_logging()

from datetime import datetime, timedelta
from typing import Dict, Any
from jose import jwt, JWTError
from fastapi import HTTPException, status
from config import settings
from utils.logger import logger

def create_jwt_token(data: Dict[str, Any]) -> str:
    """
    주어진 데이터를 사용하여 JWT(JSON Web Token)를 생성합니다.
    사용자 인증 후 클라이언트에게 발급되어, 이후 요청 시 사용자 신원을 확인하는 데 사용됩니다.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.info(f"JWT token created for sub: {data.get('sub')}")
    return encoded_jwt

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    제공된 JWT를 검증하고 페이로드(사용자 정보)를 반환합니다.
    클라이언트로부터 받은 토큰의 유효성을 확인하고, 토큰에 포함된 사용자 정보를 추출합니다.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        logger.info(f"JWT token verified for sub: {payload.get('sub')}")
        return payload
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

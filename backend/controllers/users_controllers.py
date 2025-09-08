from sqlalchemy.orm import Session
from database.models import User
from models import schemas
from utils.logger import logger
from typing import Dict, Any
from fastapi import Request

def create_or_update_social_user(
    db: Session,
    user_info: Dict[str, Any],
    provider: str,
    request: Request,
    access_token: str
):
    """
    소셜 로그인 사용자를 데이터베이스에 생성하거나 업데이트합니다.
    사용자가 소셜 계정으로 로그인할 때, 해당 사용자 정보를 DB에 저장하거나 최신 정보로 갱신합니다.
    """
    logger.info(f"Attempting to create or update social user for provider: {provider}")
    
    # Check if user already exists based on provider_id
    if provider == "kakao":
        db_user = db.query(User).filter(User.kakao_id == user_info["provider_id"]).first()
    elif provider == "google":
        db_user = db.query(User).filter(User.google_id == user_info["provider_id"]).first()
    elif provider == "naver": # Add Naver
        db_user = db.query(User).filter(User.naver_id == user_info["provider_id"]).first()
    else:
        logger.error(f"Unsupported provider in create_or_update_social_user: {provider}")
        raise ValueError("Unsupported provider")

    if db_user:
        # Update existing user
        logger.info(f"Updating existing user: {db_user.email}")
        db_user.email = user_info.get("email", db_user.email)
        db_user.username = user_info.get("name", db_user.username)
        # Update provider-specific ID
        if provider == "kakao":
            db_user.kakao_id = user_info["provider_id"]
        elif provider == "google":
            db_user.google_id = user_info["provider_id"]
        elif provider == "naver": # Add Naver
            db_user.naver_id = user_info["provider_id"]
        
        # You might want to store the access_token or refresh_token if needed for future API calls
        # For now, we just log it
        logger.debug(f"Access token for {provider} user {user_info['provider_id']}: {access_token[:10]}...")
        
    else:
        # Create new user
        logger.info(f"Creating new user for provider: {provider}, email: {user_info.get('email')}")
        user_data = {
            "username": user_info.get("name", f"{provider}_user_{user_info['provider_id']}"),
            "email": user_info.get("email", f"{provider}_{user_info['provider_id']}@example.com"),
            "hashed_password": "social_login_user_no_password", # Social users don't have passwords
            "is_active": True
        }
        if provider == "kakao":
            user_data["kakao_id"] = user_info["provider_id"]
        elif provider == "google":
            user_data["google_id"] = user_info["provider_id"]
        elif provider == "naver": # Add Naver
            user_data["naver_id"] = user_info["provider_id"]

        db_user = User(**user_data)
        db.add(db_user)

    db.commit()
    db.refresh(db_user)
    logger.info(f"User {db_user.email} successfully created/updated in DB.")
    
    # Store minimal user info in session for immediate use (optional, depends on session middleware)
    # This part might need adjustment based on how session is handled in main.py
    if request:
        request.session['is_logged_in'] = True
        request.session['user_id'] = db_user.id
        request.session['name'] = db_user.username
        request.session['email'] = db_user.email
        request.session['provider'] = provider
        logger.info(f"User info stored in session for {db_user.email}")

    return db_user
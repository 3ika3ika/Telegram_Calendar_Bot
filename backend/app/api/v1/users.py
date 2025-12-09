"""User endpoints."""
import hashlib
import hmac
import logging
from urllib.parse import parse_qs, unquote
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_session
from app.models.user import User
from app.schemas.user import TelegramInitData, UserResponse, UserUpdate
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


def verify_telegram_webapp(init_data: str) -> Optional[dict]:
    """
    Verify Telegram WebApp initData signature.
    
    Args:
        init_data: Raw initData string from Telegram.WebApp.initData
        
    Returns:
        Parsed user data if valid, None otherwise
    """
    try:
        # Development mode: Allow mock data when DEBUG is True
        if settings.DEBUG and "dev_mode_hash" in init_data:
            logger.info("Development mode: Bypassing Telegram WebApp signature verification")
            parsed = parse_qs(init_data)
            user_str = parsed.get("user", [None])[0]
            if user_str:
                import json
                user_data = json.loads(unquote(user_str))
                return user_data
            return None
        
        # Parse init_data
        parsed = parse_qs(init_data)
        
        # Extract hash
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None
        
        # Remove hash from data
        data_check = []
        for key, value in parsed.items():
            if key != "hash":
                data_check.append(f"{key}={value[0]}")
        data_check_string = "\n".join(sorted(data_check))
        
        # Calculate secret key as per Telegram docs:
        # secret_key = HMAC_SHA256("WebAppData", bot_token)
        bot_token = settings.TELEGRAM_BOT_TOKEN
        if not bot_token:
            logger.error("TELEGRAM_BOT_TOKEN is not set; cannot verify WebApp signature")
            return None
        secret_key = hmac.new(
            "WebAppData".encode(),
            bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify
        if calculated_hash != received_hash:
            logger.warning("Telegram WebApp signature verification failed")
            return None
        
        # Extract user data
        user_str = parsed.get("user", [None])[0]
        if not user_str:
            return None
        
        # Parse user JSON (simplified - in production use proper JSON parsing)
        import json
        user_data = json.loads(unquote(user_str))
        
        return user_data
        
    except Exception as e:
        logger.error(f"Error verifying Telegram WebApp data: {e}")
        return None


@router.post("/session", response_model=UserResponse)
async def create_or_get_user(
    init_data: TelegramInitData,
    session: AsyncSession = Depends(get_session),
):
    """
    Verify Telegram WebApp initData and create/return user.
    
    This endpoint verifies the Telegram WebApp signature and creates
    or retrieves the user based on telegram_user_id.
    """
    # Allow development mode without secret
    if not settings.DEBUG and not settings.TELEGRAM_WEBAPP_SECRET:
        raise HTTPException(status_code=500, detail="Telegram WebApp secret not configured")
    
    user_data = verify_telegram_webapp(init_data.init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram WebApp signature")
    
    telegram_user_id = user_data.get("id")
    if not telegram_user_id:
        raise HTTPException(status_code=400, detail="Missing user ID in initData")
    
    # Check if user exists
    result = await session.execute(
        select(User).where(User.telegram_user_id == telegram_user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Update user info
        user.username = user_data.get("username")
        user.first_name = user_data.get("first_name")
        user.last_name = user_data.get("last_name")
        user.language_code = user_data.get("language_code")
        await session.commit()
        await session.refresh(user)
        return UserResponse.model_validate(user)
    
    # Create new user
    user = User(
        telegram_user_id=telegram_user_id,
        username=user_data.get("username"),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        language_code=user_data.get("language_code"),
        timezone=user_data.get("timezone", "UTC"),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    telegram_user_id: int = Header(..., alias="X-Telegram-User-Id"),
    session: AsyncSession = Depends(get_session),
):
    """Get current user by telegram_user_id from header."""
    result = await session.execute(
        select(User).where(User.telegram_user_id == telegram_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.put("/me", response_model=UserResponse)
async def update_user(
    user_update: UserUpdate,
    telegram_user_id: int = Header(..., alias="X-Telegram-User-Id"),
    session: AsyncSession = Depends(get_session),
):
    """Update current user settings."""
    result = await session.execute(
        select(User).where(User.telegram_user_id == telegram_user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_update.timezone:
        user.timezone = user_update.timezone
    if user_update.extra_metadata:
        user.extra_metadata.update(user_update.extra_metadata)
    
    await session.commit()
    await session.refresh(user)
    return UserResponse.model_validate(user)


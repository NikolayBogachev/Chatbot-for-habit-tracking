from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import aioredis
from fastapi import Depends, HTTPException
from fastapi.logger import logger
from fastapi.openapi.models import Response
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import ValidationError
from starlette import status

from config import config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class RedisBlacklist:
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis = aioredis.from_url(redis_url)

    async def add(self, token: str, expires_in: timedelta):
        """Добавляем токен в Redis с TTL"""
        await self.redis.setex(token, int(expires_in.total_seconds()), "revoked")

    async def is_blacklisted(self, token: str) -> bool:
        """Проверяем, есть ли токен в списке"""
        return await self.redis.exists(token)


# Инициализируем RedisBlacklist
redis_blacklist = RedisBlacklist(redis_url=config.REDIS_URL)

# Типы токенов
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


class AuthService:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    async def get_current_user(cls, token: str = Depends(oauth2_scheme)) -> int:
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            user_id_str: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id_str is None or token_type != TOKEN_TYPE_ACCESS:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type or missing user ID",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            if await redis_blacklist.is_blacklisted(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            try:
                user_id = int(user_id_str)
            except (TypeError, ValueError):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid user ID in token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return user_id
        except (JWTError, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @classmethod
    def create_access_token(cls, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = {"sub": str(user_id)}
        expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(minutes=15))
        to_encode.update({
            "exp": expire,
            "type": TOKEN_TYPE_ACCESS
        })
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt

    @classmethod
    def create_refresh_token(cls, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = {"sub": str(user_id)}
        expire = datetime.now(timezone.utc) + (expires_delta if expires_delta else timedelta(days=7))
        to_encode.update({
            "exp": expire,
            "type": TOKEN_TYPE_REFRESH
        })
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt

    @classmethod
    async def decode_token(cls, token: str) -> Optional[Dict]:
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            token_type = payload.get("type")

            if token_type not in [TOKEN_TYPE_ACCESS, TOKEN_TYPE_REFRESH]:
                logger.error("Unknown token type")
                return None

            if await redis_blacklist.is_blacklisted(token):
                logger.warning("Token is blacklisted")
                return None

            return payload
        except JWTError as e:
            logger.error(f"Token decoding failed: {str(e)}")
            return None

    @classmethod
    def set_refresh_cookie(cls, response: Response, refresh_token: str):
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60,  # 7 дней
            path="/api/auth/refresh"
        )

    @classmethod
    async def revoke_token(cls, token: str):
        """Добавляет токен в черный список"""
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM], options={"verify_exp": False})
            exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            ttl = (exp - datetime.now(timezone.utc)).total_seconds()
            if ttl > 0:
                await redis_blacklist.add(token, timedelta(seconds=ttl))
        except JWTError:
            pass


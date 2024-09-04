from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from database.models import UserInDB
from api.pydantic_models import User
from api.auth import get_password_hash, decode_access_token, verify_password


class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user(self, username: str) -> Optional[UserInDB]:
        query = select(UserInDB).filter(UserInDB.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_user(self, user: User) -> UserInDB:
        db_user = UserInDB(username=user.username, hashed_password=get_password_hash(user.password))

        async with self.db as session:
            try:
                session.add(db_user)
                await session.commit()
                await session.refresh(db_user)
            except IntegrityError:
                await session.rollback()
                raise HTTPException(status_code=400, detail="User already registered")

        return db_user

    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        user = await self.get_user(username)
        if user is None or not verify_password(password, user.hashed_password):
            return None
        return user

    async def get_current_user(self, token: str) -> UserInDB:
        payload = decode_access_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await self.get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

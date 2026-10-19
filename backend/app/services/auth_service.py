from typing import Optional
from fastapi import HTTPException, status
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.repositories.base import AbstractUserRepository
from app.schemas.auth import UserCreate, UserLogin, UserRead, Token

class AuthService:
    def __init__(self, user_repo: AbstractUserRepository):
        self.user_repo = user_repo

    async def signup(self, user_in: UserCreate) -> UserRead:
        existing = await self.user_repo.get_by_email(user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        hashed_pwd = hash_password(user_in.password)
        return await self.user_repo.create(user_in.email, hashed_pwd)

    async def authenticate(self, user_in: UserLogin) -> Token:
        user_record = await self.user_repo.get_by_email(user_in.email)
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not verify_password(user_in.password, user_record["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        token_str = create_access_token(user_record["id"])
        return Token(access_token=token_str, token_type="bearer")

    async def get_user_from_token(self, token: str) -> UserRead:
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await self.user_repo.get_by_id(payload["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        return user

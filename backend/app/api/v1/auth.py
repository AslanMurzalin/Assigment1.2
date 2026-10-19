from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_auth_service, get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate, UserLogin, UserRead, Token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    return await auth_service.signup(user_in)

@router.post("/login", response_model=Token)
async def login(
    user_in: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    return await auth_service.authenticate(user_in)

@router.get("/me", response_model=UserRead)
async def get_me(
    current_user: UserRead = Depends(get_current_user),
) -> UserRead:
    return current_user

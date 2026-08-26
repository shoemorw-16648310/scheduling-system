from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.auth import hash_password, verify_password, create_access_token, require_login, get_current_user
from app.config import get_settings

router = APIRouter()

settings = get_settings()


class UserRegister(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    role: str = "teacher"
    email: Optional[str] = None
    phone: Optional[str] = None


class UserInfo(BaseModel):
    id: int
    username: str
    real_name: Optional[str] = None
    role: str
    email: Optional[str] = None
    phone: Optional[str] = None
    teacher_id: Optional[int] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """登录获取token"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    # 更新最后登录时间
    user.last_login = datetime.now()
    db.commit()

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role},
    )
    return LoginResponse(access_token=access_token, user=user)


@router.get("/me", response_model=UserInfo)
def get_me(current_user: User = Depends(require_login)):
    """获取当前用户信息"""
    return current_user


@router.post("/register", response_model=UserInfo)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """注册用户
    - 第一个注册的用户自动成为管理员
    - 后续注册需要管理员权限
    """
    existing = db.query(User).first()
    if existing and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="需要管理员权限才能创建新用户")

    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    role = data.role
    if not existing:
        role = "admin"  # 第一个用户自动是管理员

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        real_name=data.real_name,
        role=role,
        email=data.email,
        phone=data.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password")
def change_password(
    old_password: str,
    new_password: str,
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db),
):
    """修改密码"""
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")
    current_user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": "密码修改成功"}

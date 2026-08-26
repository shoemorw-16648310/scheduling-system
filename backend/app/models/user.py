from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from app.database import Base


class User(Base):
    """系统用户"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希")
    real_name = Column(String(50), comment="真实姓名")
    role = Column(String(20), default="teacher", comment="角色：admin/teacher/student")
    email = Column(String(100), comment="邮箱")
    phone = Column(String(20), comment="电话")
    teacher_id = Column(Integer, comment="关联教师ID（教师账号）")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    last_login = Column(DateTime, comment="最后登录时间")

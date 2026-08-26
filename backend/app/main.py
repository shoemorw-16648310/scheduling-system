from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.models import *  # noqa: 确保所有模型被注册
from app.models.user import User
from app.auth import hash_password
from app.api import teachers, classrooms, courses, class_groups, teaching_tasks, schedule, import_export, semesters, time_slots, auth, departments

settings = get_settings()

# 创建所有数据表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

# CORS 配置
cors_list = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if "*" in cors_list:
    allow_origins = ["*"]
    allow_credentials = False
else:
    allow_origins = cors_list
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def init_default_user():
    """启动时确保有一个默认管理员账号（从环境变量读取）"""
    import os
    db = SessionLocal()
    try:
        existing = db.query(User).first()
        if not existing:
            default_username = os.environ.get("DEFAULT_ADMIN_USER", "admin")
            default_password = os.environ.get("DEFAULT_ADMIN_PASS", "admin123")
            user = User(
                username=default_username,
                password_hash=hash_password(default_password),
                real_name="管理员",
                role="admin",
                is_active=True,
            )
            db.add(user)
            db.commit()
            print(f"[init] 已创建默认管理员: {default_username}")
    except Exception as e:
        print(f"[init] 初始化默认用户失败: {e}")
    finally:
        db.close()


@app.get("/")
async def root():
    return {"message": "欢迎使用高校自动排课系统 API", "version": settings.app_version}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# 注册路由
app.include_router(semesters.router, prefix="/api/semesters", tags=["学期管理"])
app.include_router(time_slots.router, prefix="/api/time-slots", tags=["节次配置"])
app.include_router(departments.router, prefix="/api/departments", tags=["院系专业"])
app.include_router(teachers.router, prefix="/api/teachers", tags=["教师管理"])
app.include_router(classrooms.router, prefix="/api/classrooms", tags=["教室管理"])
app.include_router(class_groups.router, prefix="/api/class-groups", tags=["班级管理"])
app.include_router(courses.router, prefix="/api/courses", tags=["课程管理"])
app.include_router(teaching_tasks.router, prefix="/api/teaching-tasks", tags=["教学任务管理"])
app.include_router(schedule.router, prefix="/api/schedule", tags=["排课管理"])
app.include_router(import_export.router, prefix="/api", tags=["导入导出"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证授权"])

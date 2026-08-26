from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.common import Department


class TeacherUnavailableBase(BaseModel):
    day_of_week: int = Field(..., ge=1, le=7, description="星期几")
    section_start: int = Field(..., ge=1, description="开始节次")
    section_end: int = Field(..., ge=1, description="结束节次")
    week_pattern: str = "all"
    reason: Optional[str] = None


class TeacherUnavailableCreate(TeacherUnavailableBase):
    pass


class TeacherUnavailableUpdate(BaseModel):
    day_of_week: Optional[int] = None
    section_start: Optional[int] = None
    section_end: Optional[int] = None
    week_pattern: Optional[str] = None
    reason: Optional[str] = None


class TeacherUnavailable(TeacherUnavailableBase):
    id: int
    teacher_id: int

    class Config:
        from_attributes = True


class TeacherBase(BaseModel):
    teacher_no: str = Field(..., max_length=20, description="工号")
    name: str = Field(..., max_length=50, description="姓名")
    gender: Optional[str] = None
    title: Optional[str] = None
    department_id: Optional[int] = None
    max_hours_per_day: int = 6
    max_hours_per_week: int = 20
    max_consecutive_hours: int = 4
    need_noon_break: bool = True
    phone: Optional[str] = None
    email: Optional[str] = None
    status: int = 1


class TeacherCreate(TeacherBase):
    pass


class TeacherUpdate(BaseModel):
    teacher_no: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    title: Optional[str] = None
    department_id: Optional[int] = None
    max_hours_per_day: Optional[int] = None
    max_hours_per_week: Optional[int] = None
    max_consecutive_hours: Optional[int] = None
    need_noon_break: Optional[bool] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[int] = None


class Teacher(TeacherBase):
    id: int
    department: Optional[Department] = None
    unavailables: List[TeacherUnavailable] = []

    class Config:
        from_attributes = True


class TeacherSimple(BaseModel):
    id: int
    teacher_no: str
    name: str

    class Config:
        from_attributes = True

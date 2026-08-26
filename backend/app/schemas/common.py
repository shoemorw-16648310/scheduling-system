from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ---------- 院系 ----------
class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=50, description="院系名称")
    code: str = Field(..., max_length=20, description="院系编码")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None


class Department(DepartmentBase):
    id: int

    class Config:
        from_attributes = True


# ---------- 专业 ----------
class MajorBase(BaseModel):
    name: str = Field(..., max_length=50, description="专业名称")
    code: str = Field(..., max_length=20, description="专业编码")
    department_id: Optional[int] = None


class MajorCreate(MajorBase):
    pass


class MajorUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department_id: Optional[int] = None


class Major(MajorBase):
    id: int
    department: Optional[Department] = None

    class Config:
        from_attributes = True


# ---------- 学期 ----------
class SemesterBase(BaseModel):
    name: str = Field(..., max_length=50, description="学期名称")
    code: str = Field(..., max_length=20, description="学期编码")
    start_date: date
    end_date: date
    total_weeks: int = Field(default=16, ge=1, le=30)
    is_active: bool = False


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    total_weeks: Optional[int] = None
    is_active: Optional[bool] = None


class Semester(SemesterBase):
    id: int

    class Config:
        from_attributes = True


# ---------- 节次 ----------
class TimeSlotBase(BaseModel):
    section: int = Field(..., ge=1, description="第几节")
    name: Optional[str] = Field(None, max_length=20)
    start_time: str = Field(..., description="开始时间 HH:MM")
    end_time: str = Field(..., description="结束时间 HH:MM")
    period: Optional[str] = Field(None, description="morning/afternoon/evening")


class TimeSlotCreate(TimeSlotBase):
    pass


class TimeSlotUpdate(BaseModel):
    section: Optional[int] = None
    name: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    period: Optional[str] = None


class TimeSlot(TimeSlotBase):
    id: int

    class Config:
        from_attributes = True


# ---------- 通用分页 ----------
class PageQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    keyword: Optional[str] = None


class PageResult(BaseModel):
    total: int
    page: int
    page_size: int
    list: list

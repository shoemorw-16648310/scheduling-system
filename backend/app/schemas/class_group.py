from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.common import Department, Major


class ClassGroupBase(BaseModel):
    class_no: str = Field(..., max_length=20, description="班级编号")
    name: str = Field(..., max_length=50, description="班级名称")
    grade: str = Field(..., max_length=10, description="年级")
    major_id: Optional[int] = None
    department_id: Optional[int] = None
    student_count: int = 0
    campus: Optional[str] = None
    status: int = 1


class ClassGroupCreate(ClassGroupBase):
    pass


class ClassGroupUpdate(BaseModel):
    class_no: Optional[str] = None
    name: Optional[str] = None
    grade: Optional[str] = None
    major_id: Optional[int] = None
    department_id: Optional[int] = None
    student_count: Optional[int] = None
    campus: Optional[str] = None
    status: Optional[int] = None


class ClassGroup(ClassGroupBase):
    id: int
    major: Optional[Major] = None
    department: Optional[Department] = None

    class Config:
        from_attributes = True


class ClassGroupSimple(BaseModel):
    id: int
    class_no: str
    name: str
    grade: str
    campus: Optional[str] = None

    class Config:
        from_attributes = True

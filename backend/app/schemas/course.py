from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class CourseBase(BaseModel):
    course_code: str = Field(..., max_length=30, description="课程代码")
    name: str = Field(..., max_length=100, description="课程名称")
    credit: Decimal = Field(default=0, description="学分")
    total_hours: int = Field(default=0, ge=0, description="总学时")
    hours_per_week: int = Field(default=2, ge=1, description="周学时")
    course_type: str = "必修"
    subject_type: str = "主课"
    required_room_type: str = "normal"
    is_consecutive: bool = True
    consecutive_sections: int = 2
    department_id: Optional[int] = None
    description: Optional[str] = None


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    course_code: Optional[str] = None
    name: Optional[str] = None
    credit: Optional[Decimal] = None
    total_hours: Optional[int] = None
    hours_per_week: Optional[int] = None
    course_type: Optional[str] = None
    subject_type: Optional[str] = None
    required_room_type: Optional[str] = None
    is_consecutive: Optional[bool] = None
    consecutive_sections: Optional[int] = None
    department_id: Optional[int] = None
    description: Optional[str] = None


class Course(CourseBase):
    id: int

    class Config:
        from_attributes = True


class CourseSimple(BaseModel):
    id: int
    course_code: str
    name: str
    hours_per_week: int

    class Config:
        from_attributes = True

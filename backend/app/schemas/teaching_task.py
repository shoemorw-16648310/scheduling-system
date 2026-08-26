from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.teacher import TeacherSimple
from app.schemas.class_group import ClassGroupSimple
from app.schemas.course import CourseSimple


class TaskTeacherCreate(BaseModel):
    teacher_id: int
    is_main: bool = True


class TaskClassCreate(BaseModel):
    class_group_id: int


class TeachingTaskBase(BaseModel):
    task_code: Optional[str] = None
    course_id: int
    semester_id: int
    student_count: Optional[int] = None
    hours_per_week: Optional[int] = None
    weeks: str = "all"
    priority: int = 5
    notes: Optional[str] = None


class TeachingTaskCreate(TeachingTaskBase):
    teacher_ids: List[int] = []
    class_ids: List[int] = []


class TeachingTaskUpdate(BaseModel):
    task_code: Optional[str] = None
    course_id: Optional[int] = None
    semester_id: Optional[int] = None
    student_count: Optional[int] = None
    hours_per_week: Optional[int] = None
    weeks: Optional[str] = None
    priority: Optional[int] = None
    notes: Optional[str] = None
    teacher_ids: Optional[List[int]] = None
    class_ids: Optional[List[int]] = None
    status: Optional[int] = None


class TeachingTask(TeachingTaskBase):
    id: int
    status: int = 1
    course: Optional[CourseSimple] = None
    teachers: List[TeacherSimple] = []
    classes: List[ClassGroupSimple] = []

    class Config:
        from_attributes = True

from app.database import Base
from app.models.department import Department, Major
from app.models.semester import Semester
from app.models.timeslot import TimeSlot
from app.models.teacher import Teacher, TeacherUnavailable
from app.models.class_group import ClassGroup
from app.models.classroom import Classroom
from app.models.course import Course
from app.models.teaching_task import TeachingTask, TaskTeacher, TaskClass
from app.models.schedule import ScheduleBatch, ScheduleEntry
from app.models.user import User

__all__ = [
    "Base",
    "Department",
    "Major",
    "Semester",
    "TimeSlot",
    "Teacher",
    "TeacherUnavailable",
    "ClassGroup",
    "Classroom",
    "Course",
    "TeachingTask",
    "TaskTeacher",
    "TaskClass",
    "ScheduleBatch",
    "ScheduleEntry",
    "User",
]

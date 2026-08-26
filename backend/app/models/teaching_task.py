from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TeachingTask(Base):
    """教学任务（排课基本单元）"""
    __tablename__ = "teaching_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_code = Column(String(30), unique=True, comment="任务编码")
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="课程ID")
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, comment="学期ID")
    student_count = Column(Integer, comment="学生人数（合班时覆盖）")
    hours_per_week = Column(Integer, comment="周学时（覆盖课程默认值）")
    weeks = Column(String(500), default="all", comment="上课周次：all/单周/双周/JSON数组")
    priority = Column(Integer, default=5, comment="排课优先级 1-10")
    notes = Column(Text, comment="备注")
    status = Column(Integer, default=1, comment="状态")

    course = relationship("Course", back_populates="teaching_tasks")
    semester = relationship("Semester", back_populates="teaching_tasks")
    task_teachers = relationship("TaskTeacher", back_populates="task", cascade="all, delete-orphan")
    task_classes = relationship("TaskClass", back_populates="task", cascade="all, delete-orphan")
    schedule_entries = relationship("ScheduleEntry", back_populates="task")


class TaskTeacher(Base):
    """教学任务-教师关联"""
    __tablename__ = "task_teachers"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("teaching_tasks.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    is_main = Column(Boolean, default=True, comment="是否主讲教师")

    task = relationship("TeachingTask", back_populates="task_teachers")
    teacher = relationship("Teacher", back_populates="task_teachers")


class TaskClass(Base):
    """教学任务-班级关联"""
    __tablename__ = "task_classes"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("teaching_tasks.id"), nullable=False)
    class_group_id = Column(Integer, ForeignKey("class_groups.id"), nullable=False)

    task = relationship("TeachingTask", back_populates="task_classes")
    class_group = relationship("ClassGroup", back_populates="task_classes")

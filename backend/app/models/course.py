from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class Course(Base):
    """课程"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(30), unique=True, nullable=False, comment="课程代码")
    name = Column(String(100), nullable=False, comment="课程名称")
    credit = Column(Numeric(3, 1), nullable=False, default=0, comment="学分")
    total_hours = Column(Integer, nullable=False, default=0, comment="总学时")
    hours_per_week = Column(Integer, nullable=False, default=2, comment="周学时")
    course_type = Column(String(20), default="必修", comment="必修/选修/公选")
    subject_type = Column(String(20), default="主课", comment="主课/副课/实验/实践")
    required_room_type = Column(String(20), default="normal", comment="所需教室类型")
    is_consecutive = Column(Boolean, default=True, comment="是否需要连堂")
    consecutive_sections = Column(Integer, default=2, comment="连堂节数")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="开课院系ID")
    description = Column(Text, comment="简介")

    department = relationship("Department", back_populates="courses")
    teaching_tasks = relationship("TeachingTask", back_populates="course")

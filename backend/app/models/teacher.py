from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Teacher(Base):
    """教师"""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    teacher_no = Column(String(20), unique=True, nullable=False, comment="工号")
    name = Column(String(50), nullable=False, comment="姓名")
    gender = Column(String(10), comment="性别")
    title = Column(String(20), comment="职称")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="所属院系ID")
    max_hours_per_day = Column(Integer, default=6, comment="每日最大课时")
    max_hours_per_week = Column(Integer, default=20, comment="每周最大课时")
    max_consecutive_hours = Column(Integer, default=4, comment="最大连续课时")
    need_noon_break = Column(Boolean, default=True, comment="是否需要午休")
    phone = Column(String(20), comment="电话")
    email = Column(String(50), comment="邮箱")
    status = Column(Integer, default=1, comment="状态：1在职/0离职")

    department = relationship("Department", back_populates="teachers")
    unavailables = relationship("TeacherUnavailable", back_populates="teacher", cascade="all, delete-orphan")
    task_teachers = relationship("TaskTeacher", back_populates="teacher")


class TeacherUnavailable(Base):
    """教师不可用时间"""
    __tablename__ = "teacher_unavailables"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, comment="教师ID")
    day_of_week = Column(Integer, nullable=False, comment="星期几：1-7")
    section_start = Column(Integer, nullable=False, comment="开始节次")
    section_end = Column(Integer, nullable=False, comment="结束节次")
    week_pattern = Column(String(200), default="all", comment="适用周次：all/单周/双周/自定义JSON")
    reason = Column(String(200), comment="原因")

    teacher = relationship("Teacher", back_populates="unavailables")

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ClassGroup(Base):
    """班级"""
    __tablename__ = "class_groups"

    id = Column(Integer, primary_key=True, index=True)
    class_no = Column(String(20), unique=True, nullable=False, comment="班级编号")
    name = Column(String(50), nullable=False, comment="班级名称")
    grade = Column(String(10), nullable=False, comment="年级")
    major_id = Column(Integer, ForeignKey("majors.id"), comment="所属专业ID")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="所属院系ID")
    student_count = Column(Integer, default=0, comment="学生人数")
    campus = Column(String(20), comment="校区")
    status = Column(Integer, default=1, comment="状态")

    major = relationship("Major", back_populates="class_groups")
    department = relationship("Department", back_populates="class_groups")
    task_classes = relationship("TaskClass", back_populates="class_group")

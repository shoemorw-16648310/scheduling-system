from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Department(Base):
    """院系"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="院系名称")
    code = Column(String(20), unique=True, nullable=False, comment="院系编码")

    majors = relationship("Major", back_populates="department")
    teachers = relationship("Teacher", back_populates="department")
    class_groups = relationship("ClassGroup", back_populates="department")
    courses = relationship("Course", back_populates="department")


class Major(Base):
    """专业"""
    __tablename__ = "majors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="专业名称")
    code = Column(String(20), unique=True, nullable=False, comment="专业编码")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="所属院系ID")

    department = relationship("Department", back_populates="majors")
    class_groups = relationship("ClassGroup", back_populates="major")

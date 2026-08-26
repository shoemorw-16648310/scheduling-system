from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Semester(Base):
    """学期"""
    __tablename__ = "semesters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, comment="学期名称")
    code = Column(String(20), unique=True, nullable=False, comment="学期编码")
    start_date = Column(Date, nullable=False, comment="开学日期")
    end_date = Column(Date, nullable=False, comment="结束日期")
    total_weeks = Column(Integer, nullable=False, default=16, comment="总周数")
    is_active = Column(Boolean, default=False, comment="是否当前学期")

    teaching_tasks = relationship("TeachingTask", back_populates="semester")
    schedule_entries = relationship("ScheduleEntry", back_populates="semester")
    schedule_batches = relationship("ScheduleBatch", back_populates="semester")

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class ScheduleBatch(Base):
    """排课批次"""
    __tablename__ = "schedule_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_code = Column(String(30), unique=True, nullable=False, comment="批次号")
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, comment="学期ID")
    status = Column(String(20), default="pending", comment="pending/running/completed/failed")
    score = Column(Integer, comment="排课评分")
    score_detail_json = Column(Text, comment="评分明细JSON（各维度惩罚分）")
    is_current = Column(Integer, default=0, comment="是否当前使用批次：0否/1是")
    config_json = Column(Text, comment="排课参数配置JSON")
    result_summary = Column(Text, comment="结果摘要JSON")
    message = Column(Text, comment="错误信息或备注")
    started_at = Column(DateTime, comment="开始时间")
    finished_at = Column(DateTime, comment="完成时间")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    semester = relationship("Semester", back_populates="schedule_batches")
    entries = relationship("ScheduleEntry", back_populates="batch")


class ScheduleEntry(Base):
    """排课结果"""
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("teaching_tasks.id"), nullable=False, comment="教学任务ID")
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), comment="教室ID")
    day_of_week = Column(Integer, nullable=False, comment="星期几：1-7")
    section_start = Column(Integer, nullable=False, comment="开始节次")
    section_end = Column(Integer, nullable=False, comment="结束节次")
    weeks = Column(String(500), default="all", comment="上课周次JSON")
    semester_id = Column(Integer, ForeignKey("semesters.id"), nullable=False, comment="学期ID")
    schedule_batch = Column(String(30), comment="排课批次号")
    batch_id = Column(Integer, ForeignKey("schedule_batches.id"), comment="排课批次ID")
    is_manual = Column(Integer, default=0, comment="是否手动调整：0自动/1手动")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    task = relationship("TeachingTask", back_populates="schedule_entries")
    classroom = relationship("Classroom")
    semester = relationship("Semester", back_populates="schedule_entries")
    batch = relationship("ScheduleBatch", back_populates="entries")

from sqlalchemy import Column, Integer, String

from app.database import Base


class TimeSlot(Base):
    """节次配置"""
    __tablename__ = "time_slots"

    id = Column(Integer, primary_key=True, index=True)
    section = Column(Integer, unique=True, nullable=False, comment="第几节")
    name = Column(String(20), comment="节次名称")
    start_time = Column(String(10), nullable=False, comment="开始时间 HH:MM")
    end_time = Column(String(10), nullable=False, comment="结束时间 HH:MM")
    period = Column(String(10), comment="时段：morning/afternoon/evening")

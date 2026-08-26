from sqlalchemy import Column, Integer, String, Boolean, Text

from app.database import Base


class Classroom(Base):
    """教室"""
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, index=True)
    room_no = Column(String(30), unique=True, nullable=False, comment="教室编号")
    building = Column(String(30), nullable=False, comment="教学楼")
    room_number = Column(String(20), nullable=False, comment="房间号")
    capacity = Column(Integer, nullable=False, default=0, comment="容纳人数")
    classroom_type = Column(String(20), nullable=False, default="normal",
                            comment="类型：normal/multimedia/lab/computer/arts")
    equipment = Column(Text, comment="设备清单JSON")
    campus = Column(String(20), comment="校区")
    status = Column(Integer, default=1, comment="状态：1可用/0维修中")

from pydantic import BaseModel, Field
from typing import Optional


class ClassroomBase(BaseModel):
    room_no: str = Field(..., max_length=30, description="教室编号")
    building: str = Field(..., max_length=30, description="教学楼")
    room_number: str = Field(..., max_length=20, description="房间号")
    capacity: int = Field(default=0, ge=0, description="容纳人数")
    classroom_type: str = Field(default="normal", description="normal/multimedia/lab/computer/arts")
    equipment: Optional[str] = None
    campus: Optional[str] = None
    status: int = 1


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    room_no: Optional[str] = None
    building: Optional[str] = None
    room_number: Optional[str] = None
    capacity: Optional[int] = None
    classroom_type: Optional[str] = None
    equipment: Optional[str] = None
    campus: Optional[str] = None
    status: Optional[int] = None


class Classroom(ClassroomBase):
    id: int

    class Config:
        from_attributes = True


class ClassroomSimple(BaseModel):
    id: int
    room_no: str
    building: str
    room_number: str
    capacity: int
    classroom_type: str

    class Config:
        from_attributes = True

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ScheduleGenerateRequest(BaseModel):
    semester_id: int
    time_limit_seconds: int = Field(default=120, ge=10, le=600)
    days_per_week: int = Field(default=5, ge=5, le=7)
    strict_room_type: bool = True
    constraint_weights: Dict[str, Any] = Field(default_factory=lambda: {
        "teacher_daily_hours": 50,
        "teacher_consecutive": 30,
        "uniform_distribution": 40,
        "main_course_morning": 60,
        "noon_break": 25,
        "class_daily_hours": 20,
        "room_balance": 15,
    })


class ScheduleBatchBase(BaseModel):
    batch_code: str
    semester_id: int
    status: str = "pending"
    score: Optional[int] = None
    is_current: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    message: Optional[str] = None


class ScheduleBatch(ScheduleBatchBase):
    id: int
    config_json: Optional[str] = None
    result_summary: Optional[str] = None
    score_detail: Optional[Dict[str, int]] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleEntryBase(BaseModel):
    task_id: int
    classroom_id: Optional[int] = None
    day_of_week: int
    section_start: int
    section_end: int
    weeks: str = "all"


class ScheduleEntryCreate(ScheduleEntryBase):
    semester_id: int
    schedule_batch: Optional[str] = None
    is_manual: int = 0


class ScheduleEntryUpdate(BaseModel):
    classroom_id: Optional[int] = None
    day_of_week: Optional[int] = None
    section_start: Optional[int] = None
    section_end: Optional[int] = None
    weeks: Optional[str] = None


class ScheduleEntry(ScheduleEntryBase):
    id: int
    semester_id: int
    schedule_batch: Optional[str] = None
    is_manual: int = 0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleEntryDetail(ScheduleEntry):
    course_name: Optional[str] = None
    teacher_names: Optional[str] = None
    class_names: Optional[str] = None
    classroom_name: Optional[str] = None


# ==================== 评分对比相关 ====================

class ScoreDimension(BaseModel):
    """评分维度元信息"""
    key: str
    label: str
    weight: int
    description: str


class BatchScoreDetail(BaseModel):
    """批次评分明细"""
    batch_id: int
    batch_code: str
    total_score: int
    dimensions: Dict[str, int]
    solve_time: Optional[float] = None
    scheduled_tasks: Optional[int] = None
    total_tasks: Optional[int] = None
    is_current: int = 0
    created_at: Optional[datetime] = None


class ScheduleCompareResponse(BaseModel):
    """排课对比响应"""
    dimensions: list
    batches: list
    best_batch_code: Optional[str] = None

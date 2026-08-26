from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.timeslot import TimeSlot
from app.schemas.common import TimeSlotCreate, TimeSlotUpdate, TimeSlot as TimeSlotSchema

router = APIRouter()


@router.get("", response_model=List[TimeSlotSchema])
def list_time_slots(db: Session = Depends(get_db)):
    return db.query(TimeSlot).order_by(TimeSlot.section).all()


@router.get("/{slot_id}", response_model=TimeSlotSchema)
def get_time_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).get(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="节次不存在")
    return slot


@router.post("", response_model=TimeSlotSchema)
def create_time_slot(data: TimeSlotCreate, db: Session = Depends(get_db)):
    existing = db.query(TimeSlot).filter(TimeSlot.section == data.section).first()
    if existing:
        raise HTTPException(status_code=400, detail="该节次号已存在")
    if data.start_time >= data.end_time:
        raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")
    slot = TimeSlot(**data.model_dump())
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


@router.put("/{slot_id}", response_model=TimeSlotSchema)
def update_time_slot(slot_id: int, data: TimeSlotUpdate, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).get(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="节次不存在")
    update_data = data.model_dump(exclude_unset=True)
    # 如果修改了 section，检查是否与其他节次冲突
    if "section" in update_data and update_data["section"] != slot.section:
        existing = db.query(TimeSlot).filter(TimeSlot.section == update_data["section"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="该节次号已存在")
    # 校验时间
    if "start_time" in update_data or "end_time" in update_data:
        start = update_data.get("start_time", slot.start_time)
        end = update_data.get("end_time", slot.end_time)
        if start >= end:
            raise HTTPException(status_code=400, detail="结束时间必须晚于开始时间")
    for key, value in update_data.items():
        setattr(slot, key, value)
    db.commit()
    db.refresh(slot)
    return slot


@router.delete("/{slot_id}")
def delete_time_slot(slot_id: int, db: Session = Depends(get_db)):
    slot = db.query(TimeSlot).get(slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="节次不存在")
    db.delete(slot)
    db.commit()
    return {"message": "删除成功"}


@router.post("/batch")
def batch_create_time_slots(data: List[TimeSlotCreate], db: Session = Depends(get_db)):
    """批量创建节次（用于初始化）"""
    db.query(TimeSlot).delete()
    for item in data:
        slot = TimeSlot(**item.model_dump())
        db.add(slot)
    db.commit()
    return {"message": "批量创建成功", "count": len(data)}

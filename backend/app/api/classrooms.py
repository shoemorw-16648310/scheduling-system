from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from app.database import get_db
from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate, Classroom as ClassroomSchema, ClassroomSimple

router = APIRouter()


@router.get("")
def list_classrooms(
    keyword: str = Query(None, description="搜索关键词"),
    classroom_type: str = Query(None, description="教室类型"),
    building: str = Query(None, description="教学楼"),
    campus: str = Query(None, description="校区"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Classroom).filter(Classroom.status == 1)
    if keyword:
        query = query.filter(or_(Classroom.room_no.contains(keyword), Classroom.building.contains(keyword)))
    if classroom_type:
        query = query.filter(Classroom.classroom_type == classroom_type)
    if building:
        query = query.filter(Classroom.building == building)
    if campus:
        query = query.filter(Classroom.campus == campus)
    total = query.count()
    items = query.order_by(Classroom.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "list": items, "page": page, "page_size": page_size}


@router.get("/all", response_model=List[ClassroomSimple])
def list_all_classrooms(db: Session = Depends(get_db)):
    return db.query(Classroom).filter(Classroom.status == 1).order_by(Classroom.room_no).all()


@router.get("/{classroom_id}", response_model=ClassroomSchema)
def get_classroom(classroom_id: int, db: Session = Depends(get_db)):
    classroom = db.query(Classroom).get(classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    return classroom


@router.post("", response_model=ClassroomSchema)
def create_classroom(data: ClassroomCreate, db: Session = Depends(get_db)):
    existing = db.query(Classroom).filter(Classroom.room_no == data.room_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="教室编号已存在")
    classroom = Classroom(**data.model_dump())
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.put("/{classroom_id}", response_model=ClassroomSchema)
def update_classroom(classroom_id: int, data: ClassroomUpdate, db: Session = Depends(get_db)):
    classroom = db.query(Classroom).get(classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(classroom, key, value)
    db.commit()
    db.refresh(classroom)
    return classroom


@router.delete("/{classroom_id}")
def delete_classroom(classroom_id: int, db: Session = Depends(get_db)):
    classroom = db.query(Classroom).get(classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="教室不存在")
    classroom.status = 0
    db.commit()
    return {"message": "删除成功"}

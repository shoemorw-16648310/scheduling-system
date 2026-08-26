from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from app.database import get_db
from app.models.teacher import Teacher, TeacherUnavailable
from app.schemas.teacher import (
    TeacherCreate, TeacherUpdate, Teacher as TeacherSchema, TeacherSimple,
    TeacherUnavailableCreate, TeacherUnavailableUpdate, TeacherUnavailable as TeacherUnavailableSchema,
)

router = APIRouter()


@router.get("")
def list_teachers(
    keyword: str = Query(None, description="搜索关键词"),
    department_id: int = Query(None, description="院系ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Teacher).filter(Teacher.status == 1)
    if keyword:
        query = query.filter(or_(Teacher.name.contains(keyword), Teacher.teacher_no.contains(keyword)))
    if department_id:
        query = query.filter(Teacher.department_id == department_id)
    total = query.count()
    items = query.order_by(Teacher.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "list": items, "page": page, "page_size": page_size}


@router.get("/all", response_model=List[TeacherSimple])
def list_all_teachers(db: Session = Depends(get_db)):
    """获取所有教师（下拉选择用）"""
    return db.query(Teacher).filter(Teacher.status == 1).order_by(Teacher.name).all()


@router.get("/{teacher_id}", response_model=TeacherSchema)
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    return teacher


@router.post("", response_model=TeacherSchema)
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db)):
    existing = db.query(Teacher).filter(Teacher.teacher_no == data.teacher_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="工号已存在")
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.put("/{teacher_id}", response_model=TeacherSchema)
def update_teacher(teacher_id: int, data: TeacherUpdate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(teacher, key, value)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    teacher.status = 0
    db.commit()
    return {"message": "删除成功"}


# ---------- 教师不可用时间 ----------
@router.get("/{teacher_id}/unavailables", response_model=List[TeacherUnavailableSchema])
def list_teacher_unavailables(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    return teacher.unavailables


@router.post("/{teacher_id}/unavailables", response_model=TeacherUnavailableSchema)
def create_teacher_unavailable(teacher_id: int, data: TeacherUnavailableCreate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).get(teacher_id)
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    unavail = TeacherUnavailable(teacher_id=teacher_id, **data.model_dump())
    db.add(unavail)
    db.commit()
    db.refresh(unavail)
    return unavail


@router.put("/unavailables/{unavail_id}", response_model=TeacherUnavailableSchema)
def update_teacher_unavailable(unavail_id: int, data: TeacherUnavailableUpdate, db: Session = Depends(get_db)):
    unavail = db.query(TeacherUnavailable).get(unavail_id)
    if not unavail:
        raise HTTPException(status_code=404, detail="记录不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(unavail, key, value)
    db.commit()
    db.refresh(unavail)
    return unavail


@router.delete("/unavailables/{unavail_id}")
def delete_teacher_unavailable(unavail_id: int, db: Session = Depends(get_db)):
    unavail = db.query(TeacherUnavailable).get(unavail_id)
    if not unavail:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(unavail)
    db.commit()
    return {"message": "删除成功"}

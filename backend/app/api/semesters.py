from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from app.database import get_db
from app.models.semester import Semester
from app.schemas.common import SemesterCreate, SemesterUpdate, Semester as SemesterSchema

router = APIRouter()


@router.get("", response_model=List[SemesterSchema])
def list_semesters(
    keyword: str = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db),
):
    query = db.query(Semester)
    if keyword:
        query = query.filter(or_(Semester.name.contains(keyword), Semester.code.contains(keyword)))
    return query.order_by(Semester.id.desc()).all()


@router.get("/{semester_id}", response_model=SemesterSchema)
def get_semester(semester_id: int, db: Session = Depends(get_db)):
    semester = db.query(Semester).get(semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    return semester


@router.post("", response_model=SemesterSchema)
def create_semester(data: SemesterCreate, db: Session = Depends(get_db)):
    # 检查编码是否存在
    existing = db.query(Semester).filter(Semester.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="学期编码已存在")
    # 日期校验
    if data.end_date <= data.start_date:
        raise HTTPException(status_code=400, detail="结束日期必须晚于开学日期")
    # 如果设为当前学期，取消其他学期的激活状态
    if data.is_active:
        db.query(Semester).filter(Semester.is_active == True).update({"is_active": False})
    semester = Semester(**data.model_dump())
    db.add(semester)
    db.commit()
    db.refresh(semester)
    return semester


@router.put("/{semester_id}", response_model=SemesterSchema)
def update_semester(semester_id: int, data: SemesterUpdate, db: Session = Depends(get_db)):
    semester = db.query(Semester).get(semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    update_data = data.model_dump(exclude_unset=True)
    # 编码唯一性校验
    if "code" in update_data and update_data["code"] != semester.code:
        existing = db.query(Semester).filter(Semester.code == update_data["code"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="学期编码已存在")
    # 日期校验
    start = update_data.get("start_date", semester.start_date)
    end = update_data.get("end_date", semester.end_date)
    if start and end and end <= start:
        raise HTTPException(status_code=400, detail="结束日期必须晚于开学日期")
    # 如果设为当前学期，取消其他学期的激活状态
    if update_data.get("is_active"):
        db.query(Semester).filter(Semester.is_active == True).filter(Semester.id != semester_id).update({"is_active": False})
    for key, value in update_data.items():
        setattr(semester, key, value)
    db.commit()
    db.refresh(semester)
    return semester


@router.delete("/{semester_id}")
def delete_semester(semester_id: int, db: Session = Depends(get_db)):
    semester = db.query(Semester).get(semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="学期不存在")
    db.delete(semester)
    db.commit()
    return {"message": "删除成功"}

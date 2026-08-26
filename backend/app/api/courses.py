from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from app.database import get_db
from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate, Course as CourseSchema, CourseSimple

router = APIRouter()


@router.get("")
def list_courses(
    keyword: str = Query(None, description="搜索关键词"),
    course_type: str = Query(None, description="课程类型"),
    department_id: int = Query(None, description="院系ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Course)
    if keyword:
        query = query.filter(or_(Course.name.contains(keyword), Course.course_code.contains(keyword)))
    if course_type:
        query = query.filter(Course.course_type == course_type)
    if department_id:
        query = query.filter(Course.department_id == department_id)
    total = query.count()
    items = query.order_by(Course.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "list": items, "page": page, "page_size": page_size}


@router.get("/all", response_model=List[CourseSimple])
def list_all_courses(db: Session = Depends(get_db)):
    return db.query(Course).order_by(Course.course_code).all()


@router.get("/{course_id}", response_model=CourseSchema)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


@router.post("", response_model=CourseSchema)
def create_course(data: CourseCreate, db: Session = Depends(get_db)):
    existing = db.query(Course).filter(Course.course_code == data.course_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="课程代码已存在")
    course = Course(**data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseSchema)
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    db.delete(course)
    db.commit()
    return {"message": "删除成功"}

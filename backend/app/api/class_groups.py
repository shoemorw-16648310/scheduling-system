from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from app.database import get_db
from app.models.class_group import ClassGroup
from app.schemas.class_group import ClassGroupCreate, ClassGroupUpdate, ClassGroup as ClassGroupSchema, ClassGroupSimple

router = APIRouter()


@router.get("")
def list_class_groups(
    keyword: str = Query(None, description="搜索关键词"),
    grade: str = Query(None, description="年级"),
    department_id: int = Query(None, description="院系ID"),
    campus: str = Query(None, description="校区"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(ClassGroup).filter(ClassGroup.status == 1)
    if keyword:
        query = query.filter(or_(ClassGroup.name.contains(keyword), ClassGroup.class_no.contains(keyword)))
    if grade:
        query = query.filter(ClassGroup.grade == grade)
    if department_id:
        query = query.filter(ClassGroup.department_id == department_id)
    if campus:
        query = query.filter(ClassGroup.campus == campus)
    total = query.count()
    items = query.order_by(ClassGroup.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "list": items, "page": page, "page_size": page_size}


@router.get("/all", response_model=List[ClassGroupSimple])
def list_all_class_groups(db: Session = Depends(get_db)):
    return db.query(ClassGroup).filter(ClassGroup.status == 1).order_by(ClassGroup.class_no).all()


@router.get("/{group_id}", response_model=ClassGroupSchema)
def get_class_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(ClassGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="班级不存在")
    return group


@router.post("", response_model=ClassGroupSchema)
def create_class_group(data: ClassGroupCreate, db: Session = Depends(get_db)):
    existing = db.query(ClassGroup).filter(ClassGroup.class_no == data.class_no).first()
    if existing:
        raise HTTPException(status_code=400, detail="班级编号已存在")
    group = ClassGroup(**data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@router.put("/{group_id}", response_model=ClassGroupSchema)
def update_class_group(group_id: int, data: ClassGroupUpdate, db: Session = Depends(get_db)):
    group = db.query(ClassGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="班级不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    return group


@router.delete("/{group_id}")
def delete_class_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(ClassGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="班级不存在")
    group.status = 0
    db.commit()
    return {"message": "删除成功"}

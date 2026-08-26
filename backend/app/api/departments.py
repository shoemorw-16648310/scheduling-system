from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from app.database import get_db
from app.models.department import Department, Major
from app.schemas.department import (
    DepartmentCreate, DepartmentUpdate, Department as DepartmentSchema,
    DepartmentSimple, DepartmentWithMajors,
    MajorCreate, MajorUpdate, Major as MajorSchema, MajorSimple,
)

router = APIRouter()


# ────────── 院系 ──────────
@router.get("")
def list_departments(
    keyword: str = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Department)
    if keyword:
        query = query.filter(or_(Department.name.contains(keyword), Department.code.contains(keyword)))
    total = query.count()
    items = query.order_by(Department.id.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "list": items, "page": page, "page_size": page_size}


@router.get("/all", response_model=List[DepartmentSimple])
def list_all_departments(db: Session = Depends(get_db)):
    """获取所有院系（下拉选择用）"""
    return db.query(Department).order_by(Department.name).all()


@router.get("/{dept_id}", response_model=DepartmentWithMajors)
def get_department(dept_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).get(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="院系不存在")
    return dept


@router.post("", response_model=DepartmentSchema)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db)):
    if db.query(Department).filter(Department.code == data.code).first():
        raise HTTPException(status_code=400, detail="院系编码已存在")
    dept = Department(**data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept


@router.put("/{dept_id}", response_model=DepartmentSchema)
def update_department(dept_id: int, data: DepartmentUpdate, db: Session = Depends(get_db)):
    dept = db.query(Department).get(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="院系不存在")
    if data.code and data.code != dept.code:
        if db.query(Department).filter(Department.code == data.code, Department.id != dept_id).first():
            raise HTTPException(status_code=400, detail="院系编码已存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dept, key, value)
    db.commit()
    db.refresh(dept)
    return dept


@router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).get(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="院系不存在")
    # 检查是否有关联数据
    if dept.teachers:
        raise HTTPException(status_code=400, detail=f"该院系下还有 {len(dept.teachers)} 名教师，无法删除")
    if dept.courses:
        raise HTTPException(status_code=400, detail=f"该院系下还有 {len(dept.courses)} 门课程，无法删除")
    if dept.class_groups:
        raise HTTPException(status_code=400, detail=f"该院系下还有 {len(dept.class_groups)} 个班级，无法删除")
    db.delete(dept)
    db.commit()
    return {"message": "删除成功"}


# ────────── 专业 ──────────
@router.get("/{dept_id}/majors", response_model=List[MajorSimple])
def list_department_majors(dept_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).get(dept_id)
    if not dept:
        raise HTTPException(status_code=404, detail="院系不存在")
    return db.query(Major).filter(Major.department_id == dept_id).order_by(Major.name).all()


@router.get("/majors/all", response_model=List[MajorSimple])
def list_all_majors(db: Session = Depends(get_db)):
    """获取所有专业（下拉选择用）"""
    return db.query(Major).order_by(Major.name).all()


@router.post("/majors", response_model=MajorSchema)
def create_major(data: MajorCreate, db: Session = Depends(get_db)):
    if db.query(Major).filter(Major.code == data.code).first():
        raise HTTPException(status_code=400, detail="专业编码已存在")
    dept = db.query(Department).get(data.department_id)
    if not dept:
        raise HTTPException(status_code=400, detail="所属院系不存在")
    major = Major(**data.model_dump())
    db.add(major)
    db.commit()
    db.refresh(major)
    return major


@router.put("/majors/{major_id}", response_model=MajorSchema)
def update_major(major_id: int, data: MajorUpdate, db: Session = Depends(get_db)):
    major = db.query(Major).get(major_id)
    if not major:
        raise HTTPException(status_code=404, detail="专业不存在")
    if data.code and data.code != major.code:
        if db.query(Major).filter(Major.code == data.code, Major.id != major_id).first():
            raise HTTPException(status_code=400, detail="专业编码已存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(major, key, value)
    db.commit()
    db.refresh(major)
    return major


@router.delete("/majors/{major_id}")
def delete_major(major_id: int, db: Session = Depends(get_db)):
    major = db.query(Major).get(major_id)
    if not major:
        raise HTTPException(status_code=404, detail="专业不存在")
    if major.class_groups:
        raise HTTPException(status_code=400, detail=f"该专业下还有 {len(major.class_groups)} 个班级，无法删除")
    db.delete(major)
    db.commit()
    return {"message": "删除成功"}

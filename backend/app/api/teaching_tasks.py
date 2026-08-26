from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

from app.database import get_db
from app.models.teaching_task import TeachingTask, TaskTeacher, TaskClass
from app.models.course import Course
from app.schemas.teaching_task import (
    TeachingTaskCreate, TeachingTaskUpdate, TeachingTask as TeachingTaskSchema,
)

router = APIRouter()


def _task_to_dict(task: TeachingTask) -> dict:
    """将教学任务转为包含关联数据的字典"""
    return {
        "id": task.id,
        "task_code": task.task_code,
        "course_id": task.course_id,
        "semester_id": task.semester_id,
        "student_count": task.student_count,
        "hours_per_week": task.hours_per_week,
        "weeks": task.weeks,
        "priority": task.priority,
        "notes": task.notes,
        "status": task.status,
        "course": {
            "id": task.course.id,
            "course_code": task.course.course_code,
            "name": task.course.name,
            "hours_per_week": task.course.hours_per_week,
        } if task.course else None,
        "teachers": [
            {"id": tt.teacher.id, "teacher_no": tt.teacher.teacher_no, "name": tt.teacher.name}
            for tt in task.task_teachers
        ],
        "classes": [
            {"id": tc.class_group.id, "class_no": tc.class_group.class_no,
             "name": tc.class_group.name, "grade": tc.class_group.grade}
            for tc in task.task_classes
        ],
    }


@router.get("")
def list_teaching_tasks(
    semester_id: int = Query(..., description="学期ID"),
    keyword: str = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(TeachingTask).filter(
        TeachingTask.semester_id == semester_id,
        TeachingTask.status == 1,
    )
    if keyword:
        query = query.join(TeachingTask.course).filter(
            or_(
                TeachingTask.task_code.contains(keyword),
                Course.name.contains(keyword),
            )
        )
    total = query.count()
    items = query.order_by(TeachingTask.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "list": [_task_to_dict(item) for item in items],
        "page": page,
        "page_size": page_size,
    }


@router.get("/{task_id}")
def get_teaching_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TeachingTask).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="教学任务不存在")
    return _task_to_dict(task)


@router.post("")
def create_teaching_task(data: TeachingTaskCreate, db: Session = Depends(get_db)):
    task_data = data.model_dump(exclude={"teacher_ids", "class_ids"})
    task = TeachingTask(**task_data)
    if not task.task_code:
        task.task_code = f"TASK{task.semester_id:04d}{task.course_id:04d}"
    db.add(task)
    db.flush()

    # 添加教师关联
    for idx, tid in enumerate(data.teacher_ids):
        tt = TaskTeacher(task_id=task.id, teacher_id=tid, is_main=(idx == 0))
        db.add(tt)

    # 添加班级关联
    for cid in data.class_ids:
        tc = TaskClass(task_id=task.id, class_group_id=cid)
        db.add(tc)

    db.commit()
    db.refresh(task)
    return _task_to_dict(task)


@router.put("/{task_id}")
def update_teaching_task(task_id: int, data: TeachingTaskUpdate, db: Session = Depends(get_db)):
    task = db.query(TeachingTask).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="教学任务不存在")

    update_data = data.model_dump(exclude_unset=True)
    teacher_ids = update_data.pop("teacher_ids", None)
    class_ids = update_data.pop("class_ids", None)

    for key, value in update_data.items():
        setattr(task, key, value)

    # 更新教师关联
    if teacher_ids is not None:
        db.query(TaskTeacher).filter(TaskTeacher.task_id == task_id).delete()
        for idx, tid in enumerate(teacher_ids):
            tt = TaskTeacher(task_id=task.id, teacher_id=tid, is_main=(idx == 0))
            db.add(tt)

    # 更新班级关联
    if class_ids is not None:
        db.query(TaskClass).filter(TaskClass.task_id == task_id).delete()
        for cid in class_ids:
            tc = TaskClass(task_id=task.id, class_group_id=cid)
            db.add(tc)

    db.commit()
    db.refresh(task)
    return _task_to_dict(task)


@router.delete("/{task_id}")
def delete_teaching_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TeachingTask).get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="教学任务不存在")
    task.status = 0
    db.commit()
    return {"message": "删除成功"}

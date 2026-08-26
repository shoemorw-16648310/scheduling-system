from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db, SessionLocal
from app.models.schedule import ScheduleBatch, ScheduleEntry
from app.models.teaching_task import TeachingTask
from app.schemas.schedule import (
    ScheduleGenerateRequest,
    ScheduleBatch as ScheduleBatchSchema,
    ScheduleEntry as ScheduleEntrySchema,
    ScheduleEntryUpdate,
    ScoreDimension,
    BatchScoreDetail,
    ScheduleCompareResponse,
)
import json

router = APIRouter()


def _generate_batch_code() -> str:
    return f"SCH{datetime.now().strftime('%Y%m%d%H%M%S')}"


def _get_current_batch_id(db: Session, semester_id: int) -> Optional[int]:
    """获取当前学期的激活批次ID"""
    batch = (
        db.query(ScheduleBatch)
        .filter(
            ScheduleBatch.semester_id == semester_id,
            ScheduleBatch.is_current == 1,
            ScheduleBatch.status == "completed",
        )
        .first()
    )
    return batch.id if batch else None


def _batch_to_schema(batch: ScheduleBatch) -> dict:
    """将 ScheduleBatch 模型转为带 score_detail 的字典"""
    result = {c.name: getattr(batch, c.name) for c in batch.__table__.columns}
    # 解析 score_detail_json
    if batch.score_detail_json:
        try:
            result["score_detail"] = json.loads(batch.score_detail_json)
        except (json.JSONDecodeError, TypeError):
            result["score_detail"] = None
    else:
        result["score_detail"] = None
    return result


@router.post("/generate")
def generate_schedule(
    data: ScheduleGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """触发排课计算（异步）"""
    batch_code = _generate_batch_code()
    batch = ScheduleBatch(
        batch_code=batch_code,
        semester_id=data.semester_id,
        status="pending",
        config_json=data.model_dump_json(),
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)

    # 启动后台排课任务
    background_tasks.add_task(
        _run_schedule_task,
        batch_id=batch.id,
        config=data,
    )

    return {"batch_code": batch_code, "status": "running", "batch_id": batch.id}


def _run_schedule_task(batch_id: int, config: ScheduleGenerateRequest):
    """后台执行排课任务（使用 CP-SAT 算法）"""
    db = SessionLocal()
    try:
        batch = db.query(ScheduleBatch).get(batch_id)
        batch.status = "running"
        batch.started_at = datetime.now()
        db.commit()

        # 1. 加载排课数据
        from app.services.scheduler.data_loader import (
            ScheduleDataLoader,
            ScheduleConfig,
        )
        from app.services.scheduler import run_schedule

        schedule_config = ScheduleConfig(
            semester_id=config.semester_id,
            days_per_week=config.days_per_week,
            time_limit_seconds=config.time_limit_seconds,
            strict_room_type=config.strict_room_type,
            constraint_weights=config.constraint_weights,
        )
        loader = ScheduleDataLoader(db, schedule_config)
        data = loader.load()

        # 2. 执行排课
        result = run_schedule(data)

        if result.success:
            # 3. 写入新批次的排课结果（不清空历史批次，保留以便对比）
            for entry_data in result.entries:
                entry = ScheduleEntry(
                    task_id=entry_data["task_id"],
                    classroom_id=entry_data["classroom_id"],
                    day_of_week=entry_data["day_of_week"],
                    section_start=entry_data["section_start"],
                    section_end=entry_data["section_end"],
                    weeks=entry_data["weeks"],
                    semester_id=batch.semester_id,
                    schedule_batch=batch.batch_code,
                    batch_id=batch.id,
                    is_manual=0,
                )
                db.add(entry)

            db.commit()
            batch.status = "completed"
            batch.score = result.score
            batch.score_detail_json = json.dumps(result.score_detail, ensure_ascii=False)
            batch.finished_at = datetime.now()
            batch.result_summary = json.dumps({
                "scheduled_tasks": result.scheduled_tasks,
                "total_tasks": result.total_tasks,
                "solve_time": round(result.solve_time, 2),
                "message": result.message,
            }, ensure_ascii=False)
            # 将新批次设为当前使用批次
            db.query(ScheduleBatch).filter(
                ScheduleBatch.semester_id == batch.semester_id,
                ScheduleBatch.id != batch.id,
            ).update({"is_current": 0})
            batch.is_current = 1
        else:
            batch.status = "failed"
            batch.message = result.message
            batch.finished_at = datetime.now()

        db.commit()
    except Exception as e:
        import traceback
        batch = db.query(ScheduleBatch).get(batch_id)
        batch.status = "failed"
        batch.message = str(e) + "\n" + traceback.format_exc()
        db.commit()
    finally:
        db.close()


@router.get("/batches")
def list_batches(
    semester_id: int = Query(None, description="学期ID"),
    db: Session = Depends(get_db),
):
    """排课批次列表"""
    query = db.query(ScheduleBatch)
    if semester_id:
        query = query.filter(ScheduleBatch.semester_id == semester_id)
    batches = query.order_by(ScheduleBatch.id.desc()).limit(20).all()
    return [_batch_to_schema(b) for b in batches]


@router.get("/batches/{batch_code}")
def get_batch(batch_code: str, db: Session = Depends(get_db)):
    """获取排课批次详情/状态"""
    batch = db.query(ScheduleBatch).filter(ScheduleBatch.batch_code == batch_code).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    return _batch_to_schema(batch)


@router.get("/entries")
def list_schedule_entries(
    semester_id: int = Query(..., description="学期ID"),
    teacher_id: int = Query(None, description="教师ID"),
    class_id: int = Query(None, description="班级ID"),
    classroom_id: int = Query(None, description="教室ID"),
    batch_code: str = Query(None, description="批次号（不传则查当前激活批次）"),
    db: Session = Depends(get_db),
):
    """查询排课结果"""
    # 确定批次ID
    if batch_code:
        batch = db.query(ScheduleBatch).filter_by(batch_code=batch_code).first()
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")
        batch_id = batch.id
    else:
        batch_id = _get_current_batch_id(db, semester_id)
        if not batch_id:
            return []

    query = db.query(ScheduleEntry).filter(ScheduleEntry.batch_id == batch_id)
    if teacher_id:
        query = query.join(TeachingTask).join(TeachingTask.task_teachers).filter_by(teacher_id=teacher_id)
    if class_id:
        query = query.join(TeachingTask).join(TeachingTask.task_classes).filter_by(class_group_id=class_id)
    if classroom_id:
        query = query.filter(ScheduleEntry.classroom_id == classroom_id)
    entries = query.all()

    # 组装返回数据
    result = []
    for entry in entries:
        item = {
            "id": entry.id,
            "task_id": entry.task_id,
            "classroom_id": entry.classroom_id,
            "day_of_week": entry.day_of_week,
            "section_start": entry.section_start,
            "section_end": entry.section_end,
            "weeks": entry.weeks,
            "semester_id": entry.semester_id,
            "schedule_batch": entry.schedule_batch,
            "is_manual": entry.is_manual,
        }
        if entry.task:
            item["course_name"] = entry.task.course.name if entry.task.course else ""
            item["teacher_names"] = ", ".join([tt.teacher.name for tt in entry.task.task_teachers])
            item["class_names"] = ", ".join([tc.class_group.name for tc in entry.task.task_classes])
        if entry.classroom:
            item["classroom_name"] = f"{entry.classroom.building}{entry.classroom.room_number}"
        result.append(item)
    return result


@router.put("/entries/{entry_id}")
def update_schedule_entry(
    entry_id: int,
    data: ScheduleEntryUpdate,
    db: Session = Depends(get_db),
):
    """手动调整单条排课记录（含冲突检测）"""
    entry = db.query(ScheduleEntry).get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="排课记录不存在")

    # 收集待更新的字段
    update_data = data.model_dump(exclude_unset=True)
    new_day = update_data.get("day_of_week", entry.day_of_week)
    new_start = update_data.get("section_start", entry.section_start)
    new_end = update_data.get("section_end", entry.section_end)
    new_room_id = update_data.get("classroom_id", entry.classroom_id)

    if new_end < new_start:
        raise HTTPException(status_code=400, detail="结束节次不能小于开始节次")

    # 冲突检测：查找同一批次内与该记录冲突的其他记录
    task = entry.task
    teacher_ids = [tt.teacher_id for tt in task.task_teachers] if task and task.task_teachers else []
    class_ids = [tc.class_group_id for tc in task.task_classes] if task and task.task_classes else []

    conflicts = []
    # 查找可能有时间重叠的其他记录
    other_entries = (
        db.query(ScheduleEntry)
        .filter(
            ScheduleEntry.batch_id == entry.batch_id,
            ScheduleEntry.id != entry.id,
            ScheduleEntry.day_of_week == new_day,
            ScheduleEntry.section_start <= new_end,
            ScheduleEntry.section_end >= new_start,
        )
        .all()
    )

    for other in other_entries:
        other_task = other.task
        # 教师冲突
        if other_task and other_task.task_teachers:
            other_teacher_ids = [tt.teacher_id for tt in other_task.task_teachers]
            clash_teachers = set(teacher_ids) & set(other_teacher_ids)
            if clash_teachers:
                conflicts.append({
                    "type": "teacher",
                    "with": other.id,
                    "detail": f"与课程「{other_task.course.name if other_task.course else ''}」教师冲突",
                })
                continue  # 有一个冲突类型就够了

        # 班级冲突
        if other_task and other_task.task_classes:
            other_class_ids = [tc.class_group_id for tc in other_task.task_classes]
            clash_classes = set(class_ids) & set(other_class_ids)
            if clash_classes:
                conflicts.append({
                    "type": "class",
                    "with": other.id,
                    "detail": f"与课程「{other_task.course.name if other_task.course else ''}」班级冲突",
                })
                continue

        # 教室冲突
        if new_room_id and other.classroom_id == new_room_id:
            conflicts.append({
                "type": "classroom",
                "with": other.id,
                "detail": f"与课程「{other_task.course.name if other_task and other_task.course else ''}」教室冲突",
            })

    if conflicts:
        raise HTTPException(
            status_code=409,
            detail=f"存在 {len(conflicts)} 个冲突：{conflicts[0]['detail']}",
        )

    for key, value in update_data.items():
        setattr(entry, key, value)
    entry.is_manual = 1
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/entries/{entry_id}")
def delete_schedule_entry(entry_id: int, db: Session = Depends(get_db)):
    """删除单条排课记录"""
    entry = db.query(ScheduleEntry).get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="排课记录不存在")
    db.delete(entry)
    db.commit()
    return {"message": "删除成功"}


@router.get("/conflicts")
def check_conflicts(
    semester_id: int = Query(...),
    batch_code: str = Query(None, description="批次号（不传则查当前激活批次）"),
    db: Session = Depends(get_db),
):
    """检测排课结果中的所有冲突"""
    if batch_code:
        batch = db.query(ScheduleBatch).filter_by(batch_code=batch_code).first()
        if not batch:
            raise HTTPException(status_code=404, detail="批次不存在")
        batch_id = batch.id
    else:
        batch_id = _get_current_batch_id(db, semester_id)
        if not batch_id:
            return {"conflicts": [], "total": 0}

    entries = (
        db.query(ScheduleEntry)
        .filter(ScheduleEntry.batch_id == batch_id)
        .order_by(ScheduleEntry.day_of_week, ScheduleEntry.section_start)
        .all()
    )

    conflicts = []
    seen_pairs = set()

    for i, e1 in enumerate(entries):
        for j in range(i + 1, len(entries)):
            e2 = entries[j]

            # 不同天跳过
            if e1.day_of_week != e2.day_of_week:
                continue
            # 时间不重叠跳过
            if e1.section_end < e2.section_start or e2.section_end < e1.section_start:
                continue

            # 计算冲突类型
            t1 = e1.task
            t2 = e2.task

            teacher_ids_1 = [tt.teacher_id for tt in t1.task_teachers] if t1 and t1.task_teachers else []
            teacher_ids_2 = [tt.teacher_id for tt in t2.task_teachers] if t2 and t2.task_teachers else []
            class_ids_1 = [tc.class_group_id for tc in t1.task_classes] if t1 and t1.task_classes else []
            class_ids_2 = [tc.class_group_id for tc in t2.task_classes] if t2 and t2.task_classes else []

            pair_key = tuple(sorted([e1.id, e2.id]))
            if pair_key in seen_pairs:
                continue

            clash_types = []
            if set(teacher_ids_1) & set(teacher_ids_2):
                clash_types.append("teacher")
            if set(class_ids_1) & set(class_ids_2):
                clash_types.append("class")
            if e1.classroom_id and e2.classroom_id and e1.classroom_id == e2.classroom_id:
                clash_types.append("classroom")

            if clash_types:
                seen_pairs.add(pair_key)
                conflicts.append({
                    "entry1_id": e1.id,
                    "entry2_id": e2.id,
                    "day_of_week": e1.day_of_week,
                    "section_start": max(e1.section_start, e2.section_start),
                    "section_end": min(e1.section_end, e2.section_end),
                    "types": clash_types,
                    "course1": t1.course.name if t1 and t1.course else "",
                    "course2": t2.course.name if t2 and t2.course else "",
                })

    return {"conflicts": conflicts, "total": len(conflicts)}


@router.get("/check-move")
def check_move_conflict(
    entry_id: int = Query(..., description="要移动的排课记录ID"),
    day_of_week: int = Query(..., ge=1, le=7, description="目标星期"),
    section_start: int = Query(..., ge=1, description="目标开始节次"),
    section_end: int = Query(..., ge=1, description="目标结束节次"),
    classroom_id: Optional[int] = Query(None, description="目标教室ID（不传则用原教室）"),
    db: Session = Depends(get_db),
):
    """拖拽时预检：移动某条排课记录到目标位置是否有冲突
    返回 has_conflict（是否冲突）+ conflicts（冲突详情列表）
    """
    entry = db.query(ScheduleEntry).get(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="排课记录不存在")

    if section_end < section_start:
        raise HTTPException(status_code=400, detail="结束节次不能小于开始节次")

    task = entry.task
    teacher_ids = [tt.teacher_id for tt in task.task_teachers] if task and task.task_teachers else []
    class_ids = [tc.class_group_id for tc in task.task_classes] if task and task.task_classes else []
    room_id = classroom_id if classroom_id is not None else entry.classroom_id

    # 查找时间重叠的其他记录（仅限于同一批次）
    other_entries = (
        db.query(ScheduleEntry)
        .filter(
            ScheduleEntry.batch_id == entry.batch_id,
            ScheduleEntry.id != entry.id,
            ScheduleEntry.day_of_week == day_of_week,
            ScheduleEntry.section_start <= section_end,
            ScheduleEntry.section_end >= section_start,
        )
        .all()
    )

    conflicts = []
    for other in other_entries:
        other_task = other.task
        clash_types = []

        # 教师冲突
        if other_task and other_task.task_teachers:
            other_teacher_ids = [tt.teacher_id for tt in other_task.task_teachers]
            if set(teacher_ids) & set(other_teacher_ids):
                clash_types.append("teacher")

        # 班级冲突
        if other_task and other_task.task_classes:
            other_class_ids = [tc.class_group_id for tc in other_task.task_classes]
            if set(class_ids) & set(other_class_ids):
                clash_types.append("class")

        # 教室冲突
        if room_id and other.classroom_id == room_id:
            clash_types.append("classroom")

        if clash_types:
            conflicts.append({
                "entry_id": other.id,
                "course_name": other_task.course.name if other_task and other_task.course else "",
                "types": clash_types,
            })

    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": conflicts,
        "total": len(conflicts),
    }


@router.post("/reset")
def reset_schedule(semester_id: int, db: Session = Depends(get_db)):
    """清空当前学期所有排课结果（所有批次）"""
    # 找到所有相关批次
    batches = db.query(ScheduleBatch).filter(ScheduleBatch.semester_id == semester_id).all()
    batch_ids = [b.id for b in batches]
    if batch_ids:
        db.query(ScheduleEntry).filter(ScheduleEntry.batch_id.in_(batch_ids)).delete()
    for batch in batches:
        db.delete(batch)
    db.commit()
    return {"message": "已清空排课结果"}


@router.get("/stats")
def get_schedule_stats(semester_id: int = Query(None), db: Session = Depends(get_db)):
    """排课统计概览
    - 排课完成率
    - 已排课节数
    - 教师数
    - 班级数
    - 冲突数
    """
    from app.models.teacher import Teacher
    from app.models.class_group import ClassGroup
    from app.models.classroom import Classroom
    from app.models.course import Course
    from app.models.teaching_task import TeachingTask
    from app.models.semester import Semester

    result = {
        "total_teachers": db.query(Teacher).filter(Teacher.status == 1).count(),
        "total_classrooms": db.query(Classroom).filter(Classroom.status == 1).count(),
        "total_courses": db.query(Course).count(),
        "total_classes": db.query(ClassGroup).filter(ClassGroup.status == 1).count(),
    }

    if semester_id:
        semester = db.query(Semester).get(semester_id)
        if semester:
            tasks = db.query(TeachingTask).filter(TeachingTask.semester_id == semester_id, TeachingTask.status == 1).all()
            batch_id = _get_current_batch_id(db, semester_id)
            if batch_id:
                entries = db.query(ScheduleEntry).filter(ScheduleEntry.batch_id == batch_id).all()
            else:
                entries = []
            scheduled_task_ids = set(e.task_id for e in entries)

            total_sections = sum(t.hours_per_week or 0 for t in tasks)
            scheduled_sections = sum(e.section_end - e.section_start + 1 for e in entries)

            # 冲突检测
            conflicts_count = 0
            for i, e1 in enumerate(entries):
                for j in range(i + 1, len(entries)):
                    e2 = entries[j]
                    if e1.day_of_week != e2.day_of_week:
                        continue
                    if e1.section_end < e2.section_start or e2.section_end < e1.section_start:
                        continue
                    t1 = e1.task
                    t2 = e2.task
                    if t1 and t2:
                        t1_teachers = set(tt.teacher_id for tt in t1.task_teachers)
                        t2_teachers = set(tt.teacher_id for tt in t2.task_teachers)
                        t1_classes = set(tc.class_group_id for tc in t1.task_classes)
                        t2_classes = set(tc.class_group_id for tc in t2.task_classes)
                        if (t1_teachers & t2_teachers) or (t1_classes & t2_classes):
                            conflicts_count += 1
                            break
                        if e1.classroom_id and e1.classroom_id == e2.classroom_id:
                            conflicts_count += 1
                            break

            result.update({
                "semester_name": semester.name,
                "total_tasks": len(tasks),
                "scheduled_tasks": len(scheduled_task_ids),
                "total_sections": total_sections,
                "scheduled_sections": scheduled_sections,
                "completion_rate": round(len(scheduled_task_ids) / len(tasks) * 100, 1) if tasks else 0,
                "conflicts": conflicts_count,
            })

    return result


# ==================== 评分对比相关 ====================

# 评分维度元信息（与前端、排课引擎保持一致）
SCORE_DIMENSIONS_INFO = [
    {"key": "main_course_morning", "label": "主课上午优先", "weight": 60, "description": "主课尽量安排在上午时段"},
    {"key": "teacher_daily_hours", "label": "教师日课时均衡", "weight": 50, "description": "教师每日课时不超过上限"},
    {"key": "uniform_distribution", "label": "课程均匀分布", "weight": 40, "description": "同一课程在周内均匀分布"},
    {"key": "teacher_consecutive", "label": "教师连堂限制", "weight": 30, "description": "教师连续课时不超过上限"},
    {"key": "noon_break", "label": "教师午休保护", "weight": 25, "description": "课程不跨越午休时段"},
    {"key": "class_daily_hours", "label": "班级日课时均衡", "weight": 20, "description": "班级每日课时相对均衡"},
    {"key": "room_balance", "label": "教室使用均衡", "weight": 15, "description": "各教室使用频次均衡"},
]


@router.get("/batches/{batch_code}/score-detail")
def get_batch_score_detail(batch_code: str, db: Session = Depends(get_db)):
    """获取单个批次的评分明细"""
    batch = db.query(ScheduleBatch).filter_by(batch_code=batch_code).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    if batch.status != "completed":
        raise HTTPException(status_code=400, detail="批次未完成，无评分数据")

    dimensions = None
    if batch.score_detail_json:
        try:
            dimensions = json.loads(batch.score_detail_json)
        except (json.JSONDecodeError, TypeError):
            dimensions = None

    summary = {}
    if batch.result_summary:
        try:
            summary = json.loads(batch.result_summary)
        except (json.JSONDecodeError, TypeError):
            summary = {}

    return {
        "batch_id": batch.id,
        "batch_code": batch.batch_code,
        "total_score": batch.score,
        "dimensions": dimensions,
        "solve_time": summary.get("solve_time"),
        "scheduled_tasks": summary.get("scheduled_tasks"),
        "total_tasks": summary.get("total_tasks"),
        "is_current": batch.is_current,
        "created_at": batch.created_at,
    }


@router.get("/compare")
def compare_batches(
    batch_codes: str = Query(..., description="批次号，逗号分隔，2-3个"),
    db: Session = Depends(get_db),
):
    """对比多个批次的评分（2-3个批次）"""
    codes = [c.strip() for c in batch_codes.split(",") if c.strip()]

    if len(codes) < 2:
        raise HTTPException(status_code=400, detail="至少需要选择2个批次进行对比")
    if len(codes) > 3:
        raise HTTPException(status_code=400, detail="最多支持3个批次同时对比")

    batches = (
        db.query(ScheduleBatch)
        .filter(ScheduleBatch.batch_code.in_(codes))
        .order_by(ScheduleBatch.id.asc())
        .all()
    )

    if len(batches) != len(codes):
        found_codes = {b.batch_code for b in batches}
        missing = [c for c in codes if c not in found_codes]
        raise HTTPException(status_code=404, detail=f"批次不存在：{', '.join(missing)}")

    for b in batches:
        if b.status != "completed":
            raise HTTPException(status_code=400, detail=f"批次 {b.batch_code} 未完成，无法对比")

    # 组装对比数据
    batch_details = []
    best_score = None
    best_batch_code = None

    for batch in batches:
        dimensions = None
        if batch.score_detail_json:
            try:
                dimensions = json.loads(batch.score_detail_json)
            except (json.JSONDecodeError, TypeError):
                dimensions = None

        summary = {}
        if batch.result_summary:
            try:
                summary = json.loads(batch.result_summary)
            except (json.JSONDecodeError, TypeError):
                summary = {}

        batch_details.append({
            "batch_id": batch.id,
            "batch_code": batch.batch_code,
            "total_score": batch.score,
            "dimensions": dimensions,
            "solve_time": summary.get("solve_time"),
            "scheduled_tasks": summary.get("scheduled_tasks"),
            "total_tasks": summary.get("total_tasks"),
            "is_current": batch.is_current,
            "created_at": batch.created_at,
        })

        if best_score is None or batch.score < best_score:
            best_score = batch.score
            best_batch_code = batch.batch_code

    return {
        "dimensions": SCORE_DIMENSIONS_INFO,
        "batches": batch_details,
        "best_batch_code": best_batch_code,
    }


@router.post("/batches/{batch_code}/activate")
def activate_batch(batch_code: str, db: Session = Depends(get_db)):
    """将指定批次设为当前使用批次"""
    batch = db.query(ScheduleBatch).filter_by(batch_code=batch_code).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批次不存在")
    if batch.status != "completed":
        raise HTTPException(status_code=400, detail="批次未完成，无法激活")

    if batch.is_current:
        return {"message": "该批次已是当前使用批次", "batch_code": batch_code}

    # 将学期内其他批次设为非当前
    db.query(ScheduleBatch).filter(
        ScheduleBatch.semester_id == batch.semester_id,
    ).update({"is_current": 0})

    # 将目标批次设为当前
    batch.is_current = 1
    db.commit()

    return {"message": "已切换到该批次排课结果", "batch_code": batch_code}

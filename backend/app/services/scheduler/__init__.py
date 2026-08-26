"""
启发式排课引擎
基于贪心初始化 + 模拟退火优化，不依赖原生库，跨平台兼容
"""
import random
import time
import math
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass, field

from .data_loader import (
    ScheduleData,
    TaskInfo,
    TeacherInfo,
    ClassroomInfo,
    ScheduleConfig,
)


@dataclass
class ScheduleEntry:
    """单条排课记录"""
    task_id: int
    session_idx: int
    day_of_week: int
    section_start: int
    section_end: int
    classroom_id: int


@dataclass
class ScheduleResult:
    """排课结果"""
    success: bool
    score: int
    score_detail: Dict[str, int]
    entries: List[Dict]
    scheduled_tasks: int
    total_tasks: int
    solve_time: float
    message: str = ""


class HeuristicScheduler:
    """启发式排课求解器"""

    def __init__(self, data: ScheduleData):
        self.data = data
        self.days = data.config.days_per_week
        self.sections = data.config.sections_per_day
        self.weights = data.config.constraint_weights
        self.room_ids = list(data.classrooms.keys())

        # 占用表 key: (day, section) -> {teachers: set, classes: set, rooms: set}
        self.occupied: Dict[Tuple[int, int], Dict[str, Set]] = {}
        for d in range(1, self.days + 1):
            for s in range(1, self.sections + 1):
                self.occupied[(d, s)] = {
                    "teachers": set(),
                    "classes": set(),
                    "rooms": set(),
                }

        # 当前排课方案 task_id -> [ScheduleEntry, ...]
        self.solution: Dict[int, List[ScheduleEntry]] = {}

    def solve(self) -> ScheduleResult:
        start_time = time.time()

        if not self.data.tasks:
            return ScheduleResult(False, 0, {}, [], 0, 0, 0, "没有教学任务")
        if not self.data.classrooms:
            return ScheduleResult(False, 0, {}, [], 0, len(self.data.tasks), 0, "没有可用教室")

        # 1. 贪心初始化
        success, failed_task, reason = self._greedy_init()
        if not success:
            return ScheduleResult(
                False, 0, {}, [], 0, len(self.data.tasks),
                time.time() - start_time,
                f"排课失败：任务「{failed_task}」无法安排 - {reason}"
            )

        # 2. 模拟退火优化
        time_limit = self.data.config.time_limit_seconds
        elapsed = time.time() - start_time
        remaining = max(2, time_limit - elapsed)
        self._simulated_annealing(max_time=remaining)

        # 3. 提取结果
        entries = self._extract_entries()
        score = self._calc_total_score()
        score_detail = self._calc_score_breakdown()
        elapsed = time.time() - start_time

        return ScheduleResult(
            success=True,
            score=score,
            score_detail=score_detail,
            entries=entries,
            scheduled_tasks=len(self.data.tasks),
            total_tasks=len(self.data.tasks),
            solve_time=elapsed,
            message=f"启发式求解完成（{len(entries)}条记录）",
        )

    # ─── 1. 贪心初始化 ────────────────────────────────────────

    def _greedy_init(self) -> tuple:
        """按优先级排序，逐个安排教学任务
        返回: (是否成功, 失败任务名, 失败原因)
        """
        # 按优先级从高到低排序，同优先级按课时多的先排
        task_list = sorted(
            self.data.tasks.values(),
            key=lambda t: (-t.priority, -t.hours_per_week),
        )

        for task in task_list:
            success, reason = self._place_task(task)
            if not success:
                return False, task.course_name, reason
        return True, None, None

    def _place_task(self, task: TaskInfo) -> tuple:
        """为一个任务的所有课次找可行位置
        返回: (是否成功, 失败原因)
        """
        entries = []
        # 先收集已占用的槽位，跳过这些
        for s in range(task.num_sessions):
            placed = False
            # 遍历所有可能的 (day, section, room) 组合，找第一个可行的
            for day in range(1, self.days + 1):
                if placed:
                    break
                max_start = self.sections - task.consecutive_sections + 1
                for sec_start in range(1, max_start + 1):
                    if placed:
                        break
                    # 按容量匹配教室
                    eligible_rooms = self._get_eligible_rooms(task)
                    if not eligible_rooms:
                        return False, f"没有容量足够的{task.required_room_type}类型教室（需容纳{task.student_count}人）"
                    for room_id in eligible_rooms:
                        if self._can_place(task, day, sec_start, room_id, entries):
                            entry = ScheduleEntry(
                                task_id=task.id,
                                session_idx=s,
                                day_of_week=day,
                                section_start=sec_start,
                                section_end=sec_start + task.consecutive_sections - 1,
                                classroom_id=room_id,
                            )
                            entries.append(entry)
                            self._mark_occupied(task, entry, occupy=True)
                            placed = True
                            break

            if not placed:
                # 回滚已安排的课次
                for e in entries:
                    self._mark_occupied(task, e, occupy=False)
                return False, "找不到可用的时间段（教师/班级/教室冲突）"

        self.solution[task.id] = entries
        return True, None

    def _get_eligible_rooms(self, task: TaskInfo) -> List[int]:
        """获取符合条件的教室列表（同校区优先排序）"""
        strict = getattr(self.data.config, 'strict_room_type', True)
        matching_type = []
        other_types = []
        normal_rooms = []

        # 计算任务的主校区（所有班级的校区，取最多的那个）
        task_campus = self._get_task_campus(task)

        for rid, room in self.data.classrooms.items():
            if room.capacity < task.student_count:
                continue
            if room.classroom_type == task.required_room_type:
                matching_type.append(rid)
            elif room.classroom_type == "normal":
                normal_rooms.append(rid)
            else:
                other_types.append(rid)

        if strict and matching_type:
            rooms = matching_type
        elif strict and task.required_room_type != "normal":
            return matching_type
        else:
            rooms = matching_type + normal_rooms + other_types

        # 同校区优先排序（有校区的教室排在前面，同校区的排最前）
        if task_campus:
            same_campus = [r for r in rooms if self.data.classrooms[r].campus == task_campus]
            other_campus = [r for r in rooms if self.data.classrooms[r].campus != task_campus]
            # 有校区但不同的 > 无校区的
            has_other = [r for r in other_campus if self.data.classrooms[r].campus]
            no_campus = [r for r in other_campus if not self.data.classrooms[r].campus]
            return same_campus + has_other + no_campus

        return rooms

    def _get_task_campus(self, task: TaskInfo) -> str:
        """获取任务的主校区（授课班级中出现最多的校区）"""
        if not task.class_ids:
            return ""
        campus_count = {}
        for cid in task.class_ids:
            cls = self.data.classes.get(cid)
            if cls and cls.campus:
                campus_count[cls.campus] = campus_count.get(cls.campus, 0) + 1
        if not campus_count:
            return ""
        return max(campus_count, key=campus_count.get)

    def _can_place(
        self, task: TaskInfo, day: int, sec_start: int, room_id: int,
        existing_entries: List[ScheduleEntry],
    ) -> bool:
        """检查在 (day, sec_start) 用 room_id 上 task 是否可行"""
        sec_end = sec_start + task.consecutive_sections - 1
        if sec_end > self.sections:
            return False

        teacher_ids = task.teacher_ids
        class_ids = task.class_ids

        for sec in range(sec_start, sec_end + 1):
            slot = self.occupied[(day, sec)]
            # 教师冲突
            for tid in teacher_ids:
                if tid in slot["teachers"]:
                    return False
            # 班级冲突
            for cid in class_ids:
                if cid in slot["classes"]:
                    return False
            # 教室冲突
            if room_id in slot["rooms"]:
                return False
            # 教师不可用时间
            for tid in teacher_ids:
                teacher = self.data.teachers.get(tid)
                if teacher and (day, sec) in teacher.unavailable_slots:
                    return False

        # 检查同一任务内不同课次不冲突（同一天同一节次）
        for e in existing_entries:
            if e.day_of_week == day:
                if not (sec_end < e.section_start or sec_start > e.section_end):
                    return False

        return True

    def _mark_occupied(self, task: TaskInfo, entry: ScheduleEntry, occupy: bool = True):
        """标记或释放占用"""
        for sec in range(entry.section_start, entry.section_end + 1):
            slot = self.occupied[(entry.day_of_week, sec)]
            for tid in task.teacher_ids:
                if occupy:
                    slot["teachers"].add(tid)
                else:
                    slot["teachers"].discard(tid)
            for cid in task.class_ids:
                if occupy:
                    slot["classes"].add(cid)
                else:
                    slot["classes"].discard(cid)
            if occupy:
                slot["rooms"].add(entry.classroom_id)
            else:
                slot["rooms"].discard(entry.classroom_id)

    # ─── 2. 模拟退火优化 ──────────────────────────────────────

    def _simulated_annealing(self, max_time: float = 10.0):
        """模拟退火优化软约束"""
        start_time = time.time()
        task_ids = list(self.data.tasks.keys())

        current_score = self._calc_total_score()
        best_score = current_score
        best_solution = self._deep_copy_solution()

        T = 100.0  # 初始温度
        T_min = 0.1
        alpha = 0.995  # 降温系数

        iterations = 0

        while T > T_min and time.time() - start_time < max_time:
            iterations += 1
            # 随机选一个任务，随机选一个课次，随机移动
            task_id = random.choice(task_ids)
            task = self.data.tasks[task_id]
            if task.num_sessions == 0:
                continue

            s_idx = random.randint(0, task.num_sessions - 1)
            old_entry = self.solution[task_id][s_idx]

            # 生成新位置
            new_day = random.randint(1, self.days)
            max_start = self.sections - task.consecutive_sections + 1
            new_sec = random.randint(1, max_start)
            eligible_rooms = self._get_eligible_rooms(task)
            new_room = random.choice(eligible_rooms)

            new_entry = ScheduleEntry(
                task_id=task_id,
                session_idx=s_idx,
                day_of_week=new_day,
                section_start=new_sec,
                section_end=new_sec + task.consecutive_sections - 1,
                classroom_id=new_room,
            )

            # 尝试移动
            delta = self._try_move(task, s_idx, new_entry)
            if delta is None:
                # 不可行，跳过
                continue

            new_score = current_score + delta

            if delta < 0 or random.random() < math.exp(-delta / T):
                # 接受新解
                current_score = new_score
                if current_score < best_score:
                    best_score = current_score
                    best_solution = self._deep_copy_solution()
            else:
                # 不接受，回滚
                self._try_move(task, s_idx, old_entry)

            T *= alpha

        # 恢复最优解
        self._restore_solution(best_solution)

    def _try_move(self, task: TaskInfo, s_idx: int, new_entry: ScheduleEntry) -> int:
        """尝试移动一个课次，返回分数变化（delta），不可行返回 None"""
        old_entry = self.solution[task.id][s_idx]

        if (new_entry.day_of_week == old_entry.day_of_week
                and new_entry.section_start == old_entry.section_start
                and new_entry.classroom_id == old_entry.classroom_id):
            return 0

        # 先释放旧位置
        self._mark_occupied(task, old_entry, occupy=False)

        # 检查新位置是否可行
        other_entries = [e for i, e in enumerate(self.solution[task.id]) if i != s_idx]
        if not self._can_place(task, new_entry.day_of_week, new_entry.section_start,
                               new_entry.classroom_id, other_entries):
            # 不可行，恢复旧位置
            self._mark_occupied(task, old_entry, occupy=True)
            return None

        # 计算旧位置对软约束的贡献
        old_penalty = self._entry_penalty(task, old_entry, s_idx)

        # 占用新位置
        self._mark_occupied(task, new_entry, occupy=True)
        self.solution[task.id][s_idx] = new_entry

        # 计算新位置对软约束的贡献
        new_penalty = self._entry_penalty(task, new_entry, s_idx)

        return new_penalty - old_penalty

    def _deep_copy_solution(self) -> Dict[int, List[ScheduleEntry]]:
        """深拷贝当前方案"""
        return {
            tid: [ScheduleEntry(
                task_id=e.task_id,
                session_idx=e.session_idx,
                day_of_week=e.day_of_week,
                section_start=e.section_start,
                section_end=e.section_end,
                classroom_id=e.classroom_id,
            ) for e in entries]
            for tid, entries in self.solution.items()
        }

    def _restore_solution(self, solution: Dict[int, List[ScheduleEntry]]):
        """恢复到某个方案"""
        # 清空所有占用
        for d in range(1, self.days + 1):
            for s in range(1, self.sections + 1):
                self.occupied[(d, s)]["teachers"].clear()
                self.occupied[(d, s)]["classes"].clear()
                self.occupied[(d, s)]["rooms"].clear()

        self.solution = solution
        for task_id, entries in solution.items():
            task = self.data.tasks[task_id]
            for e in entries:
                self._mark_occupied(task, e, occupy=True)

    # ─── 3. 评分（软约束惩罚） ────────────────────────────────

    def _calc_total_score(self) -> int:
        """计算总惩罚分数（越低越好）"""
        total = 0
        for task_id, entries in self.solution.items():
            task = self.data.tasks[task_id]
            for s_idx, entry in enumerate(entries):
                total += self._entry_penalty(task, entry, s_idx)
        return total

    def _calc_score_breakdown(self) -> Dict[str, int]:
        """计算分维度的惩罚分明细"""
        dimensions = [
            "main_course_morning",
            "teacher_daily_hours",
            "uniform_distribution",
            "teacher_consecutive",
            "noon_break",
            "class_daily_hours",
            "room_balance",
            "same_campus",
        ]
        breakdown = {dim: 0 for dim in dimensions}
        w = self.weights
        morning_sections = self.data.morning_sections

        for task_id, entries in self.solution.items():
            task = self.data.tasks[task_id]
            # 优先级加权系数
            priority_factor = 1.0
            if w.get("priority_weighted"):
                priority_factor = 0.5 + task.priority * 0.15

            def pw(val):
                return int(val * priority_factor)

            for s_idx, entry in enumerate(entries):
                # 主课上午
                if task.is_main_subject and w.get("main_course_morning", 0) > 0:
                    if entry.section_start > morning_sections:
                        breakdown["main_course_morning"] += pw(w["main_course_morning"])

                # 午休
                if w.get("noon_break", 0) > 0:
                    if (entry.section_start <= morning_sections
                            and entry.section_end > morning_sections):
                        for tid in task.teacher_ids:
                            teacher = self.data.teachers.get(tid)
                            if teacher and teacher.need_noon_break:
                                breakdown["noon_break"] += pw(w["noon_break"])
                                break

                # 均匀分布
                if w.get("uniform_distribution", 0) > 0:
                    same_day_count = 0
                    for i, e in enumerate(self.solution[task.id]):
                        if i != s_idx and e.day_of_week == entry.day_of_week:
                            same_day_count += 1
                    breakdown["uniform_distribution"] += same_day_count * pw(w["uniform_distribution"])

                # 教师日课时
                if w.get("teacher_daily_hours", 0) > 0:
                    for tid in task.teacher_ids:
                        teacher = self.data.teachers.get(tid)
                        if teacher and teacher.max_hours_per_day > 0:
                            day_hours = self._teacher_day_hours(tid, entry.day_of_week)
                            if day_hours > teacher.max_hours_per_day:
                                breakdown["teacher_daily_hours"] += (day_hours - teacher.max_hours_per_day) * pw(w["teacher_daily_hours"])

                # 教师连堂
                if w.get("teacher_consecutive", 0) > 0:
                    for tid in task.teacher_ids:
                        teacher = self.data.teachers.get(tid)
                        if teacher and teacher.max_consecutive_hours > 0:
                            cons = self._teacher_consecutive_at(tid, entry.day_of_week, entry.section_start)
                            if cons > teacher.max_consecutive_hours:
                                breakdown["teacher_consecutive"] += (cons - teacher.max_consecutive_hours) * pw(w["teacher_consecutive"])

                # 班级日课时
                if w.get("class_daily_hours", 0) > 0:
                    max_class_hours = 6
                    for cid in task.class_ids:
                        day_hours = self._class_day_hours(cid, entry.day_of_week)
                        if day_hours > max_class_hours:
                            breakdown["class_daily_hours"] += (day_hours - max_class_hours) * pw(w["class_daily_hours"])

                # 教室均衡
                if w.get("room_balance", 0) > 0:
                    room_hours = self._room_total_hours(entry.classroom_id)
                    avg_hours = self._avg_room_hours()
                    if avg_hours > 0 and room_hours > avg_hours * 1.3:
                        breakdown["room_balance"] += int(w["room_balance"] * (room_hours / avg_hours - 1))

                # 同校区
                if w.get("same_campus", 0) > 0:
                    room = self.data.classrooms.get(entry.classroom_id)
                    if room and room.campus:
                        task_campus = self._get_task_campus(task)
                        if task_campus and room.campus != task_campus:
                            breakdown["same_campus"] += pw(w["same_campus"])

        return breakdown

    def _entry_penalty(self, task: TaskInfo, entry: ScheduleEntry, s_idx: int) -> int:
        """计算单个课次的软约束惩罚"""
        penalty = 0
        w = self.weights
        morning_sections = self.data.morning_sections

        # 优先级加权系数（优先级越高惩罚越重，即越优先满足约束）
        priority_factor = 1.0
        if w.get("priority_weighted"):
            priority_factor = 0.5 + task.priority * 0.15  # 范围：0.65 ~ 2.0

        def pw(val):
            """应用优先级加权"""
            return int(val * priority_factor)

        # 主课上午惩罚
        if task.is_main_subject and w.get("main_course_morning", 0) > 0:
            if entry.section_start > morning_sections:
                penalty += pw(w["main_course_morning"])

        # 午休惩罚（教师需要午休且课程跨午休时段）
        if w.get("noon_break", 0) > 0:
            if (entry.section_start <= morning_sections
                    and entry.section_end > morning_sections):
                # 检查教师是否需要午休
                for tid in task.teacher_ids:
                    teacher = self.data.teachers.get(tid)
                    if teacher and teacher.need_noon_break:
                        penalty += pw(w["noon_break"])
                        break  # 有一个教师需要午休就算

        # 均匀分布惩罚（同任务其他课次在同一天）
        if w.get("uniform_distribution", 0) > 0:
            same_day_count = 0
            for i, e in enumerate(self.solution[task.id]):
                if i != s_idx and e.day_of_week == entry.day_of_week:
                    same_day_count += 1
            penalty += same_day_count * pw(w["uniform_distribution"])

        # 教师日课时惩罚
        if w.get("teacher_daily_hours", 0) > 0:
            for tid in task.teacher_ids:
                teacher = self.data.teachers.get(tid)
                if teacher and teacher.max_hours_per_day > 0:
                    day_hours = self._teacher_day_hours(tid, entry.day_of_week)
                    if day_hours > teacher.max_hours_per_day:
                        penalty += (day_hours - teacher.max_hours_per_day) * pw(w["teacher_daily_hours"])

        # 教师连续课时惩罚
        if w.get("teacher_consecutive", 0) > 0:
            for tid in task.teacher_ids:
                teacher = self.data.teachers.get(tid)
                if teacher and teacher.max_consecutive_hours > 0:
                    cons = self._teacher_consecutive_at(tid, entry.day_of_week, entry.section_start)
                    if cons > teacher.max_consecutive_hours:
                        penalty += (cons - teacher.max_consecutive_hours) * pw(w["teacher_consecutive"])

        # 班级日课时惩罚（每天不超过6节）
        if w.get("class_daily_hours", 0) > 0:
            max_class_hours = 6
            for cid in task.class_ids:
                day_hours = self._class_day_hours(cid, entry.day_of_week)
                if day_hours > max_class_hours:
                    penalty += (day_hours - max_class_hours) * pw(w["class_daily_hours"])

        # 教室使用均衡惩罚（避免某些教室过度使用）
        if w.get("room_balance", 0) > 0:
            room_hours = self._room_total_hours(entry.classroom_id)
            avg_hours = self._avg_room_hours()
            if avg_hours > 0 and room_hours > avg_hours * 1.3:
                penalty += int(w["room_balance"] * (room_hours / avg_hours - 1))

        # 同校区惩罚（教室与班级不在同一校区时扣分）
        if w.get("same_campus", 0) > 0:
            room = self.data.classrooms.get(entry.classroom_id)
            if room and room.campus:
                task_campus = self._get_task_campus(task)
                if task_campus and room.campus != task_campus:
                    penalty += pw(w["same_campus"])

        return penalty

    def _teacher_day_hours(self, teacher_id: int, day: int) -> int:
        """计算教师某天的总课时"""
        total = 0
        for task_id in self.data.teacher_tasks.get(teacher_id, []):
            task = self.data.tasks.get(task_id)
            if not task:
                continue
            for e in self.solution.get(task_id, []):
                if e.day_of_week == day:
                    total += task.consecutive_sections
        return total

    def _class_day_hours(self, class_id: int, day: int) -> int:
        """计算班级某天的总课时"""
        total = 0
        for task_id in self.data.class_tasks.get(class_id, []):
            task = self.data.tasks.get(task_id)
            if not task:
                continue
            for e in self.solution.get(task_id, []):
                if e.day_of_week == day:
                    total += task.consecutive_sections
        return total

    def _room_total_hours(self, room_id: int) -> int:
        """计算某教室每周总课时"""
        total = 0
        for task_id, entries in self.solution.items():
            task = self.data.tasks.get(task_id)
            if not task:
                continue
            for e in entries:
                if e.classroom_id == room_id:
                    total += task.consecutive_sections
        return total

    def _avg_room_hours(self) -> float:
        """计算所有教室的平均周课时"""
        if not self.data.classrooms:
            return 0
        total_entries = sum(
            len(entries) * self.data.tasks[tid].consecutive_sections
            for tid, entries in self.solution.items()
        )
        return total_entries / len(self.data.classrooms)

    def _teacher_consecutive_at(self, teacher_id: int, day: int, sec: int) -> int:
        """计算教师某天某节次前后的连续课时数"""
        # 收集该教师当天所有课的节次集合
        occupied_secs = set()
        for task_id in self.data.teacher_tasks.get(teacher_id, []):
            task = self.data.tasks.get(task_id)
            if not task:
                continue
            for e in self.solution.get(task_id, []):
                if e.day_of_week == day:
                    for s in range(e.section_start, e.section_end + 1):
                        occupied_secs.add(s)

        if sec not in occupied_secs:
            return 0

        # 向左延伸
        cons = 1
        s = sec - 1
        while s >= 1 and s in occupied_secs:
            cons += 1
            s -= 1
        # 向右延伸
        s = sec + 1
        while s <= self.sections and s in occupied_secs:
            cons += 1
            s += 1
        return cons

    # ─── 4. 提取结果 ─────────────────────────────────────────

    def _extract_entries(self) -> List[Dict]:
        result = []
        for task_id, entries in self.solution.items():
            for e in entries:
                result.append({
                    "task_id": e.task_id,
                    "classroom_id": e.classroom_id,
                    "day_of_week": e.day_of_week,
                    "section_start": e.section_start,
                    "section_end": e.section_end,
                    "weeks": "all",
                })
        return result


def run_schedule(data: ScheduleData) -> ScheduleResult:
    """执行排课的便捷函数"""
    scheduler = HeuristicScheduler(data)
    return scheduler.solve()

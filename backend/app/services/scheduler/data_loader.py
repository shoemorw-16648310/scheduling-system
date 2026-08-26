"""
排课数据结构
从数据库加载数据，转换为算法使用的内部数据结构
"""
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple
from sqlalchemy.orm import Session

from app.models.teaching_task import TeachingTask, TaskTeacher, TaskClass
from app.models.teacher import Teacher, TeacherUnavailable
from app.models.classroom import Classroom
from app.models.class_group import ClassGroup
from app.models.course import Course
from app.models.timeslot import TimeSlot
from app.models.semester import Semester


@dataclass
class TaskInfo:
    """教学任务信息（排课基本单元）"""
    id: int
    task_code: str
    course_id: int
    course_name: str
    hours_per_week: int           # 周学时
    consecutive_sections: int     # 每次课连续节数
    num_sessions: int             # 每周排几次课
    required_room_type: str       # 所需教室类型
    subject_type: str             # 主课/副课/实验
    is_main_subject: bool         # 是否主课（影响软约束）
    priority: int                 # 优先级
    student_count: int            # 学生人数
    teacher_ids: List[int] = field(default_factory=list)   # 授课教师ID列表
    main_teacher_id: int = 0      # 主讲教师ID
    class_ids: List[int] = field(default_factory=list)     # 授课班级ID列表


@dataclass
class TeacherInfo:
    id: int
    name: str
    max_hours_per_day: int
    max_consecutive_hours: int
    need_noon_break: bool
    unavailable_slots: Set[Tuple[int, int]] = field(default_factory=set)  # (day_of_week, section)


@dataclass
class ClassroomInfo:
    id: int
    room_no: str
    building: str
    room_number: str
    capacity: int
    classroom_type: str
    campus: str = ""


@dataclass
class ClassInfo:
    id: int
    name: str
    student_count: int
    campus: str = ""


@dataclass
class ScheduleConfig:
    """排课配置"""
    semester_id: int
    days_per_week: int = 5
    sections_per_day: int = 10
    time_limit_seconds: int = 120
    num_workers: int = 4
    # 硬约束开关
    strict_room_type: bool = True  # 严格教室类型匹配（类型不匹配直接排除）
    # 软约束权重
    constraint_weights: Dict[str, int] = field(default_factory=lambda: {
        "teacher_daily_hours": 50,
        "teacher_consecutive": 30,
        "uniform_distribution": 40,
        "main_course_morning": 60,
        "noon_break": 25,
        "class_daily_hours": 20,
        "room_balance": 15,
        "same_campus": 35,
        "priority_weighted": True,  # 优先级越高惩罚权重越大
    })


@dataclass
class ScheduleData:
    """排课所需的全部数据"""
    config: ScheduleConfig
    tasks: Dict[int, TaskInfo] = field(default_factory=dict)
    teachers: Dict[int, TeacherInfo] = field(default_factory=dict)
    classrooms: Dict[int, ClassroomInfo] = field(default_factory=dict)
    classes: Dict[int, ClassInfo] = field(default_factory=dict)
    time_slots: List[TimeSlot] = field(default_factory=list)

    # 反向索引
    teacher_tasks: Dict[int, List[int]] = field(default_factory=dict)  # teacher_id -> [task_id, ...]
    class_tasks: Dict[int, List[int]] = field(default_factory=dict)    # class_id -> [task_id, ...]

    # 上午节次数量（用于软约束判断）
    morning_sections: int = 4


class ScheduleDataLoader:
    """从数据库加载排课数据"""

    def __init__(self, db: Session, config: ScheduleConfig):
        self.db = db
        self.config = config

    def load(self) -> ScheduleData:
        data = ScheduleData(config=self.config)

        # 1. 加载节次配置
        self._load_time_slots(data)

        # 2. 加载教师
        self._load_teachers(data)

        # 3. 加载教室
        self._load_classrooms(data)

        # 4. 加载班级
        self._load_classes(data)

        # 5. 加载教学任务
        self._load_tasks(data)

        # 6. 计算上午节次数量
        self._calc_morning_sections(data)

        return data

    def _load_time_slots(self, data: ScheduleData):
        slots = self.db.query(TimeSlot).order_by(TimeSlot.section).all()
        data.time_slots = slots
        if slots:
            self.config.sections_per_day = len(slots)

    def _load_teachers(self, data: ScheduleData):
        teachers = self.db.query(Teacher).filter(Teacher.status == 1).all()
        for t in teachers:
            unavail_set = set()
            for unavail in t.unavailables:
                for sec in range(unavail.section_start, unavail.section_end + 1):
                    # day_of_week=0 表示所有工作日
                    if unavail.day_of_week == 0:
                        for day in range(1, self.config.days_per_week + 1):
                            unavail_set.add((day, sec))
                    else:
                        unavail_set.add((unavail.day_of_week, sec))

            info = TeacherInfo(
                id=t.id,
                name=t.name,
                max_hours_per_day=t.max_hours_per_day,
                max_consecutive_hours=t.max_consecutive_hours,
                need_noon_break=t.need_noon_break,
                unavailable_slots=unavail_set,
            )
            data.teachers[t.id] = info
            data.teacher_tasks[t.id] = []

    def _load_classrooms(self, data: ScheduleData):
        classrooms = self.db.query(Classroom).filter(Classroom.status == 1).all()
        for c in classrooms:
            info = ClassroomInfo(
                id=c.id,
                room_no=c.room_no,
                building=c.building,
                room_number=c.room_number,
                capacity=c.capacity,
                classroom_type=c.classroom_type,
                campus=c.campus or "",
            )
            data.classrooms[c.id] = info

    def _load_classes(self, data: ScheduleData):
        classes = self.db.query(ClassGroup).filter(ClassGroup.status == 1).all()
        for c in classes:
            info = ClassInfo(
                id=c.id,
                name=c.name,
                student_count=c.student_count,
                campus=c.campus or "",
            )
            data.classes[c.id] = info
            data.class_tasks[c.id] = []

    def _load_tasks(self, data: ScheduleData):
        tasks = (
            self.db.query(TeachingTask)
            .filter(
                TeachingTask.semester_id == self.config.semester_id,
                TeachingTask.status == 1,
            )
            .all()
        )

        for task in tasks:
            course: Course = task.course
            if not course:
                continue

            # 周学时：教学任务覆盖 > 课程默认
            hpw = task.hours_per_week if task.hours_per_week else course.hours_per_week

            # 连堂节数
            consecutive = course.consecutive_sections if course.is_consecutive else 1
            if consecutive < 1:
                consecutive = 1

            # 每周排课次数 = 周学时 / 连堂节数（向上取整）
            num_sessions = max(1, (hpw + consecutive - 1) // consecutive)

            # 学生人数：教学任务覆盖 > 班级人数总和
            student_count = task.student_count
            if not student_count:
                total = 0
                for tc in task.task_classes:
                    if tc.class_group:
                        total += tc.class_group.student_count
                student_count = total if total > 0 else 30

            teacher_ids = [tt.teacher_id for tt in task.task_teachers]
            main_teacher_id = teacher_ids[0] if teacher_ids else 0
            class_ids = [tc.class_group_id for tc in task.task_classes]

            is_main = course.subject_type in ("主课", "必修")

            info = TaskInfo(
                id=task.id,
                task_code=task.task_code or f"TASK{task.id}",
                course_id=task.course_id,
                course_name=course.name,
                hours_per_week=hpw,
                consecutive_sections=consecutive,
                num_sessions=num_sessions,
                required_room_type=course.required_room_type or "normal",
                subject_type=course.subject_type,
                is_main_subject=is_main,
                priority=task.priority or 5,
                student_count=student_count,
                teacher_ids=teacher_ids,
                main_teacher_id=main_teacher_id,
                class_ids=class_ids,
            )
            data.tasks[task.id] = info

            # 建立反向索引
            for tid in teacher_ids:
                if tid in data.teacher_tasks:
                    data.teacher_tasks[tid].append(task.id)
            for cid in class_ids:
                if cid in data.class_tasks:
                    data.class_tasks[cid].append(task.id)

    def _calc_morning_sections(self, data: ScheduleData):
        """计算上午有多少节"""
        count = 0
        for slot in data.time_slots:
            if slot.period == "morning":
                count += 1
            else:
                break
        if count == 0:
            count = data.config.sections_per_day // 2  # 默认上下午各一半
        data.morning_sections = count

"""
初始化演示数据
运行方式：python scripts/init_demo_data.py
"""
import sys
import os
from datetime import date

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import SessionLocal, engine, Base
from app.models import *  # noqa


def init_data():
    db = SessionLocal()

    try:
        # 先清空已有数据（按外键依赖的反向顺序）
        print("清空旧数据...")
        db.execute(ScheduleEntry.__table__.delete())
        db.execute(ScheduleBatch.__table__.delete())
        db.execute(TaskClass.__table__.delete())
        db.execute(TaskTeacher.__table__.delete())
        db.execute(TeachingTask.__table__.delete())
        db.execute(ClassGroup.__table__.delete())
        db.execute(Classroom.__table__.delete())
        db.execute(TeacherUnavailable.__table__.delete())
        db.execute(Teacher.__table__.delete())
        db.execute(Course.__table__.delete())
        db.execute(TimeSlot.__table__.delete())
        db.execute(Semester.__table__.delete())
        db.execute(Major.__table__.delete())
        db.execute(Department.__table__.delete())
        db.commit()

        # 1. 创建节次
        print("初始化节次配置...")
        time_slots = [
            (1, "第1节", "08:00", "08:45", "morning"),
            (2, "第2节", "08:55", "09:40", "morning"),
            (3, "第3节", "10:00", "10:45", "morning"),
            (4, "第4节", "10:55", "11:40", "morning"),
            (5, "第5节", "14:00", "14:45", "afternoon"),
            (6, "第6节", "14:55", "15:40", "afternoon"),
            (7, "第7节", "16:00", "16:45", "afternoon"),
            (8, "第8节", "16:55", "17:40", "afternoon"),
            (9, "第9节", "19:00", "19:45", "evening"),
            (10, "第10节", "19:55", "20:40", "evening"),
        ]
        for sec, name, start, end, period in time_slots:
            slot = TimeSlot(section=sec, name=name, start_time=start, end_time=end, period=period)
            db.add(slot)
        db.commit()

        # 2. 创建院系和专业
        print("初始化院系和专业...")
        dept_cs = Department(name="计算机学院", code="CS")
        dept_math = Department(name="数学学院", code="MATH")
        dept_eng = Department(name="外国语学院", code="FL")
        db.add_all([dept_cs, dept_math, dept_eng])
        db.commit()

        major_cs = Major(name="计算机科学与技术", code="CS001", department_id=dept_cs.id)
        major_se = Major(name="软件工程", code="SE001", department_id=dept_cs.id)
        major_math = Major(name="数学与应用数学", code="MATH001", department_id=dept_math.id)
        db.add_all([major_cs, major_se, major_math])
        db.commit()

        # 3. 创建学期
        print("初始化学期...")
        semester = Semester(
            name="2024-2025学年第一学期",
            code="2024-2025-1",
            start_date=date(2024, 9, 1),
            end_date=date(2025, 1, 15),
            total_weeks=18,
            is_active=True,
        )
        db.add(semester)
        db.commit()

        # 4. 创建教师 (10位)
        print("初始化教师...")
        teachers = [
            ("T001", "张伟", "男", "教授", dept_cs.id, 6, 4, True),
            ("T002", "李娜", "女", "副教授", dept_cs.id, 6, 4, True),
            ("T003", "王强", "男", "副教授", dept_cs.id, 6, 4, False),
            ("T004", "刘芳", "女", "讲师", dept_cs.id, 6, 4, True),
            ("T005", "陈明", "男", "教授", dept_cs.id, 4, 2, True),
            ("T006", "杨丽", "女", "副教授", dept_math.id, 6, 4, True),
            ("T007", "赵磊", "男", "讲师", dept_math.id, 6, 4, False),
            ("T008", "黄静", "女", "教授", dept_eng.id, 6, 4, True),
            ("T009", "周杰", "男", "副教授", dept_eng.id, 6, 4, True),
            ("T010", "吴敏", "女", "讲师", dept_eng.id, 8, 4, False),
        ]
        for no, name, gender, title, dept_id, max_day, max_consec, noon in teachers:
            t = Teacher(
                teacher_no=no, name=name, gender=gender, title=title,
                department_id=dept_id, max_hours_per_day=max_day,
                max_consecutive_hours=max_consec, need_noon_break=noon,
            )
            db.add(t)
        db.commit()

        # 5. 创建教室 (14间)
        print("初始化教室...")
        classrooms = [
            ("A101", "A座", "101", 60, "multimedia"),
            ("A102", "A座", "102", 60, "multimedia"),
            ("A201", "A座", "201", 80, "multimedia"),
            ("A202", "A座", "202", 80, "normal"),
            ("A301", "A座", "301", 120, "multimedia"),
            ("A302", "A座", "302", 120, "normal"),
            ("B101", "B座", "101", 60, "computer"),
            ("B102", "B座", "102", 60, "computer"),
            ("B103", "B座", "103", 80, "computer"),
            ("B201", "B座", "201", 50, "lab"),
            ("B202", "B座", "202", 50, "lab"),
            ("C101", "C座", "101", 30, "arts"),
            ("C201", "C座", "201", 150, "normal"),
            ("C301", "C座", "301", 200, "multimedia"),
        ]
        for no, building, room_num, cap, rtype in classrooms:
            c = Classroom(room_no=no, building=building, room_number=room_num, capacity=cap, classroom_type=rtype)
            db.add(c)
        db.commit()

        # 6. 创建班级 (6个)
        print("初始化班级...")
        classes = [
            ("CS2401", "计算机2401班", "2024", major_cs.id, dept_cs.id, 50),
            ("CS2402", "计算机2402班", "2024", major_cs.id, dept_cs.id, 48),
            ("SE2401", "软件工程2401班", "2024", major_se.id, dept_cs.id, 45),
            ("SE2402", "软件工程2402班", "2024", major_se.id, dept_cs.id, 46),
            ("MATH2401", "数学2401班", "2024", major_math.id, dept_math.id, 40),
            ("CS2301", "计算机2301班", "2023", major_cs.id, dept_cs.id, 52),
        ]
        for no, name, grade, major_id, dept_id, count in classes:
            c = ClassGroup(class_no=no, name=name, grade=grade, major_id=major_id, department_id=dept_id, student_count=count)
            db.add(c)
        db.commit()

        # 7. 创建课程 (12门)
        print("初始化课程...")
        courses = [
            ("CS101", "计算机基础", 2, 32, 2, "必修", "主课", "multimedia", True, 2, dept_cs.id),
            ("CS102", "C语言程序设计", 4, 64, 4, "必修", "主课", "computer", True, 2, dept_cs.id),
            ("CS201", "数据结构", 3, 48, 3, "必修", "主课", "computer", True, 2, dept_cs.id),
            ("CS202", "操作系统", 3, 48, 3, "必修", "主课", "multimedia", True, 2, dept_cs.id),
            ("CS301", "数据库原理", 3, 48, 3, "必修", "主课", "computer", True, 2, dept_cs.id),
            ("CS302", "计算机网络", 3, 48, 3, "必修", "主课", "multimedia", True, 2, dept_cs.id),
            ("CS401", "软件工程", 3, 48, 3, "必修", "主课", "multimedia", True, 2, dept_cs.id),
            ("MATH101", "高等数学", 5, 80, 5, "必修", "主课", "normal", True, 2, dept_math.id),
            ("MATH102", "线性代数", 2, 32, 2, "必修", "主课", "normal", True, 2, dept_math.id),
            ("ENG101", "大学英语", 4, 64, 4, "必修", "主课", "multimedia", True, 2, dept_eng.id),
            ("ENG201", "英语口语", 2, 32, 2, "选修", "副课", "normal", False, 1, dept_eng.id),
            ("PE101", "大学体育", 2, 32, 2, "必修", "副课", "normal", True, 2, dept_cs.id),
        ]
        for code, name, credit, hours, hpw, ctype, stype, rtype, consec, consec_sec, dept_id in courses:
            c = Course(
                course_code=code, name=name, credit=credit, total_hours=hours,
                hours_per_week=hpw, course_type=ctype, subject_type=stype,
                required_room_type=rtype, is_consecutive=consec,
                consecutive_sections=consec_sec, department_id=dept_id,
            )
            db.add(c)
        db.commit()

        # 8. 创建教学任务 (17个)
        print("初始化教学任务...")
        tasks = [
            # 课程id, 教师ids, 班级ids, 周学时
            (1, [1], [1, 2], 2),   # 计算机基础 - 张教授 - 计算机2401,2402 (多媒体合班)
            (2, [2], [1], 4),       # C语言 - 李娜 - 计算机2401 (单班，机房)
            (2, [3], [2], 4),       # C语言 - 王强 - 计算机2402 (单班，机房)
            (3, [1], [3], 3),       # 数据结构 - 张教授 - 软件2401 (单班，机房)
            (3, [2], [4], 3),       # 数据结构 - 李娜 - 软件2402 (单班，机房)
            (4, [4], [3], 3),       # 操作系统 - 刘芳 - 软件2401 (多媒体)
            (4, [5], [4], 3),       # 操作系统 - 陈明 - 软件2402 (多媒体)
            (5, [2], [1], 3),       # 数据库 - 李娜 - 计算机2401 (单班，机房)
            (5, [3], [2], 3),       # 数据库 - 王强 - 计算机2402 (单班，机房)
            (6, [3], [3, 4], 3),    # 计算机网络 - 王强 - 软件2401,2402 (多媒体合班)
            (7, [5], [3, 4], 3),    # 软件工程 - 陈明 - 软件2401,2402 (多媒体合班)
            (8, [6], [1, 2, 5], 5), # 高等数学 - 杨丽 - 计算机2401,2402 + 数学2401 (合班，普通教室)
            (9, [7], [1, 2, 5], 2), # 线性代数 - 赵磊 - 计算机2401,2402 + 数学2401 (合班，普通教室)
            (10, [8], [1, 2, 3, 4], 4), # 大学英语1组 - 黄静 - 计算机+软件班 (合班，多媒体)
            (10, [9], [5, 6], 4),   # 大学英语2组 - 周杰 - 数学2401+计算机2301 (合班，多媒体)
            (11, [9], [1, 2], 2),   # 英语口语 - 周杰 - 计算机2401,2402 (合班，普通教室)
            (12, [10], [1, 2], 2),  # 体育1组 - 吴敏 - 计算机2401,2402 (合班，普通教室)
            (12, [10], [3, 4], 2),  # 体育2组 - 吴敏 - 软件2401,2402 (合班，普通教室)
            (1, [1], [6], 2),       # 计算机基础 - 张教授 - 计算机2301 (多媒体)
        ]
        for i, (course_id, tids, cids, hpw) in enumerate(tasks, 1):
            task = TeachingTask(
                task_code=f"TASK{i:04d}",
                course_id=course_id,
                semester_id=semester.id,
                hours_per_week=hpw,
                priority=5 if i <= 10 else 3,
            )
            db.add(task)
            db.flush()

            for idx, tid in enumerate(tids):
                tt = TaskTeacher(task_id=task.id, teacher_id=tid, is_main=(idx == 0))
                db.add(tt)

            for cid in cids:
                tc = TaskClass(task_id=task.id, class_group_id=cid)
                db.add(tc)

        db.commit()

        print()
        print("=== 演示数据初始化完成！ ===")
        print(f"   - 节次：10 个")
        print(f"   - 院系：3 个")
        print(f"   - 专业：3 个")
        print(f"   - 学期：1 个")
        print(f"   - 教师：10 位")
        print(f"   - 教室：12 间")
        print(f"   - 班级：6 个")
        print(f"   - 课程：12 门")
        print(f"   - 教学任务：{len(tasks)} 个")
        print()
        print("现在可以打开 http://localhost:5173 查看效果")

    except Exception as e:
        db.rollback()
        print(f"初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # 先建表
    Base.metadata.create_all(bind=engine)
    init_data()

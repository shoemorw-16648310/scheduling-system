<template>
  <div class="page-container timetable-page">
    <div class="page-header">
      <div class="page-title">课表查询</div>
      <div style="display: flex; gap: 10px; align-items: center;">
        <el-select v-model="selectedSemester" placeholder="选择学期" style="width: 220px;" @change="loadEntries">
          <el-option v-for="s in semesterList" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-dropdown>
          <el-button type="success" :disabled="!selectedSemester || scheduleEntries.length === 0">
            <el-icon><Download /></el-icon>
            导出课表
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item disabled style="color: #909399; font-size: 12px;">── Excel 格式 ──</el-dropdown-item>
              <el-dropdown-item @click="handleExport('class', 'excel')">按班级导出（全部）</el-dropdown-item>
              <el-dropdown-item @click="handleExport('teacher', 'excel')">按教师导出（全部）</el-dropdown-item>
              <el-dropdown-item @click="handleExport('classroom', 'excel')">按教室导出（全部）</el-dropdown-item>
              <el-dropdown-item divided disabled style="color: #909399; font-size: 12px;">── PDF 格式 ──</el-dropdown-item>
              <el-dropdown-item @click="handleExport('class', 'pdf')">按班级导出（全部）</el-dropdown-item>
              <el-dropdown-item @click="handleExport('teacher', 'pdf')">按教师导出（全部）</el-dropdown-item>
              <el-dropdown-item @click="handleExport('classroom', 'pdf')">按教室导出（全部）</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-card">
      <el-row :gutter="16" align="middle">
        <el-col :span="4">
          <span class="filter-label">视图模式：</span>
          <el-radio-group v-model="viewType" size="default" @change="onViewTypeChange">
            <el-radio-button value="class">按班级</el-radio-button>
            <el-radio-button value="teacher">按教师</el-radio-button>
            <el-radio-button value="classroom">按教室</el-radio-button>
          </el-radio-group>
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="viewFilter"
            :placeholder="`选择${viewTypeLabel}`"
            filterable
            clearable
            style="width: 100%;"
            @change="loadEntries"
          >
            <el-option v-for="item in filterOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <span class="filter-label">每周天数：</span>
          <el-radio-group v-model="daysPerWeek" size="default">
            <el-radio-button :value="5">5天</el-radio-button>
            <el-radio-button :value="6">6天</el-radio-button>
            <el-radio-button :value="7">7天</el-radio-button>
          </el-radio-group>
        </el-col>
        <el-col :span="10" style="text-align: right;">
          <el-input
            v-model="keyword"
            placeholder="搜索课程/教师/班级/教室"
            clearable
            style="width: 280px;"
            :prefix-icon="Search"
          />
        </el-col>
      </el-row>
    </el-card>

    <!-- 课表网格 -->
    <el-card shadow="never" class="timetable-card">
      <div v-loading="entriesLoading" class="timetable-container">
        <div v-if="scheduleEntries.length === 0 && !entriesLoading" class="empty-tip">
          <el-empty description="暂无排课数据" />
        </div>

        <div v-else class="timetable-grid" :style="gridStyle">
          <!-- 表头：星期 -->
          <div class="grid-header grid-corner"></div>
          <div v-for="day in displayDays" :key="'h'+day" class="grid-header grid-day-header">
            {{ weekDayMap[day] }}
          </div>

          <!-- 节次行 -->
          <template v-for="section in sectionsPerDay" :key="'r'+section">
            <div class="grid-section-label">
              <div class="sec-num">第{{ section }}节</div>
              <div class="sec-time" v-if="timeSlots[section - 1]">
                {{ timeSlots[section - 1].start_time }}-{{ timeSlots[section - 1].end_time }}
              </div>
            </div>
            <div v-for="day in displayDays" :key="'c'+day+'-'+section" class="grid-cell">
              <div
                v-for="entry in getCellEntries(day, section)"
                :key="entry.id"
                class="course-card"
                :class="['subject-' + getSubjectType(entry)]"
                :style="{ '--card-span': entry.section_end - entry.section_start + 1 }"
                @click="showEntryDetail(entry)"
              >
                <div class="course-name">{{ entry.course_name }}</div>
                <div class="course-meta" v-if="viewType !== 'teacher'">{{ entry.teacher_names }}</div>
                <div class="course-meta" v-if="viewType !== 'class'">{{ entry.class_names }}</div>
                <div class="course-meta" v-if="viewType !== 'classroom'">{{ entry.classroom_name }}</div>
                <div class="course-weeks" v-if="entry.weeks && entry.weeks !== 'all'">
                  {{ formatWeeks(entry.weeks) }}
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 课节统计 -->
      <div v-if="scheduleEntries.length > 0" class="stats-bar">
        <el-tag type="info">共 {{ scheduleEntries.length }} 节课</el-tag>
        <el-tag type="success">已排 {{ uniqueCourses }} 门课程</el-tag>
        <el-tag type="warning">每周总课时 {{ totalHours }} 节</el-tag>
      </div>
    </el-card>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="课程详情" width="480px">
      <el-descriptions :column="1" border v-if="currentEntry">
        <el-descriptions-item label="课程名称">{{ currentEntry.course_name }}</el-descriptions-item>
        <el-descriptions-item label="授课教师">{{ currentEntry.teacher_names }}</el-descriptions-item>
        <el-descriptions-item label="授课班级">{{ currentEntry.class_names }}</el-descriptions-item>
        <el-descriptions-item label="上课时间">
          {{ weekDayMap[currentEntry.day_of_week] }} 第{{ currentEntry.section_start }}-{{ currentEntry.section_end }}节
        </el-descriptions-item>
        <el-descriptions-item label="上课教室">{{ currentEntry.classroom_name }}</el-descriptions-item>
        <el-descriptions-item label="周次">{{ formatWeeks(currentEntry.weeks) }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import { scheduleApi, semesterApi, teacherApi, classGroupApi, classroomApi, timeSlotApi } from '@/api'

const entriesLoading = ref(false)
const scheduleEntries = ref([])
const semesterList = ref([])
const selectedSemester = ref(null)
const timeSlots = ref([])

const viewType = ref('class')
const viewFilter = ref(null)
const daysPerWeek = ref(5)
const keyword = ref('')

const detailVisible = ref(false)
const currentEntry = ref(null)

const weekDayMap = { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日' }

const viewTypeLabel = computed(() => ({
  class: '班级', teacher: '教师', classroom: '教室',
}[viewType.value]))

const displayDays = computed(() => {
  const days = []
  for (let i = 1; i <= daysPerWeek.value; i++) days.push(i)
  return days
})

const sectionsPerDay = computed(() => timeSlots.value.length || 10)

const gridStyle = computed(() => ({
  gridTemplateColumns: `70px repeat(${daysPerWeek.value}, 1fr)`,
}))

const teacherList = ref([])
const classList = ref([])
const classroomList = ref([])

const filterOptions = computed(() => {
  if (viewType.value === 'teacher') return teacherList.value.map(t => ({ id: t.id, name: t.name }))
  if (viewType.value === 'class') return classList.value.map(c => ({ id: c.id, name: c.name }))
  return classroomList.value.map(c => ({ id: c.id, name: c.building + c.room_number }))
})

const uniqueCourses = computed(() => {
  const names = new Set(scheduleEntries.value.map(e => e.course_name).filter(Boolean))
  return names.size
})

const totalHours = computed(() => {
  return scheduleEntries.value.reduce((sum, e) => sum + (e.section_end - e.section_start + 1), 0)
})

// 过滤后的条目
const filteredEntries = computed(() => {
  let list = scheduleEntries.value
  if (keyword.value) {
    const kw = keyword.value.toLowerCase()
    list = list.filter(e =>
      (e.course_name && e.course_name.toLowerCase().includes(kw)) ||
      (e.teacher_names && e.teacher_names.toLowerCase().includes(kw)) ||
      (e.class_names && e.class_names.toLowerCase().includes(kw)) ||
      (e.classroom_name && e.classroom_name.toLowerCase().includes(kw))
    )
  }
  return list
})

const getCellEntries = (day, section) => {
  return filteredEntries.value.filter(e =>
    e.day_of_week === day && e.section_start === section
  )
}

const getSubjectType = (entry) => {
  if (!entry.course_name) return 'normal'
  const name = entry.course_name
  if (name.includes('数学') || name.includes('线代') || name.includes('高数') || name.includes('概率')) return 'math'
  if (name.includes('英语') || name.includes('语言') || name.includes('语文')) return 'language'
  if (name.includes('计算机') || name.includes('程序') || name.includes('数据') || name.includes('操作系统') || name.includes('数据库') || name.includes('网络') || name.includes('软件')) return 'cs'
  if (name.includes('体育')) return 'pe'
  if (name.includes('物理')) return 'physics'
  if (name.includes('化学') || name.includes('生物')) return 'science'
  return 'normal'
}

const formatWeeks = (weeks) => {
  if (!weeks || weeks === 'all') return '全周'
  return weeks
}

const showEntryDetail = (entry) => {
  currentEntry.value = entry
  detailVisible.value = true
}

const onViewTypeChange = () => {
  viewFilter.value = null
  loadEntries()
}

const loadSemesters = async () => {
  try {
    semesterList.value = await semesterApi.list()
    if (semesterList.value.length > 0 && !selectedSemester.value) {
      selectedSemester.value = semesterList.value[0].id
      loadEntries()
    }
  } catch (e) {}
}

const loadFilterOptions = async () => {
  try {
    const [teachers, classes, rooms] = await Promise.all([
      teacherApi.all(),
      classGroupApi.all(),
      classroomApi.all(),
    ])
    teacherList.value = teachers
    classList.value = classes
    classroomList.value = rooms
  } catch (e) {}
}

const loadTimeSlots = async () => {
  try {
    timeSlots.value = await timeSlotApi.list()
  } catch (e) {}
}

const loadEntries = async () => {
  if (!selectedSemester.value) return
  entriesLoading.value = true
  try {
    const params = { semester_id: selectedSemester.value }
    if (viewFilter.value) {
      if (viewType.value === 'teacher') params.teacher_id = viewFilter.value
      else if (viewType.value === 'class') params.class_id = viewFilter.value
      else if (viewType.value === 'classroom') params.classroom_id = viewFilter.value
    }
    scheduleEntries.value = await scheduleApi.entries(params)
  } catch (e) {} finally {
    entriesLoading.value = false
  }
}

const handleExport = (viewType, format) => {
  if (!selectedSemester.value) {
    ElMessage.warning('请先选择学期')
    return
  }
  const url = scheduleApi.exportUrl(selectedSemester.value, viewType, format)
  window.open(url, '_blank')
}

onMounted(() => {
  loadTimeSlots()
  loadFilterOptions()
  loadSemesters()
})
</script>

<style lang="scss" scoped>
.timetable-page {
  .filter-card {
    margin-bottom: 16px;

    :deep(.el-card__body) {
      padding: 16px 20px;
    }
  }

  .filter-label {
    font-size: 14px;
    color: #606266;
    margin-right: 8px;
  }

  .timetable-card {
    :deep(.el-card__body) {
      padding: 0;
    }
  }

  .timetable-container {
    min-height: 400px;
    padding: 16px;
  }

  .empty-tip {
    padding: 60px 0;
  }

  .timetable-grid {
    display: grid;
    gap: 2px;
    background: #ebeef5;
    border: 1px solid #ebeef5;

    .grid-header {
      background: #f5f7fa;
      padding: 10px 4px;
      text-align: center;
      font-weight: 600;
      font-size: 13px;
      color: #303133;
    }

    .grid-section-label {
      background: #f5f7fa;
      padding: 6px 4px;
      text-align: center;
      font-size: 12px;
      color: #606266;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;

      .sec-num {
        font-weight: 600;
      }

      .sec-time {
        font-size: 10px;
        color: #909399;
        margin-top: 2px;
      }
    }

    .grid-cell {
      background: #fff;
      min-height: 60px;
      padding: 2px;
      position: relative;
    }
  }

  .course-card {
    background: #ecf5ff;
    border-radius: 4px;
    padding: 6px 8px;
    font-size: 12px;
    cursor: pointer;
    height: calc(var(--card-span) * 60px + (var(--card-span) - 1) * 2px - 4px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    overflow: hidden;
    transition: all 0.2s;
    border-left: 3px solid #409eff;

    &:hover {
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      transform: translateY(-1px);
      z-index: 2;
    }

    .course-name {
      font-weight: 600;
      color: #303133;
      margin-bottom: 2px;
      line-height: 1.3;
    }

    .course-meta {
      color: #606266;
      font-size: 11px;
      line-height: 1.4;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .course-weeks {
      color: #909399;
      font-size: 10px;
      margin-top: 2px;
    }

    &.subject-math { background: #fef0f0; border-left-color: #f56c6c; }
    &.subject-language { background: #fdf6ec; border-left-color: #e6a23c; }
    &.subject-cs { background: #f0f9eb; border-left-color: #67c23a; }
    &.subject-pe { background: #ecf5ff; border-left-color: #409eff; }
    &.subject-physics { background: #f0f9ff; border-left-color: #36cfc9; }
    &.subject-science { background: #f9f0ff; border-left-color: #9254de; }
    &.subject-normal { background: #f4f4f5; border-left-color: #909399; }
  }

  .stats-bar {
    display: flex;
    gap: 12px;
    padding: 12px 20px;
    background: #fafafa;
    border-top: 1px solid #ebeef5;
  }
}
</style>

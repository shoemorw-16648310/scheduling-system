<template>
  <div class="page-container scheduler-page">
    <div class="page-header">
      <div class="page-title">排课中心</div>
      <div style="display: flex; gap: 10px; align-items: center;">
        <el-select v-model="selectedSemester" placeholder="选择学期" style="width: 220px;">
          <el-option v-for="s in semesterList" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button type="primary" @click="handleGenerate" :loading="isRunning" :disabled="!selectedSemester">
          <el-icon><MagicStick /></el-icon>
          {{ isRunning ? '排课中...' : '开始排课' }}
        </el-button>
      </div>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：配置面板 -->
      <el-col :span="5">
        <el-card shadow="never" class="config-panel">
          <template #header>
            <span style="font-weight: 600;">排课配置</span>
          </template>

          <div class="config-section">
            <div class="config-title">基本参数</div>
            <el-form label-width="90px" size="small">
              <el-form-item label="排课时长">
                <el-input-number v-model="config.time_limit_seconds" :min="10" :max="600" style="width: 100%;" />
                <span class="unit">秒</span>
              </el-form-item>
              <el-form-item label="每周天数">
                <el-radio-group v-model="config.days_per_week">
                  <el-radio :value="5">5天</el-radio>
                  <el-radio :value="6">6天</el-radio>
                  <el-radio :value="7">7天</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-form>
          </div>

          <el-divider />

          <div class="config-section">
            <div class="config-title">硬约束设置</div>
            <el-form label-width="110px" size="small">
              <el-form-item label="严格教室类型">
                <el-switch v-model="config.strict_room_type" />
                <span style="font-size: 12px; color: #909399; margin-left: 8px;">
                  类型不匹配时不降级
                </span>
              </el-form-item>
            </el-form>
          </div>

          <el-divider />

          <div class="config-section">
            <div class="config-title">约束权重</div>
            <div class="weight-list">
              <div class="weight-item" v-for="(item, key) in config.constraint_weights" :key="key">
                <span class="weight-label">{{ weightLabels[key] }}</span>
                <el-slider v-model="config.constraint_weights[key]" :min="0" :max="100" show-input size="small" />
              </div>
            </div>
          </div>

          <el-divider />

          <div class="config-section">
            <div class="config-title">排课结果</div>
            <div v-if="latestBatch" class="batch-info">
              <el-descriptions :column="1" size="small" border>
                <el-descriptions-item label="状态">
                  <el-tag :type="batchStatusType(latestBatch.status)" size="small">
                    {{ batchStatusText(latestBatch.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="批次号">
                  <div style="display:flex;align-items:center;gap:4px">
                    {{ latestBatch.batch_code }}
                    <el-tag v-if="latestBatch.is_current" type="success" size="small" effect="dark">当前</el-tag>
                  </div>
                </el-descriptions-item>
                <el-descriptions-item label="评分">{{ latestBatch.score || '-' }}</el-descriptions-item>
                <el-descriptions-item label="用时">
                  {{ latestBatch.started_at && latestBatch.finished_at
                    ? ((new Date(latestBatch.finished_at) - new Date(latestBatch.started_at)) / 1000).toFixed(1) + 's'
                    : '-' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
            <el-empty v-else description="暂无排课记录" :image-size="80" />
          </div>

          <el-divider />

          <div class="config-section">
            <div class="config-title">操作提示</div>
            <div class="tip-item">
              <el-icon><Mouse /></el-icon>
              <span>拖拽课节可调整时间</span>
            </div>
            <div class="tip-item">
              <el-icon><Edit /></el-icon>
              <span>点击课节可编辑详情</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：课表网格 -->
      <el-col :span="19">
        <el-tabs v-model="activeTab" class="scheduler-tabs">
          <el-tab-pane label="课表预览" name="timetable">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div style="font-weight: 600;">课表预览（拖拽可调课）</div>
              <div>
                <el-radio-group v-model="viewType" size="small">
                  <el-radio-button value="class">按班级</el-radio-button>
                  <el-radio-button value="teacher">按教师</el-radio-button>
                  <el-radio-button value="classroom">按教室</el-radio-button>
                </el-radio-group>
                <el-select v-model="viewFilter" placeholder="选择查看对象" size="small" style="margin-left: 10px; width: 180px;">
                  <el-option v-for="item in filterOptions" :key="item.id" :label="item.name" :value="item.id" />
                </el-select>
                <el-dropdown style="margin-left: 10px;">
                  <el-button type="success" size="small" :disabled="scheduleEntries.length === 0">
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
          </template>

          <div v-loading="entriesLoading" class="timetable-container">
            <div v-if="scheduleEntries.length === 0 && !entriesLoading" style="padding: 60px 0;">
              <el-empty description="暂无排课数据，请先执行排课" />
            </div>

            <!-- 课表网格 -->
            <div v-else class="timetable-grid">
              <!-- 表头：星期 -->
              <div class="grid-header grid-corner"></div>
              <div
                v-for="day in displayDays"
                :key="'h'+day"
                class="grid-header grid-day-header"
              >
                {{ weekDayMap[day] }}
              </div>

              <!-- 节次行 -->
              <template v-for="section in sectionsPerDay" :key="'r'+section">
                <div class="grid-section-label">
                  <div class="sec-num">第{{ section }}节</div>
                  <div class="sec-time" v-if="timeSlots[section - 1]">
                    {{ timeSlots[section - 1].start_time }}
                  </div>
                </div>
                <div
                  v-for="day in displayDays"
                  :key="'c'+day+'-'+section"
                  class="grid-cell"
                  :class="getDropCellClass(day, section)"
                  @dragover.prevent="onDragOver(day, section)"
                  @dragleave="onDragLeave(day, section)"
                  @drop="onDrop(day, section)"
                >
                  <div
                    v-for="entry in getCellEntries(day, section)"
                    :key="entry.id"
                    class="course-card"
                    :class="[
                      'subject-' + getSubjectType(entry),
                      {
                        'manual': entry.is_manual,
                        'dragging': draggingEntry?.id === entry.id,
                        'conflict-target': isConflictEntry(entry.id),
                      }
                    ]"
                    :style="{ '--card-span': entry.section_end - entry.section_start + 1 }"
                    draggable="true"
                    @dragstart="onDragStart(entry, day, section)"
                    @dragend="onDragEnd"
                    @click.stop="openEditDialog(entry)"
                    @mouseenter="hoveredEntry = entry.id"
                    @mouseleave="hoveredEntry = null"
                  >
                    <div class="course-name">{{ entry.course_name }}</div>
                    <div class="course-meta">{{ entry.teacher_names }}</div>
                    <div class="course-meta">{{ entry.classroom_name }}</div>
                    <div class="course-actions" v-if="hoveredEntry === entry.id">
                      <el-icon @click.stop="openEditDialog(entry)"><Edit /></el-icon>
                      <el-icon @click.stop="handleDelete(entry)"><Delete /></el-icon>
                    </div>
                    <div class="manual-badge" v-if="entry.is_manual">手动</div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </el-card>
          </el-tab-pane>

          <!-- Tab2：结果对比 -->
          <el-tab-pane label="结果对比" name="compare">
            <BatchCompare
              ref="batchCompareRef"
              :batches="allBatches"
              :semester-id="selectedSemester"
              @activated="onBatchActivated"
            />
          </el-tab-pane>
        </el-tabs>
      </el-col>
    </el-row>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="调整排课" width="500px">
      <el-form v-if="editingEntry" :model="editForm" label-width="100px">
        <el-form-item label="课程">
          <span>{{ editingEntry.course_name }}</span>
        </el-form-item>
        <el-form-item label="教师">
          <span>{{ editingEntry.teacher_names }}</span>
        </el-form-item>
        <el-form-item label="班级">
          <span>{{ editingEntry.class_names }}</span>
        </el-form-item>
        <el-form-item label="星期">
          <el-select v-model="editForm.day_of_week" style="width: 100%;">
            <el-option v-for="day in displayDays" :key="day" :label="weekDayMap[day]" :value="day" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始节次">
          <el-select v-model="editForm.section_start" style="width: 100%;" @change="onSectionStartChange">
            <el-option
              v-for="s in Math.max(1, sectionsPerDay - (editingEntry.section_end - editingEntry.section_start))"
              :key="s"
              :label="'第' + s + '节'"
              :value="s"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="结束节次">
          <span>第{{ editForm.section_end }}节</span>
        </el-form-item>
        <el-form-item label="教室">
          <el-select v-model="editForm.classroom_id" style="width: 100%;">
            <el-option
              v-for="room in classroomList"
              :key="room.id"
              :label="room.building + room.room_number + ' (' + room.room_no + ')'"
              :value="room.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveEdit" :loading="savingEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MagicStick, Mouse, Edit, Delete, Download } from '@element-plus/icons-vue'
import { scheduleApi, semesterApi, teacherApi, classGroupApi, classroomApi, timeSlotApi } from '@/api'
import BatchCompare from './components/BatchCompare.vue'

// ─── 基础数据 ──────────────────────────────────────
const selectedSemester = ref(null)
const semesterList = ref([])
const isRunning = ref(false)
const latestBatch = ref(null)
const allBatches = ref([])
const scheduleEntries = ref([])
const entriesLoading = ref(false)
const teacherList = ref([])
const classList = ref([])
const classroomList = ref([])
const timeSlots = ref([])
const activeTab = ref('timetable')
const batchCompareRef = ref(null)

const config = reactive({
  time_limit_seconds: 120,
  days_per_week: 5,
  strict_room_type: true,
  constraint_weights: {
    teacher_daily_hours: 50,
    teacher_consecutive: 30,
    uniform_distribution: 40,
    main_course_morning: 60,
    noon_break: 25,
    class_daily_hours: 20,
    room_balance: 15,
  },
})

const viewType = ref('class')
const viewFilter = ref(null)

const weekDayMap = { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日' }
const weightLabels = {
  teacher_daily_hours: '教师日课时上限',
  teacher_consecutive: '教师连堂限制',
  uniform_distribution: '课程均匀分布',
  main_course_morning: '主课上午优先',
  noon_break: '教师午休需求',
  class_daily_hours: '班级日课时均衡',
  room_balance: '教室使用均衡',
}

const displayDays = computed(() => {
  const days = []
  for (let i = 1; i <= config.days_per_week; i++) days.push(i)
  return days
})

const sectionsPerDay = computed(() => timeSlots.value.length || 10)

const filterOptions = computed(() => {
  if (viewType.value === 'teacher') return teacherList.value.map(t => ({ id: t.id, name: t.name }))
  if (viewType.value === 'class') return classList.value.map(c => ({ id: c.id, name: c.name }))
  return classroomList.value.map(c => ({ id: c.id, name: c.room_no }))
})

const batchStatusType = (status) => ({
  pending: 'info', running: 'warning', completed: 'success', failed: 'danger',
}[status] || 'info')

const batchStatusText = (status) => ({
  pending: '排队中', running: '排课中', completed: '已完成', failed: '失败',
}[status] || status)

// ─── 拖拽状态 ──────────────────────────────────────
const draggingEntry = ref(null)
const dragStartDay = ref(null)
const dragStartSection = ref(null)
const dropTargetDay = ref(null)
const dropTargetSection = ref(null)
const dropHasConflict = ref(false)
const dropConflictInfo = ref([])
const hoveredEntry = ref(null)

let conflictCheckTimer = null

const isDropTarget = (day, section) => {
  return dropTargetDay.value === day && dropTargetSection.value === section
}

const getDropCellClass = (day, section) => {
  if (!isDropTarget(day, section)) return ''
  return dropHasConflict.value ? 'drop-conflict' : 'drop-ok'
}

const isConflictEntry = (entryId) => {
  if (!dropHasConflict.value || !dropConflictInfo.value.length) return false
  return dropConflictInfo.value.some(c => c.entry_id === entryId)
}

// ─── 课表网格 ──────────────────────────────────────
const getCellEntries = (day, section) => {
  // 只返回从这个节次开始的课程（避免重复渲染多节课程）
  return scheduleEntries.value.filter(e =>
    e.day_of_week === day && e.section_start === section
  )
}

const getSubjectType = (entry) => {
  if (!entry.course_name) return 'normal'
  // 根据课程名简单分类颜色
  const name = entry.course_name
  if (name.includes('数学') || name.includes('线代') || name.includes('高数')) return 'math'
  if (name.includes('语言') || name.includes('英语')) return 'language'
  if (name.includes('计算机') || name.includes('程序') || name.includes('数据') || name.includes('操作系统') || name.includes('数据库') || name.includes('网络') || name.includes('软件')) return 'cs'
  if (name.includes('体育')) return 'pe'
  return 'normal'
}

// ─── 拖拽处理 ──────────────────────────────────────
const onDragStart = (entry, day, section) => {
  draggingEntry.value = entry
  dragStartDay.value = day
  dragStartSection.value = section
  dropHasConflict.value = false
  dropConflictInfo.value = []
}

const onDragOver = (day, section) => {
  if (!draggingEntry.value) return
  const entry = draggingEntry.value
  const span = entry.section_end - entry.section_start + 1
  if (section + span - 1 > sectionsPerDay.value) return

  dropTargetDay.value = day
  dropTargetSection.value = section

  // 原位置直接判定无冲突
  if (day === entry.day_of_week && section === entry.section_start) {
    dropHasConflict.value = false
    dropConflictInfo.value = []
    return
  }

  // 去抖调用冲突检测
  if (conflictCheckTimer) clearTimeout(conflictCheckTimer)
  conflictCheckTimer = setTimeout(async () => {
    if (!draggingEntry.value || dropTargetDay.value !== day || dropTargetSection.value !== section) return
    try {
      const res = await scheduleApi.checkMove({
        entry_id: entry.id,
        day_of_week: day,
        section_start: section,
        section_end: section + span - 1,
      })
      // 再次确认目标位置没变（用户可能已经移走了）
      if (dropTargetDay.value === day && dropTargetSection.value === section) {
        dropHasConflict.value = res.has_conflict
        dropConflictInfo.value = res.conflicts || []
      }
    } catch (e) {
      // 静默处理
    }
  }, 120)
}

const onDragLeave = (day, section) => {
  if (dropTargetDay.value === day && dropTargetSection.value === section) {
    dropTargetDay.value = null
    dropTargetSection.value = null
    dropHasConflict.value = false
    dropConflictInfo.value = []
  }
}

const onDragEnd = () => {
  draggingEntry.value = null
  dropTargetDay.value = null
  dropTargetSection.value = null
  dropHasConflict.value = false
  dropConflictInfo.value = []
  if (conflictCheckTimer) {
    clearTimeout(conflictCheckTimer)
    conflictCheckTimer = null
  }
}

const onDrop = async (day, section) => {
  if (!draggingEntry.value) return
  const entry = draggingEntry.value
  const span = entry.section_end - entry.section_start + 1
  const newEnd = section + span - 1

  if (newEnd > sectionsPerDay.value) {
    ElMessage.warning('超出每天节次范围')
    onDragEnd()
    return
  }

  if (day === entry.day_of_week && section === entry.section_start) {
    onDragEnd()
    return
  }

  // 有冲突时提示确认
  if (dropHasConflict.value && dropConflictInfo.value.length > 0) {
    const first = dropConflictInfo.value[0]
    try {
      await ElMessageBox.confirm(
        `检测到冲突：${first.course_name}（${first.types.map(t => ({teacher:'教师',class:'班级',classroom:'教室'}[t])).join('、')}冲突）\n是否仍要移动？`,
        '冲突提醒',
        { type: 'warning', confirmButtonText: '强制移动', cancelButtonText: '取消' }
      )
    } catch (e) {
      onDragEnd()
      return
    }
  }

  try {
    await scheduleApi.updateEntry(entry.id, {
      day_of_week: day,
      section_start: section,
      section_end: newEnd,
    })
    ElMessage.success('调课成功')
    loadEntries()
  } catch (e) {
    ElMessage.error('调课失败：' + (e.response?.data?.detail || e.message))
  }

  onDragEnd()
}

// ─── 编辑对话框 ────────────────────────────────────
const editDialogVisible = ref(false)
const editingEntry = ref(null)
const editForm = reactive({
  day_of_week: 1,
  section_start: 1,
  section_end: 2,
  classroom_id: null,
})
const savingEdit = ref(false)

const openEditDialog = (entry) => {
  editingEntry.value = entry
  editForm.day_of_week = entry.day_of_week
  editForm.section_start = entry.section_start
  editForm.section_end = entry.section_end
  editForm.classroom_id = entry.classroom_id
  editDialogVisible.value = true
}

const onSectionStartChange = (val) => {
  if (editingEntry.value) {
    const span = editingEntry.value.section_end - editingEntry.value.section_start + 1
    editForm.section_end = val + span - 1
  }
}

const saveEdit = async () => {
  if (!editingEntry.value) return
  savingEdit.value = true
  try {
    await scheduleApi.updateEntry(editingEntry.value.id, {
      day_of_week: editForm.day_of_week,
      section_start: editForm.section_start,
      section_end: editForm.section_end,
      classroom_id: editForm.classroom_id,
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    loadEntries()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.response?.data?.detail || e.message))
  } finally {
    savingEdit.value = false
  }
}

const handleDelete = async (entry) => {
  try {
    await ElMessageBox.confirm(`确定删除「${entry.course_name}」这条排课记录？`, '确认删除', {
      type: 'warning',
    })
    await scheduleApi.deleteEntry(entry.id)
    ElMessage.success('已删除')
    loadEntries()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleExport = (viewType, format = 'excel') => {
  if (!selectedSemester.value) {
    ElMessage.warning('请先选择学期')
    return
  }
  const url = scheduleApi.exportUrl(selectedSemester.value, viewType, format)
  window.open(url, '_blank')
}

// ─── 数据加载 ──────────────────────────────────────
const loadSemesters = async () => {
  try {
    semesterList.value = await semesterApi.list()
    if (semesterList.value.length > 0) {
      const active = semesterList.value.find(s => s.is_active)
      selectedSemester.value = active ? active.id : semesterList.value[0].id
    }
  } catch (e) {}
}

const loadOptions = async () => {
  try {
    const [t, c, r, ts] = await Promise.all([
      teacherApi.all(), classGroupApi.all(), classroomApi.all(), timeSlotApi.list(),
    ])
    teacherList.value = t
    classList.value = c
    classroomList.value = r
    timeSlots.value = ts
  } catch (e) {}
}

const loadBatches = async () => {
  if (!selectedSemester.value) return
  try {
    const batches = await scheduleApi.batches({ semester_id: selectedSemester.value })
    allBatches.value = batches
    latestBatch.value = batches[0] || null
  } catch (e) {}
}

const onBatchActivated = async (batchCode) => {
  // 刷新课表数据
  await loadEntries()
  // 切换到课表预览 Tab
  activeTab.value = 'timetable'
  ElMessage.success(`已切换到批次 ${batchCode}`)
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
  } finally {
    entriesLoading.value = false
  }
}

const handleGenerate = async () => {
  if (!selectedSemester.value) {
    ElMessage.warning('请先选择学期')
    return
  }
  isRunning.value = true
  try {
    const res = await scheduleApi.generate({
      semester_id: selectedSemester.value,
      time_limit_seconds: config.time_limit_seconds,
      days_per_week: config.days_per_week,
      strict_room_type: config.strict_room_type,
      constraint_weights: config.constraint_weights,
    })
    ElMessage.info('排课任务已提交，正在执行...')

    const batchCode = res.batch_code
    const poll = setInterval(async () => {
      try {
        const batch = await scheduleApi.getBatch(batchCode)
        latestBatch.value = batch
        if (batch.status === 'completed' || batch.status === 'failed') {
          clearInterval(poll)
          isRunning.value = false
          if (batch.status === 'completed') {
            ElMessage.success('排课完成！')
            loadBatches()
            loadEntries()
          } else {
            ElMessage.error('排课失败：' + (batch.message || '未知错误'))
          }
        }
      } catch (e) {
        clearInterval(poll)
        isRunning.value = false
      }
    }, 2000)
  } catch (e) {
    isRunning.value = false
  }
}

watch([viewType, viewFilter], () => {
  loadEntries()
})

watch(selectedSemester, () => {
  loadBatches()
  loadEntries()
})

onMounted(async () => {
  await loadSemesters()
  await loadOptions()
  // 默认选中第一个班级
  if (classList.value.length > 0) {
    viewFilter.value = classList.value[0].id
  }
  loadBatches()
  loadEntries()
})
</script>

<style lang="scss" scoped>
.scheduler-page {
  .config-panel {
    position: sticky;
    top: 0;

    .config-section {
      .config-title {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 12px;
      }
    }

    .weight-list {
      max-height: 320px;
      overflow-y: auto;
      padding-right: 4px;
    }

    .weight-item {
      margin-bottom: 12px;

      .weight-label {
        display: block;
        font-size: 12px;
        color: #606266;
        margin-bottom: 4px;
      }
    }

    .unit {
      margin-left: 6px;
      font-size: 12px;
      color: #909399;
    }

    .batch-info {
      font-size: 12px;
    }

    .tip-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: #606266;
      margin-bottom: 8px;
    }
  }

  .timetable-container {
    min-height: 500px;
    overflow-x: auto;
  }

  // ─── 课表网格 ──────────────────────────
  .timetable-grid {
    display: grid;
    grid-template-columns: 70px repeat(v-bind('config.days_per_week'), 1fr);
    gap: 1px;
    background: #e4e7ed;
    border: 1px solid #e4e7ed;
    min-width: 700px;

    .grid-header {
      background: #f5f7fa;
      padding: 10px 4px;
      text-align: center;
      font-weight: 600;
      font-size: 13px;
      color: #303133;
    }

    .grid-corner {
      background: #f5f7fa;
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
        color: #303133;
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
      transition: background 0.2s;

      &.drop-ok {
        background: #f0f9eb;
        outline: 2px dashed #67c23a;
        outline-offset: -2px;
      }

      &.drop-conflict {
        background: #fef0f0;
        outline: 2px dashed #f56c6c;
        outline-offset: -2px;
        animation: conflict-pulse 0.8s ease-in-out infinite;
      }
    }

    @keyframes conflict-pulse {
      0%, 100% { background: #fef0f0; }
      50% { background: #fde2e2; }
    }

    // ─── 课程卡片 ──────────────────────────
    .course-card {
      position: relative;
      padding: 6px 8px;
      border-radius: 4px;
      color: #fff;
      font-size: 12px;
      cursor: grab;
      user-select: none;
      transition: transform 0.15s, box-shadow 0.15s;
      height: calc(var(--card-span) * 60px - 4px);
      min-height: 56px;
      overflow: hidden;
      display: flex;
      flex-direction: column;

      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
      }

      &:active {
        cursor: grabbing;
      }

      &.dragging {
        opacity: 0.4;
      }

      &.conflict-target {
        border: 2px solid #f56c6c !important;
        box-shadow: 0 0 8px rgba(245, 108, 108, 0.5);
        animation: conflict-shake 0.5s ease-in-out infinite;
      }

      @keyframes conflict-shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-2px); }
        75% { transform: translateX(2px); }
      }

      &.manual {
        border: 2px solid #e6a23c;
      }

      .course-name {
        font-weight: 600;
        font-size: 13px;
        margin-bottom: 3px;
        line-height: 1.3;
      }

      .course-meta {
        font-size: 11px;
        opacity: 0.9;
        line-height: 1.4;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .course-actions {
        position: absolute;
        top: 4px;
        right: 4px;
        display: flex;
        gap: 4px;
        background: rgba(0, 0, 0, 0.3);
        padding: 2px 4px;
        border-radius: 4px;

        .el-icon {
          cursor: pointer;
          font-size: 14px;

          &:hover {
            color: #ffd04b;
          }
        }
      }

      .manual-badge {
        position: absolute;
        bottom: 2px;
        right: 4px;
        font-size: 10px;
        background: #e6a23c;
        padding: 1px 4px;
        border-radius: 2px;
      }

      // 课程类型颜色
      &.subject-cs { background: linear-gradient(135deg, #409eff, #66b1ff); }
      &.subject-math { background: linear-gradient(135deg, #67c23a, #85ce61); }
      &.subject-language { background: linear-gradient(135deg, #e6a23c, #ebb563); }
      &.subject-pe { background: linear-gradient(135deg, #f56c6c, #f78989); }
      &.subject-normal { background: linear-gradient(135deg, #909399, #a6a9ad); }
    }
  }
}
</style>

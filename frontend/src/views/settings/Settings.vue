<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">系统设置</div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <span style="font-weight: 600;">学期管理</span>
          </template>
          <el-button type="primary" size="small" @click="openSemesterDialog()" style="margin-bottom: 12px;">
            <el-icon><Plus /></el-icon>新增学期
          </el-button>
          <el-table :data="semesterList" border size="small">
            <el-table-column prop="name" label="学期名称" min-width="180" show-overflow-tooltip />
            <el-table-column prop="code" label="编码" width="120" />
            <el-table-column prop="total_weeks" label="周数" width="70" align="center" />
            <el-table-column label="当前学期" width="100" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.is_active"
                  :disabled="row.is_active"
                  size="small"
                  active-text="是"
                  @change="handleSetActive(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="130" align="center" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openSemesterDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="deleteSemester(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600;">节次配置</span>
              <el-button size="small" @click="initDefaultTimeSlots">恢复默认</el-button>
            </div>
          </template>
          <p style="color: #909399; font-size: 13px; margin-bottom: 12px;">
            配置每天的课程节次时间表，排课将按此时间安排。
          </p>
          <el-button type="primary" size="small" @click="openSlotDialog()" style="margin-bottom: 12px;">
            <el-icon><Plus /></el-icon>新增节次
          </el-button>
          <el-table :data="timeSlots" border size="small">
            <el-table-column prop="section" label="节次" width="70" align="center" />
            <el-table-column prop="name" label="名称" width="100" />
            <el-table-column label="时间段" width="150">
              <template #default="{ row }">{{ row.start_time }} - {{ row.end_time }}</template>
            </el-table-column>
            <el-table-column prop="period" label="时段" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" :type="periodType(row.period)">{{ periodLabel(row.period) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="110" align="center" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="openSlotDialog(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="deleteSlot(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 学期弹窗 -->
    <el-dialog v-model="showSemesterDialog" :title="semesterDialogTitle" width="480px" @close="resetSemesterForm">
      <el-form ref="semesterFormRef" :model="semesterForm" :rules="semesterRules" label-width="90px">
        <el-form-item label="学期名称" prop="name">
          <el-input v-model="semesterForm.name" placeholder="如：2024-2025学年第一学期" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="学期编码" prop="code">
          <el-input v-model="semesterForm.code" placeholder="如：2024-2025-1" />
        </el-form-item>
        <el-form-item label="开学日期" prop="start_date">
          <el-date-picker v-model="semesterForm.start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="结束日期" prop="end_date">
          <el-date-picker v-model="semesterForm.end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="总周数" prop="total_weeks">
          <el-input-number v-model="semesterForm.total_weeks" :min="1" :max="30" />
        </el-form-item>
        <el-form-item label="当前学期">
          <el-switch v-model="semesterForm.is_active" active-text="设为当前学期" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSemesterDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSemester" :loading="semesterSaving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 节次弹窗 -->
    <el-dialog v-model="showSlotDialog" :title="slotDialogTitle" width="420px" @close="resetSlotForm">
      <el-form ref="slotFormRef" :model="slotForm" :rules="slotRules" label-width="90px">
        <el-form-item label="节次号" prop="section">
          <el-input-number v-model="slotForm.section" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="slotForm.name" placeholder="如：第1节" />
        </el-form-item>
        <el-form-item label="开始时间" prop="start_time">
          <el-time-picker v-model="slotForm.start_time" format="HH:mm" value-format="HH:mm" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="结束时间" prop="end_time">
          <el-time-picker v-model="slotForm.end_time" format="HH:mm" value-format="HH:mm" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="时段" prop="period">
          <el-select v-model="slotForm.period" style="width: 100%;">
            <el-option label="上午" value="morning" />
            <el-option label="下午" value="afternoon" />
            <el-option label="晚上" value="evening" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSlotDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSlot" :loading="slotSaving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { semesterApi, timeSlotApi } from '@/api'

const semesterList = ref([])
const timeSlots = ref([])

// --- 学期管理 ---
const showSemesterDialog = ref(false)
const semesterFormRef = ref(null)
const semesterSaving = ref(false)
const semesterEditId = ref(null)
const semesterForm = reactive({
  name: '', code: '', start_date: '', end_date: '', total_weeks: 16, is_active: false,
})

const semesterDialogTitle = computed(() => semesterEditId.value ? '编辑学期' : '新增学期')

const semesterRules = {
  name: [{ required: true, message: '请输入学期名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入学期编码', trigger: 'blur' }],
  start_date: [{ required: true, message: '请选择开学日期', trigger: 'change' }],
  end_date: [{ required: true, message: '请选择结束日期', trigger: 'change' }],
  total_weeks: [{ required: true, message: '请输入总周数', trigger: 'blur' }],
}

const loadSemesters = async () => {
  try {
    semesterList.value = await semesterApi.list()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载学期列表失败')
  }
}

const openSemesterDialog = (row = null) => {
  semesterEditId.value = row ? row.id : null
  if (row) {
    Object.assign(semesterForm, {
      name: row.name,
      code: row.code,
      start_date: row.start_date,
      end_date: row.end_date,
      total_weeks: row.total_weeks,
      is_active: row.is_active,
    })
  } else {
    resetSemesterForm()
  }
  showSemesterDialog.value = true
}

const resetSemesterForm = () => {
  Object.assign(semesterForm, {
    name: '', code: '', start_date: '', end_date: '', total_weeks: 16, is_active: false,
  })
  semesterFormRef.value?.clearValidate()
}

const saveSemester = async () => {
  if (!semesterFormRef.value) return
  const valid = await semesterFormRef.value.validate().catch(() => false)
  if (!valid) return

  if (semesterForm.start_date && semesterForm.end_date && semesterForm.start_date >= semesterForm.end_date) {
    ElMessage.warning('结束日期必须晚于开学日期')
    return
  }

  semesterSaving.value = true
  try {
    if (semesterEditId.value) {
      await semesterApi.update(semesterEditId.value, semesterForm)
      ElMessage.success('修改成功')
    } else {
      await semesterApi.create(semesterForm)
      ElMessage.success('新增成功')
    }
    showSemesterDialog.value = false
    loadSemesters()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    semesterSaving.value = false
  }
}

const handleSetActive = async (row) => {
  try {
    await semesterApi.update(row.id, { is_active: true })
    ElMessage.success(`已将「${row.name}」设为当前学期`)
    loadSemesters()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '设置失败')
    // 回滚开关状态
    loadSemesters()
  }
}

const deleteSemester = (row) => {
  ElMessageBox.confirm(`确定删除学期「${row.name}」吗？`, '提示', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await semesterApi.delete(row.id)
      ElMessage.success('删除成功')
      loadSemesters()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }).catch(() => {})
}

// --- 节次配置 ---
const showSlotDialog = ref(false)
const slotFormRef = ref(null)
const slotSaving = ref(false)
const slotEditId = ref(null)
const slotForm = reactive({
  section: 1, name: '', start_time: '08:00', end_time: '08:45', period: 'morning',
})

const slotDialogTitle = computed(() => slotEditId.value ? '编辑节次' : '新增节次')

const slotRules = {
  section: [{ required: true, message: '请输入节次号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  start_time: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  end_time: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  period: [{ required: true, message: '请选择时段', trigger: 'change' }],
}

const periodLabel = (p) => ({ morning: '上午', afternoon: '下午', evening: '晚上' }[p] || p)
const periodType = (p) => ({ morning: 'success', afternoon: 'warning', evening: 'danger' }[p] || 'info')

const loadTimeSlots = async () => {
  try {
    timeSlots.value = await timeSlotApi.list()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '加载节次配置失败')
  }
}

const openSlotDialog = (row = null) => {
  slotEditId.value = row ? row.id : null
  if (row) {
    Object.assign(slotForm, {
      section: row.section,
      name: row.name,
      start_time: row.start_time,
      end_time: row.end_time,
      period: row.period,
    })
  } else {
    resetSlotForm()
  }
  showSlotDialog.value = true
}

const resetSlotForm = () => {
  Object.assign(slotForm, {
    section: timeSlots.value.length + 1,
    name: `第${timeSlots.value.length + 1}节`,
    start_time: '08:00',
    end_time: '08:45',
    period: 'morning',
  })
  slotFormRef.value?.clearValidate()
}

const saveSlot = async () => {
  if (!slotFormRef.value) return
  const valid = await slotFormRef.value.validate().catch(() => false)
  if (!valid) return

  if (slotForm.start_time >= slotForm.end_time) {
    ElMessage.warning('结束时间必须晚于开始时间')
    return
  }

  slotSaving.value = true
  try {
    if (slotEditId.value) {
      await timeSlotApi.update(slotEditId.value, slotForm)
      ElMessage.success('修改成功')
    } else {
      await timeSlotApi.create(slotForm)
      ElMessage.success('新增成功')
    }
    showSlotDialog.value = false
    loadTimeSlots()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  } finally {
    slotSaving.value = false
  }
}

const deleteSlot = (row) => {
  ElMessageBox.confirm(`确定删除第${row.section}节「${row.name}」吗？`, '提示', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      await timeSlotApi.delete(row.id)
      ElMessage.success('删除成功')
      loadTimeSlots()
    } catch (e) {
      ElMessage.error(e.response?.data?.detail || '删除失败')
    }
  }).catch(() => {})
}

const initDefaultTimeSlots = async () => {
  ElMessageBox.confirm('确定恢复默认节次配置吗？现有配置将被覆盖。', '提示', { type: 'warning' })
    .then(async () => {
      const defaultSlots = [
        { section: 1, name: '第1节', start_time: '08:00', end_time: '08:45', period: 'morning' },
        { section: 2, name: '第2节', start_time: '08:55', end_time: '09:40', period: 'morning' },
        { section: 3, name: '第3节', start_time: '10:00', end_time: '10:45', period: 'morning' },
        { section: 4, name: '第4节', start_time: '10:55', end_time: '11:40', period: 'morning' },
        { section: 5, name: '第5节', start_time: '14:00', end_time: '14:45', period: 'afternoon' },
        { section: 6, name: '第6节', start_time: '14:55', end_time: '15:40', period: 'afternoon' },
        { section: 7, name: '第7节', start_time: '16:00', end_time: '16:45', period: 'afternoon' },
        { section: 8, name: '第8节', start_time: '16:55', end_time: '17:40', period: 'afternoon' },
        { section: 9, name: '第9节', start_time: '19:00', end_time: '19:45', period: 'evening' },
        { section: 10, name: '第10节', start_time: '19:55', end_time: '20:40', period: 'evening' },
      ]
      try {
        await timeSlotApi.batchCreate(defaultSlots)
        ElMessage.success('恢复默认节次成功')
        loadTimeSlots()
      } catch (e) {
        ElMessage.error(e.response?.data?.detail || '恢复失败')
      }
    }).catch(() => {})
}

onMounted(() => {
  loadSemesters()
  loadTimeSlots()
})
</script>

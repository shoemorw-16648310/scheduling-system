<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">教师管理</div>
      <div style="display: flex; gap: 10px;">
        <el-button @click="downloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button type="success" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>新增教师
        </el-button>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchParams.keyword"
        placeholder="搜索姓名/工号"
        clearable
        style="width: 240px;"
        @keyup.enter="loadList"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="loadList">查询</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>

    <!-- 表格 -->
    <el-card shadow="never">
      <el-table :data="tableData.list" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="teacher_no" label="工号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="80" align="center" />
        <el-table-column prop="title" label="职称" width="100" />
        <el-table-column prop="max_hours_per_day" label="日最大课时" width="100" align="center" />
        <el-table-column prop="max_consecutive_hours" label="最大连堂" width="100" align="center" />
        <el-table-column prop="need_noon_break" label="午休需求" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.need_noon_break ? 'success' : 'info'" size="small">
              {{ row.need_noon_break ? '需要' : '不需要' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" width="130" />
        <el-table-column label="操作" width="200" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" size="small" @click="handleUnavailable(row)">禁排时间</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="searchParams.page"
          v-model:page-size="searchParams.page_size"
          :total="tableData.total"
          layout="total, sizes, prev, pager, next, jumper"
          :page-sizes="[10, 20, 50, 100]"
          @size-change="loadList"
          @current-change="loadList"
        />
      </div>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" label-width="100px" ref="formRef">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="工号" prop="teacher_no" :rules="[{ required: true, message: '请输入工号' }]">
              <el-input v-model="form.teacher_no" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="姓名" prop="name" :rules="[{ required: true, message: '请输入姓名' }]">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别">
              <el-select v-model="form.gender" placeholder="请选择" style="width: 100%;">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职称">
              <el-select v-model="form.title" placeholder="请选择" style="width: 100%;">
                <el-option label="教授" value="教授" />
                <el-option label="副教授" value="副教授" />
                <el-option label="讲师" value="讲师" />
                <el-option label="助教" value="助教" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="日最大课时">
              <el-input-number v-model="form.max_hours_per_day" :min="1" :max="12" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大连堂">
              <el-input-number v-model="form.max_consecutive_hours" :min="1" :max="8" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="午休需求">
              <el-switch v-model="form.need_noon_break" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="form.phone" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="邮箱">
              <el-input v-model="form.email" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 禁排时间弹窗 -->
    <el-dialog v-model="unavailableVisible" :title="`${currentTeacher?.name} - 禁排时间设置`" width="800px">
      <div class="unavailable-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>点击格点切换禁排状态（红色为禁排），可拖拽多选</span>
      </div>

      <div class="unavailable-grid">
        <div class="grid-header grid-corner"></div>
        <div v-for="day in weekDays" :key="'h'+day.value" class="grid-header">
          {{ day.label }}
        </div>

        <template v-for="slot in timeSlotList" :key="'r'+slot.section">
          <div class="grid-section-label">
            <div>第{{ slot.section }}节</div>
            <div class="sec-time">{{ slot.start_time }}</div>
          </div>
          <div
            v-for="day in weekDays"
            :key="'c'+day.value+'-'+slot.section"
            class="grid-cell"
            :class="{ 'unavailable': isUnavailable(day.value, slot.section), 'available': !isUnavailable(day.value, slot.section) }"
            @mousedown="startSelect(day.value, slot.section)"
            @mouseover="continueSelect(day.value, slot.section)"
            @mouseup="endSelect"
            @click="toggleUnavailable(day.value, slot.section)"
          >
            <el-icon v-if="isUnavailable(day.value, slot.section)" class="cell-icon"><Close /></el-icon>
          </div>
        </template>
      </div>

      <div style="margin-top: 16px; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <el-button size="small" @click="clearAllUnavailable">清空全部</el-button>
          <el-button size="small" @click="setAllUnavailable">全部禁排</el-button>
        </div>
        <div style="color: #909399; font-size: 12px;">
          当前禁排：{{ unavailableCount }} 个时段
        </div>
      </div>

      <template #footer>
        <el-button @click="unavailableVisible = false">取消</el-button>
        <el-button type="primary" @click="saveUnavailable" :loading="unavailableLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="批量导入教师" width="520px">
      <div class="import-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>请下载模板并按格式填写后上传，支持 .xlsx / .xls 格式</span>
      </div>
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip>
          <div class="el-upload__tip">仅支持 Excel 文件，单个文件不超过 10MB</div>
        </template>
      </el-upload>

      <div v-if="importResult" class="import-result">
        <el-alert :title="importResult.message" type="success" :closable="false" show-icon />
        <div v-if="importResult.failures && importResult.failures.length" class="fail-detail">
          <div class="fail-title">失败详情（前 {{ importResult.failures.length }} 条）：</div>
          <div v-for="(f, idx) in importResult.failures" :key="idx" class="fail-item">
            第 {{ f.row }} 行 - {{ f.name }}：{{ f.errors.join('、') }}
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="downloadTemplate">下载模板</el-button>
        <el-button @click="showImportDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleImport" :loading="importLoading" :disabled="!importFile">
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, InfoFilled, Close, Download, UploadFilled } from '@element-plus/icons-vue'
import { teacherApi, timeSlotApi } from '@/api'

const loading = ref(false)
const tableData = ref({ list: [], total: 0 })
const searchParams = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增教师')
const formRef = ref(null)
const editId = ref(null)
const form = reactive({
  teacher_no: '',
  name: '',
  gender: '',
  title: '',
  department_id: null,
  max_hours_per_day: 6,
  max_hours_per_week: 20,
  max_consecutive_hours: 4,
  need_noon_break: true,
  phone: '',
  email: '',
})

const weekDayMap = { 1: '周一', 2: '周二', 3: '周三', 4: '周四', 5: '周五', 6: '周六', 7: '周日' }
const weekDays = [
  { value: 1, label: '周一' },
  { value: 2, label: '周二' },
  { value: 3, label: '周三' },
  { value: 4, label: '周四' },
  { value: 5, label: '周五' },
  { value: 6, label: '周六' },
  { value: 7, label: '周日' },
]

const loadList = async () => {
  loading.value = true
  try {
    const res = await teacherApi.list(searchParams)
    tableData.value = res
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchParams.keyword = ''
  searchParams.page = 1
  loadList()
}

const handleAdd = () => {
  editId.value = null
  dialogTitle.value = '新增教师'
  Object.keys(form).forEach(k => {
    if (k === 'max_hours_per_day') form[k] = 6
    else if (k === 'max_hours_per_week') form[k] = 20
    else if (k === 'max_consecutive_hours') form[k] = 4
    else if (k === 'need_noon_break') form[k] = true
    else form[k] = ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editId.value = row.id
  dialogTitle.value = '编辑教师'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (editId.value) {
      await teacherApi.update(editId.value, form)
      ElMessage.success('修改成功')
    } else {
      await teacherApi.create(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
  } catch (e) {}
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除教师「${row.name}」吗？`, '提示', {
    type: 'warning',
  }).then(async () => {
    await teacherApi.delete(row.id)
    ElMessage.success('删除成功')
    loadList()
  }).catch(() => {})
}

// ---- 禁排时间（可视化网格） ----
const unavailableVisible = ref(false)
const unavailableLoading = ref(false)
const currentTeacher = ref(null)
const timeSlotList = ref([])
// 存储禁排的时段: Set<"day-section">
const unavailableSet = ref(new Set())
// 拖拽选择状态
const isSelecting = ref(false)
const selectMode = ref('add') // 'add' 或 'remove'
const startCell = ref(null)

const isUnavailable = (day, section) => {
  return unavailableSet.value.has(`${day}-${section}`)
}

const unavailableCount = computed(() => unavailableSet.value.size)

const handleUnavailable = async (row) => {
  currentTeacher.value = row
  // 加载节次配置
  if (timeSlotList.value.length === 0) {
    try {
      timeSlotList.value = await timeSlotApi.list()
    } catch (e) {}
  }
  // 加载已有禁排时间
  unavailableLoading.value = true
  try {
    const list = await teacherApi.getUnavailables(row.id)
    const set = new Set()
    for (const item of list) {
      for (let sec = item.section_start; sec <= item.section_end; sec++) {
        if (item.day_of_week === 0) {
          // day_of_week=0 表示每天
          for (let d = 1; d <= 7; d++) {
            set.add(`${d}-${sec}`)
          }
        } else {
          set.add(`${item.day_of_week}-${sec}`)
        }
      }
    }
    unavailableSet.value = set
  } finally {
    unavailableLoading.value = false
  }
  unavailableVisible.value = true
}

const toggleUnavailable = (day, section) => {
  const key = `${day}-${section}`
  const set = new Set(unavailableSet.value)
  if (set.has(key)) {
    set.delete(key)
  } else {
    set.add(key)
  }
  unavailableSet.value = set
}

const startSelect = (day, section) => {
  isSelecting.value = true
  startCell.value = { day, section }
  const key = `${day}-${section}`
  selectMode.value = unavailableSet.value.has(key) ? 'remove' : 'add'
}

const continueSelect = (day, section) => {
  if (!isSelecting.value || !startCell.value) return
  // 框选范围内的所有单元格
  const minDay = Math.min(startCell.value.day, day)
  const maxDay = Math.max(startCell.value.day, day)
  const minSec = Math.min(startCell.value.section, section)
  const maxSec = Math.max(startCell.value.section, section)

  const set = new Set(unavailableSet.value)
  for (let d = minDay; d <= maxDay; d++) {
    for (let s = minSec; s <= maxSec; s++) {
      const key = `${d}-${s}`
      if (selectMode.value === 'add') {
        set.add(key)
      } else {
        set.delete(key)
      }
    }
  }
  unavailableSet.value = set
}

const endSelect = () => {
  isSelecting.value = false
  startCell.value = null
}

const clearAllUnavailable = () => {
  unavailableSet.value = new Set()
}

const setAllUnavailable = () => {
  const set = new Set()
  for (let d = 1; d <= 7; d++) {
    for (const slot of timeSlotList.value) {
      set.add(`${d}-${slot.section}`)
    }
  }
  unavailableSet.value = set
}

const saveUnavailable = async () => {
  if (!currentTeacher.value) return
  unavailableLoading.value = true
  try {
    // 先删除所有旧的禁排记录
    const oldList = await teacherApi.getUnavailables(currentTeacher.value.id)
    for (const item of oldList) {
      await teacherApi.deleteUnavailable(item.id)
    }
    // 合并连续的节次，减少记录数
    const records = mergeUnavailableSlots(unavailableSet.value)
    for (const rec of records) {
      await teacherApi.addUnavailable(currentTeacher.value.id, {
        day_of_week: rec.day,
        section_start: rec.start,
        section_end: rec.end,
      })
    }
    ElMessage.success('保存成功')
    unavailableVisible.value = false
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    unavailableLoading.value = false
  }
}

// 合并连续的禁排时段
const mergeUnavailableSlots = (set) => {
  const records = []
  for (let day = 1; day <= 7; day++) {
    const sections = []
    for (const slot of timeSlotList.value) {
      if (set.has(`${day}-${slot.section}`)) {
        sections.push(slot.section)
      }
    }
    if (sections.length === 0) continue
    // 合并连续段
    sections.sort((a, b) => a - b)
    let start = sections[0]
    let end = sections[0]
    for (let i = 1; i < sections.length; i++) {
      if (sections[i] === end + 1) {
        end = sections[i]
      } else {
        records.push({ day, start, end })
        start = sections[i]
        end = sections[i]
      }
    }
    records.push({ day, start, end })
  }
  return records
}

// ---- 批量导入 ----
const showImportDialog = ref(false)
const importLoading = ref(false)
const importFile = ref(null)
const uploadRef = ref(null)
const importResult = ref(null)

const handleFileChange = (file) => {
  importFile.value = file.raw
  importResult.value = null
}

const handleFileRemove = () => {
  importFile.value = null
  importResult.value = null
}

const downloadTemplate = () => {
  window.open(teacherApi.templateUrl(), '_blank')
}

const handleImport = async () => {
  if (!importFile.value) return
  importLoading.value = true
  try {
    const res = await teacherApi.import(importFile.value)
    importResult.value = res
    ElMessage.success(res.message || '导入成功')
    loadList()
  } catch (e) {
    // 错误由拦截器提示
  } finally {
    importLoading.value = false
  }
}

onMounted(() => {
  loadList()
})
</script>

<style lang="scss" scoped>
.unavailable-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
  margin-bottom: 12px;
}

.unavailable-grid {
  display: grid;
  grid-template-columns: 70px repeat(7, 1fr);
  gap: 2px;
  background: #e4e7ed;
  border: 1px solid #e4e7ed;
  user-select: none;

  .grid-header {
    background: #f5f7fa;
    padding: 8px 4px;
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

    .sec-time {
      font-size: 10px;
      color: #909399;
      margin-top: 2px;
    }
  }

  .grid-cell {
    background: #fff;
    height: 36px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s;

    &:hover {
      outline: 2px solid #409eff;
      outline-offset: -2px;
    }

    &.unavailable {
      background: #fef0f0;

      .cell-icon {
        color: #f56c6c;
        font-size: 16px;
      }
    }

    &.available {
      background: #f0f9eb;
    }
  }
}

.import-tip {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
  margin-bottom: 16px;
}

.import-result {
  margin-top: 16px;

  .fail-detail {
    margin-top: 10px;
    max-height: 160px;
    overflow-y: auto;
    background: #fef0f0;
    border-radius: 4px;
    padding: 10px 12px;
    font-size: 12px;
  }

  .fail-title {
    font-weight: 600;
    color: #f56c6c;
    margin-bottom: 6px;
  }

  .fail-item {
    color: #606266;
    line-height: 1.8;
  }
}
</style>

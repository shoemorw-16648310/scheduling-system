<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">教学任务管理</div>
      <div style="display: flex; gap: 10px;">
        <el-select v-model="selectedSemester" placeholder="选择学期" style="width: 220px;" @change="loadList">
          <el-option v-for="s in semesterList" :key="s.id" :label="s.name" :value="s.id" />
        </el-select>
        <el-button @click="downloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button type="success" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>新增任务
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchParams.keyword"
        placeholder="搜索任务编码/课程名称"
        clearable
        style="width: 260px;"
        @keyup.enter="loadList"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-button type="primary" @click="loadList">查询</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="tableData.list" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="task_code" label="任务编码" width="160" />
        <el-table-column label="课程" min-width="180">
          <template #default="{ row }">
            {{ row.course?.name }}
            <el-tag size="small" type="info" style="margin-left: 6px;">{{ row.course?.course_code }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="授课教师" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="t in row.teachers" :key="t.id" size="small" style="margin-right: 4px; margin-bottom: 2px;">
              {{ t.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="授课班级" min-width="150">
          <template #default="{ row }">
            <el-tag v-for="c in row.classes" :key="c.id" size="small" type="success" style="margin-right: 4px; margin-bottom: 2px;">
              {{ c.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="hours_per_week" label="周学时" width="80" align="center" />
        <el-table-column prop="priority" label="优先级" width="80" align="center">
          <template #default="{ row }">
            <el-progress :percentage="row.priority * 10" :show-text="false" :stroke-width="6" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right" align="center">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="720px">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="课程">
              <el-select v-model="form.course_id" filterable placeholder="请选择课程" style="width: 100%;">
                <el-option v-for="c in courseList" :key="c.id" :label="`${c.name} (${c.course_code})`" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务编码">
              <el-input v-model="form.task_code" placeholder="可留空自动生成" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="授课教师">
              <el-select v-model="teacherIds" multiple filterable placeholder="请选择教师（首位为主讲）" style="width: 100%;">
                <el-option v-for="t in teacherList" :key="t.id" :label="`${t.name} (${t.teacher_no})`" :value="t.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="授课班级">
              <el-select v-model="classIds" multiple filterable placeholder="请选择班级" style="width: 100%;">
                <el-option v-for="c in classList" :key="c.id" :label="`${c.name} (${c.class_no})`" :value="c.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="周学时">
              <el-input-number v-model="form.hours_per_week" :min="1" :max="12" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="优先级">
              <el-input-number v-model="form.priority" :min="1" :max="10" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学生人数">
              <el-input-number v-model="form.student_count" :min="0" :max="500" style="width: 100%;" placeholder="留空按班级" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="批量导入教学任务" width="600px" :close-on-click-modal="false">
      <div class="import-tips">
        <el-icon><InfoFilled /></el-icon>
        <span>请先下载模板，按模板格式填写后上传。支持 .xlsx 格式。</span>
        <el-link type="primary" @click="downloadTemplate">下载导入模板</el-link>
      </div>

      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        accept=".xlsx,.xls"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将 Excel 文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">仅支持 .xlsx / .xls 格式文件</div>
        </template>
      </el-upload>

      <!-- 导入结果 -->
      <div v-if="importResult" class="import-result">
        <el-divider content-position="left">导入结果</el-divider>
        <div class="result-summary">
          <el-statistic title="成功" :value="importResult.success_count" value-color="#67c23a" />
          <el-statistic title="失败" :value="importResult.fail_count" value-color="#f56c6c" />
        </div>
        <div v-if="importResult.failures && importResult.failures.length > 0" class="failures-list">
          <div class="failures-title">失败明细（前50条）：</div>
          <el-table :data="importResult.failures" size="small" border max-height="240">
            <el-table-column prop="row" label="行号" width="70" align="center" />
            <el-table-column prop="course" label="课程" width="150" />
            <el-table-column label="错误信息">
              <template #default="{ row }">
                <div v-for="(e, i) in row.errors" :key="i" style="color: #f56c6c; font-size: 12px;">
                  • {{ e }}
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <template #footer>
        <el-button @click="closeImportDialog">关闭</el-button>
        <el-button
          type="primary"
          :disabled="!importFile"
          :loading="importLoading"
          @click="handleImport"
        >
          开始导入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, InfoFilled } from '@element-plus/icons-vue'
import { teachingTaskApi, semesterApi, courseApi, teacherApi, classGroupApi } from '@/api'

const loading = ref(false)
const tableData = ref({ list: [], total: 0 })
const searchParams = reactive({ page: 1, page_size: 20, keyword: '' })

const semesterList = ref([])
const selectedSemester = ref(null)
const courseList = ref([])
const teacherList = ref([])
const classList = ref([])

const dialogVisible = ref(false)
const dialogTitle = ref('新增教学任务')
const editId = ref(null)
const form = reactive({
  course_id: null, task_code: '', student_count: null,
  hours_per_week: 2, priority: 5, notes: '',
})
const teacherIds = ref([])
const classIds = ref([])

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
  window.open(teachingTaskApi.templateUrl(), '_blank')
}

const handleImport = async () => {
  if (!selectedSemester.value) {
    ElMessage.warning('请先选择学期')
    return
  }
  if (!importFile.value) return
  importLoading.value = true
  try {
    const res = await teachingTaskApi.import(selectedSemester.value, importFile.value)
    importResult.value = res
    ElMessage.success(res.message)
    if (res.success_count > 0) {
      loadList()
    }
  } catch (e) {
    // 错误由拦截器提示
  } finally {
    importLoading.value = false
  }
}

const closeImportDialog = () => {
  showImportDialog.value = false
  importFile.value = null
  importResult.value = null
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
}

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
    const [c, t, g] = await Promise.all([
      courseApi.all(),
      teacherApi.all(),
      classGroupApi.all(),
    ])
    courseList.value = c
    teacherList.value = t
    classList.value = g
  } catch (e) {}
}

const loadList = async () => {
  if (!selectedSemester.value) return
  loading.value = true
  try {
    const res = await teachingTaskApi.list({
      ...searchParams,
      semester_id: selectedSemester.value,
    })
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
  if (!selectedSemester.value) {
    ElMessage.warning('请先选择学期')
    return
  }
  editId.value = null
  dialogTitle.value = '新增教学任务'
  Object.assign(form, { course_id: null, task_code: '', student_count: null, hours_per_week: 2, priority: 5, notes: '' })
  teacherIds.value = []
  classIds.value = []
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editId.value = row.id
  dialogTitle.value = '编辑教学任务'
  Object.assign(form, row)
  teacherIds.value = row.teachers.map(t => t.id)
  classIds.value = row.classes.map(c => c.id)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    const payload = {
      ...form,
      semester_id: selectedSemester.value,
      teacher_ids: teacherIds.value,
      class_ids: classIds.value,
    }
    if (editId.value) {
      await teachingTaskApi.update(editId.value, payload)
      ElMessage.success('修改成功')
    } else {
      await teachingTaskApi.create(payload)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
  } catch (e) {}
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除该教学任务吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await teachingTaskApi.delete(row.id)
      ElMessage.success('删除成功')
      loadList()
    }).catch(() => {})
}

onMounted(async () => {
  await loadSemesters()
  await loadOptions()
  loadList()
})
</script>

<style lang="scss" scoped>
.import-tips {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #ecf5ff;
  color: #409eff;
  border-radius: 4px;
  font-size: 13px;
  margin-bottom: 16px;

  .el-icon {
    flex-shrink: 0;
  }

  .el-link {
    margin-left: auto;
  }
}

.import-result {
  margin-top: 16px;

  .result-summary {
    display: flex;
    gap: 40px;
    justify-content: center;
    padding: 16px 0;
  }

  .failures-title {
    font-size: 13px;
    color: #f56c6c;
    margin-bottom: 8px;
  }
}
</style>

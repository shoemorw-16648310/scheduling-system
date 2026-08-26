<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">课程管理</div>
      <div style="display: flex; gap: 10px;">
        <el-button @click="downloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button type="success" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>新增课程
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchParams.keyword"
        placeholder="搜索课程名称/代码"
        clearable
        style="width: 240px;"
        @keyup.enter="loadList"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="searchParams.course_type" placeholder="课程类型" clearable style="width: 120px;">
        <el-option label="必修" value="必修" />
        <el-option label="选修" value="选修" />
        <el-option label="公选" value="公选" />
      </el-select>
      <el-button type="primary" @click="loadList">查询</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="tableData.list" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="course_code" label="课程代码" width="140" />
        <el-table-column prop="name" label="课程名称" min-width="180" />
        <el-table-column prop="credit" label="学分" width="80" align="center" />
        <el-table-column prop="total_hours" label="总学时" width="90" align="center" />
        <el-table-column prop="hours_per_week" label="周学时" width="90" align="center" />
        <el-table-column prop="course_type" label="类型" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.course_type === '必修' ? 'danger' : row.course_type === '选修' ? 'primary' : 'info'">
              {{ row.course_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="subject_type" label="性质" width="90" align="center" />
        <el-table-column prop="is_consecutive" label="连堂" width="80" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_consecutive" type="success" size="small">{{ row.consecutive_sections }}节</el-tag>
            <span v-else>-</span>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="680px">
      <el-form :model="form" label-width="110px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="课程代码">
              <el-input v-model="form.course_code" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="课程名称">
              <el-input v-model="form.name" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学分">
              <el-input-number v-model="form.credit" :min="0" :max="10" :step="0.5" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="总学时">
              <el-input-number v-model="form.total_hours" :min="0" :max="200" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="周学时">
              <el-input-number v-model="form.hours_per_week" :min="1" :max="12" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="课程类型">
              <el-select v-model="form.course_type" style="width: 100%;">
                <el-option label="必修" value="必修" />
                <el-option label="选修" value="选修" />
                <el-option label="公选" value="公选" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="课程性质">
              <el-select v-model="form.subject_type" style="width: 100%;">
                <el-option label="主课" value="主课" />
                <el-option label="副课" value="副课" />
                <el-option label="实验" value="实验" />
                <el-option label="实践" value="实践" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="所需教室">
              <el-select v-model="form.required_room_type" style="width: 100%;">
                <el-option label="普通教室" value="normal" />
                <el-option label="多媒体" value="multimedia" />
                <el-option label="实验室" value="lab" />
                <el-option label="计算机房" value="computer" />
                <el-option label="艺术教室" value="arts" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="是否连堂">
              <el-switch v-model="form.is_consecutive" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="连堂节数">
              <el-input-number v-model="form.consecutive_sections" :min="2" :max="6" :disabled="!form.is_consecutive" style="width: 100%;" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="课程简介">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="批量导入课程" width="520px">
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
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled, Download, UploadFilled } from '@element-plus/icons-vue'
import { courseApi } from '@/api'

const loading = ref(false)
const tableData = ref({ list: [], total: 0 })
const searchParams = reactive({ page: 1, page_size: 20, keyword: '', course_type: '' })

const dialogVisible = ref(false)
const dialogTitle = ref('新增课程')
const editId = ref(null)
const form = reactive({
  course_code: '', name: '', credit: 2, total_hours: 32, hours_per_week: 2,
  course_type: '必修', subject_type: '主课', required_room_type: 'normal',
  is_consecutive: true, consecutive_sections: 2, description: '',
})

const loadList = async () => {
  loading.value = true
  try {
    const res = await courseApi.list(searchParams)
    tableData.value = res
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchParams.keyword = ''
  searchParams.course_type = ''
  searchParams.page = 1
  loadList()
}

const handleAdd = () => {
  editId.value = null
  dialogTitle.value = '新增课程'
  Object.assign(form, {
    course_code: '', name: '', credit: 2, total_hours: 32, hours_per_week: 2,
    course_type: '必修', subject_type: '主课', required_room_type: 'normal',
    is_consecutive: true, consecutive_sections: 2, description: '',
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editId.value = row.id
  dialogTitle.value = '编辑课程'
  Object.assign(form, row)
  form.credit = Number(form.credit)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (editId.value) {
      await courseApi.update(editId.value, form)
      ElMessage.success('修改成功')
    } else {
      await courseApi.create(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
  } catch (e) {}
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除课程「${row.name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await courseApi.delete(row.id)
      ElMessage.success('删除成功')
      loadList()
    }).catch(() => {})
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
  window.open(courseApi.templateUrl(), '_blank')
}

const handleImport = async () => {
  if (!importFile.value) return
  importLoading.value = true
  try {
    const res = await courseApi.import(importFile.value)
    importResult.value = res
    ElMessage.success(res.message || '导入成功')
    loadList()
  } catch (e) {} finally {
    importLoading.value = false
  }
}

onMounted(() => { loadList() })
</script>

<style lang="scss" scoped>
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

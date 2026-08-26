<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">教室管理</div>
      <div style="display: flex; gap: 10px;">
        <el-button @click="downloadTemplate">
          <el-icon><Download /></el-icon>下载模板
        </el-button>
        <el-button type="success" @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>批量导入
        </el-button>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>新增教室
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchParams.keyword"
        placeholder="搜索教室编号/教学楼"
        clearable
        style="width: 240px;"
        @keyup.enter="loadList"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-select v-model="searchParams.classroom_type" placeholder="教室类型" clearable style="width: 140px;">
        <el-option label="普通教室" value="normal" />
        <el-option label="多媒体教室" value="multimedia" />
        <el-option label="实验室" value="lab" />
        <el-option label="计算机房" value="computer" />
        <el-option label="艺术教室" value="arts" />
      </el-select>
      <el-select v-model="searchParams.campus" placeholder="校区" clearable filterable allow-create style="width: 140px;">
        <el-option v-for="c in campusOptions" :key="c" :label="c" :value="c" />
      </el-select>
      <el-button type="primary" @click="loadList">查询</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="tableData.list" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="room_no" label="教室编号" width="140" />
        <el-table-column prop="building" label="教学楼" width="120" />
        <el-table-column prop="room_number" label="房间号" width="100" />
        <el-table-column prop="capacity" label="容量" width="80" align="center" />
        <el-table-column prop="classroom_type" label="类型" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="typeTagMap[row.classroom_type]">{{ typeNameMap[row.classroom_type] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="campus" label="校区" width="100" />
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="教室编号">
              <el-input v-model="form.room_no" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教学楼">
              <el-input v-model="form.building" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="房间号">
              <el-input v-model="form.room_number" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="容纳人数">
              <el-input-number v-model="form.capacity" :min="0" :max="500" style="width: 100%;" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="教室类型">
              <el-select v-model="form.classroom_type" style="width: 100%;">
                <el-option label="普通教室" value="normal" />
                <el-option label="多媒体教室" value="multimedia" />
                <el-option label="实验室" value="lab" />
                <el-option label="计算机房" value="computer" />
                <el-option label="艺术教室" value="arts" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="校区">
              <el-select v-model="form.campus" placeholder="请选择或输入校区" filterable allow-create style="width: 100%;">
                <el-option v-for="c in campusOptions" :key="c" :label="c" :value="c" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="设备">
              <el-input v-model="form.equipment" type="textarea" :rows="2" placeholder="设备清单，如：投影仪、音响..." />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入弹窗 -->
    <el-dialog v-model="showImportDialog" title="批量导入教室" width="520px">
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
            第 {{ f.row }} 行 - {{ f.room_no }}：{{ f.errors.join('、') }}
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
import { classroomApi } from '@/api'

const loading = ref(false)
const tableData = ref({ list: [], total: 0 })
const searchParams = reactive({
  page: 1,
  page_size: 20,
  keyword: '',
  classroom_type: '',
  campus: '',
})

const dialogVisible = ref(false)
const dialogTitle = ref('新增教室')
const editId = ref(null)
const form = reactive({
  room_no: '',
  building: '',
  room_number: '',
  capacity: 50,
  classroom_type: 'normal',
  equipment: '',
  campus: '',
})

const typeNameMap = { normal: '普通教室', multimedia: '多媒体', lab: '实验室', computer: '计算机房', arts: '艺术教室' }
const typeTagMap = { normal: 'info', multimedia: 'primary', lab: 'warning', computer: 'success', arts: 'danger' }

// 校区选项
const campusOptions = ref([])

const loadCampusOptions = async () => {
  try {
    const res = await classroomApi.list({ page: 1, page_size: 200 })
    const campuses = new Set()
    res.list.forEach(r => { if (r.campus) campuses.add(r.campus) })
    campusOptions.value = Array.from(campuses)
  } catch (e) {}
}

const loadList = async () => {
  loading.value = true
  try {
    const res = await classroomApi.list(searchParams)
    tableData.value = res
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchParams.keyword = ''
  searchParams.classroom_type = ''
  searchParams.campus = ''
  searchParams.page = 1
  loadList()
}

const handleAdd = () => {
  editId.value = null
  dialogTitle.value = '新增教室'
  Object.assign(form, { room_no: '', building: '', room_number: '', capacity: 50, classroom_type: 'normal', equipment: '', campus: '' })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editId.value = row.id
  dialogTitle.value = '编辑教室'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (editId.value) {
      await classroomApi.update(editId.value, form)
      ElMessage.success('修改成功')
    } else {
      await classroomApi.create(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
    loadCampusOptions()
  } catch (e) {}
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除教室「${row.room_no}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await classroomApi.delete(row.id)
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
  window.open(classroomApi.templateUrl(), '_blank')
}

const handleImport = async () => {
  if (!importFile.value) return
  importLoading.value = true
  try {
    const res = await classroomApi.import(importFile.value)
    importResult.value = res
    ElMessage.success(res.message || '导入成功')
    loadList()
  } catch (e) {} finally {
    importLoading.value = false
  }
}

onMounted(() => {
  loadList()
  loadCampusOptions()
})
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

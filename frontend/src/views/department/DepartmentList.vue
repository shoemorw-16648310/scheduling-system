<template>
  <div class="page-container department-page">
    <div class="page-header">
      <div class="page-title">院系专业管理</div>
      <el-button type="primary" @click="handleAddDept">
        <el-icon><Plus /></el-icon>新增院系
      </el-button>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：院系列表 -->
      <el-col :span="8">
        <el-card shadow="never" class="dept-list-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600;">院系列表</span>
              <el-input
                v-model="deptKeyword"
                placeholder="搜索院系"
                size="small"
                clearable
                style="width: 180px;"
                :prefix-icon="Search"
              />
            </div>
          </template>

          <div class="dept-list" v-loading="deptLoading">
            <div
              v-for="dept in filteredDepts"
              :key="dept.id"
              class="dept-item"
              :class="{ active: currentDept?.id === dept.id }"
              @click="selectDept(dept)"
            >
              <div class="dept-info">
                <div class="dept-name">{{ dept.name }}</div>
                <div class="dept-code">编码：{{ dept.code }}</div>
              </div>
              <div class="dept-actions">
                <el-icon class="action-icon" @click.stop="handleEditDept(dept)"><Edit /></el-icon>
                <el-icon class="action-icon danger" @click.stop="handleDeleteDept(dept)"><Delete /></el-icon>
              </div>
            </div>
            <el-empty v-if="filteredDepts.length === 0 && !deptLoading" description="暂无院系" :image-size="80" />
          </div>
        </el-card>
      </el-col>

      <!-- 右侧：专业列表 -->
      <el-col :span="16">
        <el-card shadow="never">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600;">
                {{ currentDept ? currentDept.name + ' - 专业列表' : '请选择左侧院系' }}
              </span>
              <el-button
                type="primary"
                size="small"
                :disabled="!currentDept"
                @click="handleAddMajor"
              >
                <el-icon><Plus /></el-icon>新增专业
              </el-button>
            </div>
          </template>

          <el-table :data="majorList" v-loading="majorLoading" border stripe>
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="code" label="专业编码" width="160" />
            <el-table-column prop="name" label="专业名称" min-width="200" />
            <el-table-column label="操作" width="180" fixed="right" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleEditMajor(row)">编辑</el-button>
                <el-button link type="danger" size="small" @click="handleDeleteMajor(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>

          <el-empty v-if="!currentDept" description="请先选择左侧院系" :image-size="60" style="padding: 40px 0;" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 院系编辑弹窗 -->
    <el-dialog v-model="deptDialogVisible" :title="deptDialogTitle" width="420px">
      <el-form :model="deptForm" label-width="90px" ref="deptFormRef">
        <el-form-item label="院系编码" prop="code" :rules="[{ required: true, message: '请输入院系编码' }]">
          <el-input v-model="deptForm.code" placeholder="如：CS、MATH" />
        </el-form-item>
        <el-form-item label="院系名称" prop="name" :rules="[{ required: true, message: '请输入院系名称' }]">
          <el-input v-model="deptForm.name" placeholder="如：计算机学院" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deptDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitDept">确定</el-button>
      </template>
    </el-dialog>

    <!-- 专业编辑弹窗 -->
    <el-dialog v-model="majorDialogVisible" :title="majorDialogTitle" width="420px">
      <el-form :model="majorForm" label-width="90px" ref="majorFormRef">
        <el-form-item label="所属院系">
          <el-select v-model="majorForm.department_id" style="width: 100%;">
            <el-option v-for="d in deptList" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="专业编码" prop="code" :rules="[{ required: true, message: '请输入专业编码' }]">
          <el-input v-model="majorForm.code" placeholder="如：CS001" />
        </el-form-item>
        <el-form-item label="专业名称" prop="name" :rules="[{ required: true, message: '请输入专业名称' }]">
          <el-input v-model="majorForm.name" placeholder="如：计算机科学与技术" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="majorDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitMajor">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete } from '@element-plus/icons-vue'
import { departmentApi } from '@/api'

const deptLoading = ref(false)
const majorLoading = ref(false)
const deptList = ref([])
const majorList = ref([])
const currentDept = ref(null)
const deptKeyword = ref('')

const filteredDepts = computed(() => {
  if (!deptKeyword.value) return deptList.value
  const kw = deptKeyword.value.toLowerCase()
  return deptList.value.filter(d =>
    d.name.toLowerCase().includes(kw) || d.code.toLowerCase().includes(kw)
  )
})

// 院系弹窗
const deptDialogVisible = ref(false)
const deptDialogTitle = ref('新增院系')
const deptFormRef = ref(null)
const editDeptId = ref(null)
const deptForm = reactive({ name: '', code: '' })

// 专业弹窗
const majorDialogVisible = ref(false)
const majorDialogTitle = ref('新增专业')
const majorFormRef = ref(null)
const editMajorId = ref(null)
const majorForm = reactive({ name: '', code: '', department_id: null })

const loadDepts = async () => {
  deptLoading.value = true
  try {
    const res = await departmentApi.all()
    deptList.value = res
  } finally {
    deptLoading.value = false
  }
}

const selectDept = async (dept) => {
  currentDept.value = dept
  await loadMajors(dept.id)
}

const loadMajors = async (deptId) => {
  majorLoading.value = true
  try {
    majorList.value = await departmentApi.majors(deptId)
  } finally {
    majorLoading.value = false
  }
}

// ─── 院系操作 ───
const handleAddDept = () => {
  editDeptId.value = null
  deptDialogTitle.value = '新增院系'
  deptForm.name = ''
  deptForm.code = ''
  deptDialogVisible.value = true
}

const handleEditDept = (dept) => {
  editDeptId.value = dept.id
  deptDialogTitle.value = '编辑院系'
  deptForm.name = dept.name
  deptForm.code = dept.code
  deptDialogVisible.value = true
}

const handleSubmitDept = async () => {
  try {
    await deptFormRef.value.validate()
  } catch (e) {
    return
  }
  try {
    if (editDeptId.value) {
      await departmentApi.update(editDeptId.value, deptForm)
      ElMessage.success('修改成功')
    } else {
      await departmentApi.create(deptForm)
      ElMessage.success('新增成功')
    }
    deptDialogVisible.value = false
    loadDepts()
  } catch (e) {}
}

const handleDeleteDept = (dept) => {
  ElMessageBox.confirm(`确定删除院系「${dept.name}」吗？删除前请确保该院系下没有关联的教师、课程和班级。`, '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      await departmentApi.delete(dept.id)
      ElMessage.success('删除成功')
      if (currentDept.value?.id === dept.id) {
        currentDept.value = null
        majorList.value = []
      }
      loadDepts()
    } catch (e) {}
  }).catch(() => {})
}

// ─── 专业操作 ───
const handleAddMajor = () => {
  editMajorId.value = null
  majorDialogTitle.value = '新增专业'
  majorForm.name = ''
  majorForm.code = ''
  majorForm.department_id = currentDept.value?.id || null
  majorDialogVisible.value = true
}

const handleEditMajor = (major) => {
  editMajorId.value = major.id
  majorDialogTitle.value = '编辑专业'
  majorForm.name = major.name
  majorForm.code = major.code
  majorForm.department_id = major.department_id
  majorDialogVisible.value = true
}

const handleSubmitMajor = async () => {
  try {
    await majorFormRef.value.validate()
  } catch (e) {
    return
  }
  try {
    if (editMajorId.value) {
      await departmentApi.updateMajor(editMajorId.value, majorForm)
      ElMessage.success('修改成功')
    } else {
      await departmentApi.createMajor(majorForm)
      ElMessage.success('新增成功')
    }
    majorDialogVisible.value = false
    if (currentDept.value) loadMajors(currentDept.value.id)
  } catch (e) {}
}

const handleDeleteMajor = (major) => {
  ElMessageBox.confirm(`确定删除专业「${major.name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      try {
        await departmentApi.deleteMajor(major.id)
        ElMessage.success('删除成功')
        if (currentDept.value) loadMajors(currentDept.value.id)
      } catch (e) {}
    }).catch(() => {})
}

onMounted(() => {
  loadDepts()
})
</script>

<style lang="scss" scoped>
.department-page {
  .dept-list-card {
    height: calc(100vh - 180px);

    :deep(.el-card__body) {
      height: calc(100% - 57px);
      padding: 0;
      overflow-y: auto;
    }
  }

  .dept-list {
    padding: 8px;
  }

  .dept-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 14px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 4px;

    &:hover {
      background: #f5f7fa;
    }

    &.active {
      background: #ecf5ff;
      border-left: 3px solid #409eff;
      padding-left: 11px;
    }

    .dept-info {
      flex: 1;
      overflow: hidden;

      .dept-name {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 4px;
      }

      .dept-code {
        font-size: 12px;
        color: #909399;
      }
    }

    .dept-actions {
      display: none;
      gap: 8px;

      .action-icon {
        font-size: 14px;
        color: #909399;
        cursor: pointer;

        &:hover {
          color: #409eff;
        }

        &.danger:hover {
          color: #f56c6c;
        }
      }
    }

    &:hover .dept-actions {
      display: flex;
    }
  }
}
</style>

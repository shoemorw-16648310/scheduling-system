<template>
  <div class="page-container">
    <div class="page-header">
      <div class="page-title">班级管理</div>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>新增班级
      </el-button>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchParams.keyword"
        placeholder="搜索班级编号/名称"
        clearable
        style="width: 240px;"
        @keyup.enter="loadList"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-input v-model="searchParams.grade" placeholder="年级" clearable style="width: 120px;" />
      <el-select v-model="searchParams.campus" placeholder="校区" clearable style="width: 140px;" filterable allow-create>
        <el-option v-for="c in campusOptions" :key="c" :label="c" :value="c" />
      </el-select>
      <el-button type="primary" @click="loadList">查询</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>

    <el-card shadow="never">
      <el-table :data="tableData.list" v-loading="loading" border stripe>
        <el-table-column type="index" label="序号" width="60" align="center" />
        <el-table-column prop="class_no" label="班级编号" width="140" />
        <el-table-column prop="name" label="班级名称" width="160" />
        <el-table-column prop="grade" label="年级" width="100" align="center" />
        <el-table-column prop="campus" label="校区" width="100" />
        <el-table-column prop="student_count" label="人数" width="80" align="center" />
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="班级编号">
          <el-input v-model="form.class_no" />
        </el-form-item>
        <el-form-item label="班级名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="年级">
          <el-input v-model="form.grade" placeholder="如：2024" />
        </el-form-item>
        <el-form-item label="校区">
          <el-select v-model="form.campus" placeholder="请选择或输入校区" filterable allow-create style="width: 100%;">
            <el-option v-for="c in campusOptions" :key="c" :label="c" :value="c" />
          </el-select>
        </el-form-item>
        <el-form-item label="学生人数">
          <el-input-number v-model="form.student_count" :min="0" :max="500" style="width: 100%;" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { classGroupApi, classroomApi } from '@/api'

const loading = ref(false)
const tableData = ref({ list: [], total: 0 })
const searchParams = reactive({ page: 1, page_size: 20, keyword: '', grade: '', campus: '' })

const dialogVisible = ref(false)
const dialogTitle = ref('新增班级')
const editId = ref(null)
const form = reactive({ class_no: '', name: '', grade: '', campus: '', student_count: 30 })

// 校区选项（从教室和班级中收集）
const campusOptions = ref([])

const loadCampusOptions = async () => {
  try {
    const [classRes, roomRes] = await Promise.all([
      classGroupApi.list({ page: 1, page_size: 200 }),
      classroomApi.list({ page: 1, page_size: 200 }),
    ])
    const campuses = new Set()
    classRes.list.forEach(c => { if (c.campus) campuses.add(c.campus) })
    roomRes.list.forEach(r => { if (r.campus) campuses.add(r.campus) })
    campusOptions.value = Array.from(campuses)
  } catch (e) {}
}

const loadList = async () => {
  loading.value = true
  try {
    const params = { ...searchParams }
    if (!params.campus) delete params.campus
    const res = await classGroupApi.list(params)
    tableData.value = res
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  searchParams.keyword = ''
  searchParams.grade = ''
  searchParams.campus = ''
  searchParams.page = 1
  loadList()
}

const handleAdd = () => {
  editId.value = null
  dialogTitle.value = '新增班级'
  Object.assign(form, { class_no: '', name: '', grade: '', campus: '', student_count: 30 })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editId.value = row.id
  dialogTitle.value = '编辑班级'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  try {
    if (editId.value) {
      await classGroupApi.update(editId.value, form)
      ElMessage.success('修改成功')
    } else {
      await classGroupApi.create(form)
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadList()
    loadCampusOptions()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '保存失败')
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定删除班级「${row.name}」吗？`, '提示', { type: 'warning' })
    .then(async () => {
      await classGroupApi.delete(row.id)
      ElMessage.success('删除成功')
      loadList()
    }).catch(() => {})
}

onMounted(() => {
  loadList()
  loadCampusOptions()
})
</script>

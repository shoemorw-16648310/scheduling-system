import request from './request'

// 认证
export const authApi = {
  login: (username, password) => {
    const form = new FormData()
    form.append('username', username)
    form.append('password', password)
    return request.post('/auth/login', form)
  },
  getMe: () => request.get('/auth/me'),
  register: (data) => request.post('/auth/register', data),
  changePassword: (oldPassword, newPassword) =>
    request.post('/auth/change-password', null, { params: { old_password: oldPassword, new_password: newPassword } }),
}

// 院系
export const departmentApi = {
  list: (params) => request.get('/departments', { params }),
  all: () => request.get('/departments/all'),
  get: (id) => request.get(`/departments/${id}`),
  create: (data) => request.post('/departments', data),
  update: (id, data) => request.put(`/departments/${id}`, data),
  delete: (id) => request.delete(`/departments/${id}`),
  // 专业
  majors: (deptId) => request.get(`/departments/${deptId}/majors`),
  allMajors: () => request.get('/departments/majors/all'),
  createMajor: (data) => request.post('/departments/majors', data),
  updateMajor: (id, data) => request.put(`/departments/majors/${id}`, data),
  deleteMajor: (id) => request.delete(`/departments/majors/${id}`),
}

// 教师
export const teacherApi = {
  list: (params) => request.get('/teachers', { params }),
  all: () => request.get('/teachers/all'),
  get: (id) => request.get(`/teachers/${id}`),
  create: (data) => request.post('/teachers', data),
  update: (id, data) => request.put(`/teachers/${id}`, data),
  delete: (id) => request.delete(`/teachers/${id}`),
  // 不可用时间
  getUnavailables: (teacherId) => request.get(`/teachers/${teacherId}/unavailables`),
  addUnavailable: (teacherId, data) => request.post(`/teachers/${teacherId}/unavailables`, data),
  updateUnavailable: (id, data) => request.put(`/teachers/unavailables/${id}`, data),
  deleteUnavailable: (id) => request.delete(`/teachers/unavailables/${id}`),
  // 批量导入
  import: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request.post('/import/teachers', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  templateUrl: () =>
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/import/template/teachers`,
}

// 教室
export const classroomApi = {
  list: (params) => request.get('/classrooms', { params }),
  all: () => request.get('/classrooms/all'),
  get: (id) => request.get(`/classrooms/${id}`),
  create: (data) => request.post('/classrooms', data),
  update: (id, data) => request.put(`/classrooms/${id}`, data),
  delete: (id) => request.delete(`/classrooms/${id}`),
  // 批量导入
  import: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request.post('/import/classrooms', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  templateUrl: () =>
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/import/template/classrooms`,
}

// 班级
export const classGroupApi = {
  list: (params) => request.get('/class-groups', { params }),
  all: () => request.get('/class-groups/all'),
  get: (id) => request.get(`/class-groups/${id}`),
  create: (data) => request.post('/class-groups', data),
  update: (id, data) => request.put(`/class-groups/${id}`, data),
  delete: (id) => request.delete(`/class-groups/${id}`),
}

// 课程
export const courseApi = {
  list: (params) => request.get('/courses', { params }),
  all: () => request.get('/courses/all'),
  get: (id) => request.get(`/courses/${id}`),
  create: (data) => request.post('/courses', data),
  update: (id, data) => request.put(`/courses/${id}`, data),
  delete: (id) => request.delete(`/courses/${id}`),
  // 批量导入
  import: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request.post('/import/courses', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  templateUrl: () =>
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/import/template/courses`,
}

// 教学任务
export const teachingTaskApi = {
  list: (params) => request.get('/teaching-tasks', { params }),
  get: (id) => request.get(`/teaching-tasks/${id}`),
  create: (data) => request.post('/teaching-tasks', data),
  update: (id, data) => request.put(`/teaching-tasks/${id}`, data),
  delete: (id) => request.delete(`/teaching-tasks/${id}`),
  // 批量导入
  import: (semesterId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request.post(`/import/teaching-tasks?semester_id=${semesterId}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  // 下载模板
  templateUrl: () =>
    `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/import/template/teaching-tasks`,
}

// 学期
export const semesterApi = {
  list: () => request.get('/semesters'),
  get: (id) => request.get(`/semesters/${id}`),
  create: (data) => request.post('/semesters', data),
  update: (id, data) => request.put(`/semesters/${id}`, data),
  delete: (id) => request.delete(`/semesters/${id}`),
}

// 节次
export const timeSlotApi = {
  list: () => request.get('/time-slots'),
  get: (id) => request.get(`/time-slots/${id}`),
  create: (data) => request.post('/time-slots', data),
  update: (id, data) => request.put(`/time-slots/${id}`, data),
  delete: (id) => request.delete(`/time-slots/${id}`),
  batchCreate: (data) => request.post('/time-slots/batch', data),
}

// 排课
export const scheduleApi = {
  generate: (data) => request.post('/schedule/generate', data),
  batches: (params) => request.get('/schedule/batches', { params }),
  getBatch: (batchCode) => request.get(`/schedule/batches/${batchCode}`),
  entries: (params) => request.get('/schedule/entries', { params }),
  updateEntry: (id, data) => request.put(`/schedule/entries/${id}`, data),
  deleteEntry: (id) => request.delete(`/schedule/entries/${id}`),
  conflicts: (params) => request.get('/schedule/conflicts', { params }),
  checkMove: (params) => request.get('/schedule/check-move', { params }),
  reset: (semesterId) => request.post('/schedule/reset', null, { params: { semester_id: semesterId } }),
  stats: (params) => request.get('/schedule/stats', { params }),
  exportUrl: (semesterId, viewType, format = 'excel') => {
    const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    if (format === 'pdf') {
      return `${base}/export/schedule/pdf?semester_id=${semesterId}&view_type=${viewType}`
    }
    return `${base}/export/schedule?semester_id=${semesterId}&view_type=${viewType}`
  },
  // 评分明细与对比
  getScoreDetail: (batchCode) => request.get(`/schedule/batches/${batchCode}/score-detail`),
  compareBatches: (batchCodes) => request.get('/schedule/compare', { params: { batch_codes: batchCodes.join(',') } }),
  activateBatch: (batchCode) => request.post(`/schedule/batches/${batchCode}/activate`),
}

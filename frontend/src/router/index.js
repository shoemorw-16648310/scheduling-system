import { createRouter, createWebHistory } from 'vue-router'
import Layout from '@/views/layout/Layout.vue'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '首页概览', icon: 'HomeFilled' },
      },
      {
        path: 'teachers',
        name: 'Teachers',
        component: () => import('@/views/teacher/TeacherList.vue'),
        meta: { title: '教师管理', icon: 'User' },
      },
      {
        path: 'departments',
        name: 'Departments',
        component: () => import('@/views/department/DepartmentList.vue'),
        meta: { title: '院系专业', icon: 'OfficeBuilding' },
      },
      {
        path: 'classrooms',
        name: 'Classrooms',
        component: () => import('@/views/classroom/ClassroomList.vue'),
        meta: { title: '教室管理', icon: 'OfficeBuilding' },
      },
      {
        path: 'class-groups',
        name: 'ClassGroups',
        component: () => import('@/views/class-group/ClassGroupList.vue'),
        meta: { title: '班级管理', icon: 'Avatar' },
      },
      {
        path: 'courses',
        name: 'Courses',
        component: () => import('@/views/course/CourseList.vue'),
        meta: { title: '课程管理', icon: 'Reading' },
      },
      {
        path: 'teaching-tasks',
        name: 'TeachingTasks',
        component: () => import('@/views/teaching-task/TeachingTaskList.vue'),
        meta: { title: '教学任务', icon: 'Notebook' },
      },
      {
        path: 'scheduler',
        name: 'Scheduler',
        component: () => import('@/views/scheduler/Scheduler.vue'),
        meta: { title: '排课中心', icon: 'Calendar' },
      },
      {
        path: 'timetable',
        name: 'Timetable',
        component: () => import('@/views/timetable/TimetableView.vue'),
        meta: { title: '课表查询', icon: 'Tickets' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/settings/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const userStore = useUserStore()
  const hasToken = !!userStore.token

  if (to.meta.public) {
    // 公开页面，已登录则跳首页
    if (hasToken && to.path === '/login') {
      next('/')
    } else {
      next()
    }
  } else {
    // 需要登录
    if (!hasToken) {
      next({ path: '/login', query: { redirect: to.fullPath } })
    } else {
      next()
    }
  }
})

// 设置页面标题
router.afterEach((to) => {
  const title = to.meta?.title
  if (title) {
    document.title = `${title} - 自动排课系统`
  } else {
    document.title = '自动排课系统'
  }
})

export default router

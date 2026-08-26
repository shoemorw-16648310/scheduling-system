<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <el-icon :size="24" color="#409eff"><Calendar /></el-icon>
        <span class="logo-text">排课系统</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="#b9c0cc"
        active-text-color="#ffffff"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleUserCommand">
            <span class="user-info">
              <el-avatar :size="28" icon="UserFilled" />
              <span class="username">{{ userStore.displayName }}</span>
              <el-icon><CaretBottom /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人信息
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <el-icon><Lock /></el-icon>修改密码
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>

  <!-- 修改密码弹窗 -->
  <el-dialog v-model="showPasswordDialog" title="修改密码" width="420px">
    <el-form
      :model="passwordForm"
      :rules="passwordRules"
      ref="passwordFormRef"
      label-width="100px"
    >
      <el-form-item label="原密码" prop="old_password">
        <el-input v-model="passwordForm.old_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="passwordForm.new_password" type="password" show-password />
      </el-form-item>
      <el-form-item label="确认新密码" prop="confirm_password">
        <el-input v-model="passwordForm.confirm_password" type="password" show-password />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="showPasswordDialog = false">取消</el-button>
      <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const menuItems = [
  { path: '/dashboard', title: '首页概览', icon: 'HomeFilled' },
  { path: '/timetable', title: '课表查询', icon: 'Tickets' },
  { path: '/departments', title: '院系专业', icon: 'OfficeBuilding' },
  { path: '/teachers', title: '教师管理', icon: 'User' },
  { path: '/classrooms', title: '教室管理', icon: 'School' },
  { path: '/class-groups', title: '班级管理', icon: 'Avatar' },
  { path: '/courses', title: '课程管理', icon: 'Reading' },
  { path: '/teaching-tasks', title: '教学任务', icon: 'Notebook' },
  { path: '/scheduler', title: '排课中心', icon: 'Calendar' },
  { path: '/settings', title: '系统设置', icon: 'Setting' },
]

const activeMenu = computed(() => route.path)
const currentTitle = computed(() => route.meta?.title || '')

// 启动时拉取最新用户信息
onMounted(() => {
  if (userStore.isLoggedIn) {
    userStore.fetchUserInfo().catch(() => {
      router.push('/login')
    })
  }
})

const handleUserCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      type: 'warning',
      confirmButtonText: '退出',
    }).then(() => {
      userStore.logout()
      ElMessage.success('已退出登录')
      router.push('/login')
    }).catch(() => {})
  } else if (command === 'password') {
    showPasswordDialog.value = true
  } else if (command === 'profile') {
    ElMessage.info('个人信息页开发中')
  }
}

// 修改密码弹窗
const showPasswordDialog = ref(false)
const passwordLoading = ref(false)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const validateConfirmPwd = (_rule, value, callback) => {
  if (value !== passwordForm.value.new_password) {
    callback(new Error('两次输入的新密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPwd, trigger: 'blur' },
  ],
}

const passwordFormRef = ref(null)

const handleChangePassword = async () => {
  try {
    await passwordFormRef.value.validate()
  } catch (e) {
    return
  }
  passwordLoading.value = true
  try {
    await authApi.changePassword(passwordForm.value.old_password, passwordForm.value.new_password)
    ElMessage.success('密码修改成功，请重新登录')
    showPasswordDialog.value = false
    userStore.logout()
    router.push('/login')
  } catch (e) {
    // 错误由拦截器提示
  } finally {
    passwordLoading.value = false
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #001529;
  display: flex;
  flex-direction: column;

  .logo {
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    color: #fff;
    font-size: 18px;
    font-weight: 600;
    border-bottom: 1px solid #1f2d3d;

    .logo-text {
      background: linear-gradient(90deg, #409eff, #67c23a);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }

  :deep(.el-menu) {
    border-right: none;
  }
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e8eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;

      .username {
        font-size: 14px;
        color: #303133;
      }
    }
  }
}

.main-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>

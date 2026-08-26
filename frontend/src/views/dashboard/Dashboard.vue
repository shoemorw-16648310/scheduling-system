<template>
  <div class="dashboard">
    <!-- 顶部统计卡片 -->
    <el-row :gutter="16">
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-blue">
              <el-icon :size="26"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">教师总数</div>
              <div class="stat-value">{{ stats.total_teachers || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-green">
              <el-icon :size="26"><School /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">教室总数</div>
              <div class="stat-value">{{ stats.total_classrooms || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-orange">
              <el-icon :size="26"><Reading /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">课程总数</div>
              <div class="stat-value">{{ stats.total_courses || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-red">
              <el-icon :size="26"><Avatar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">班级总数</div>
              <div class="stat-value">{{ stats.total_classes || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-purple">
              <el-icon :size="26"><Notebook /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">教学任务</div>
              <div class="stat-value">{{ stats.total_tasks || 0 }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon icon-cyan">
              <el-icon :size="26"><OfficeBuilding /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-label">院系数量</div>
              <div class="stat-value">{{ deptCount }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 中间：排课进度 + 快速入口 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="16">
        <el-card class="schedule-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-weight: 600;">排课进度</span>
                <el-select v-model="selectedSemester" size="small" style="width: 200px;" @change="loadStats">
                  <el-option v-for="s in semesterList" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </div>
              <el-button type="primary" size="small" @click="$router.push('/scheduler')">
                <el-icon><Calendar /></el-icon>
                前往排课
              </el-button>
            </div>
          </template>

          <div v-if="selectedSemester" class="schedule-stats">
            <el-row :gutter="24">
              <el-col :span="6">
                <div class="progress-item">
                  <div class="progress-label">排课完成率</div>
                  <el-progress
                    type="dashboard"
                    :percentage="stats.completion_rate || 0"
                    :color="progressColor"
                    :stroke-width="10"
                    :width="120"
                  />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-block">
                  <div class="stat-block-value">{{ stats.scheduled_tasks || 0 }}<span class="stat-block-unit"> / {{ stats.total_tasks || 0 }}</span></div>
                  <div class="stat-block-label">已排任务 / 总任务</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-block">
                  <div class="stat-block-value">{{ stats.scheduled_sections || 0 }}<span class="stat-block-unit">节</span></div>
                  <div class="stat-block-label">已排课时</div>
                </div>
              </el-col>
              <el-col :span="6">
                <div class="stat-block">
                  <div class="stat-block-value" :class="{ danger: (stats.conflicts || 0) > 0 }">
                    {{ stats.conflicts || 0 }}<span class="stat-block-unit">个</span>
                  </div>
                  <div class="stat-block-label">冲突数量</div>
                </div>
              </el-col>
            </el-row>
          </div>

          <el-empty v-else description="请先选择学期" :image-size="60" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>
            <span style="font-weight: 600;">快速入口</span>
          </template>
          <div class="quick-actions">
            <div class="action-grid">
              <div class="action-item" @click="$router.push('/timetable')">
                <el-icon :size="24" color="#409eff"><Tickets /></el-icon>
                <span>课表查询</span>
              </div>
              <div class="action-item" @click="$router.push('/scheduler')">
                <el-icon :size="24" color="#67c23a"><Calendar /></el-icon>
                <span>排课中心</span>
              </div>
              <div class="action-item" @click="$router.push('/teaching-tasks')">
                <el-icon :size="24" color="#e6a23c"><Notebook /></el-icon>
                <span>教学任务</span>
              </div>
              <div class="action-item" @click="$router.push('/teachers')">
                <el-icon :size="24" color="#f56c6c"><User /></el-icon>
                <span>教师管理</span>
              </div>
              <div class="action-item" @click="$router.push('/departments')">
                <el-icon :size="24" color="#909399"><OfficeBuilding /></el-icon>
                <span>院系专业</span>
              </div>
              <div class="action-item" @click="$router.push('/settings')">
                <el-icon :size="24" color="#9254de"><Setting /></el-icon>
                <span>系统设置</span>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 底部：最近排课批次 -->
    <el-row :gutter="16" style="margin-top: 16px;">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 600;">最近排课记录</span>
              <el-button link type="primary" @click="$router.push('/scheduler')">查看全部</el-button>
            </div>
          </template>
          <el-table :data="recentBatches" v-loading="batchLoading" size="small">
            <el-table-column prop="batch_code" label="批次号" width="200" />
            <el-table-column label="学期" width="160">
              <template #default="{ row }">{{ getSemesterName(row.semester_id) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="batchStatusType(row.status)" size="small">{{ batchStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="score" label="评分" width="80" align="center">
              <template #default="{ row }">{{ row.score || '-' }}</template>
            </el-table-column>
            <el-table-column label="用时" width="100" align="center">
              <template #default="{ row }">
                {{ row.started_at && row.finished_at ? ((new Date(row.finished_at) - new Date(row.started_at)) / 1000).toFixed(1) + 's' : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="finished_at" label="完成时间" width="180" />
          </el-table>
          <el-empty v-if="recentBatches.length === 0 && !batchLoading" description="暂无排课记录" :image-size="60" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  User, School, Reading, Avatar, Notebook, OfficeBuilding,
  Calendar, Tickets, Setting,
} from '@element-plus/icons-vue'
import { scheduleApi, semesterApi, departmentApi } from '@/api'

const router = useRouter()

const stats = ref({})
const deptCount = ref(0)
const semesterList = ref([])
const selectedSemester = ref(null)
const recentBatches = ref([])
const batchLoading = ref(false)

const progressColor = computed(() => {
  const rate = stats.value.completion_rate || 0
  if (rate >= 90) return '#67c23a'
  if (rate >= 60) return '#409eff'
  if (rate >= 30) return '#e6a23c'
  return '#f56c6c'
})

const batchStatusType = (status) => ({
  pending: 'info', running: 'warning', completed: 'success', failed: 'danger',
}[status] || 'info')

const batchStatusText = (status) => ({
  pending: '排队中', running: '排课中', completed: '已完成', failed: '失败',
}[status] || status)

const getSemesterName = (id) => {
  const s = semesterList.value.find(s => s.id === id)
  return s ? s.name : '-'
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

const loadStats = async () => {
  try {
    const res = await scheduleApi.stats({ semester_id: selectedSemester.value })
    stats.value = res
  } catch (e) {}
}

const loadDeptCount = async () => {
  try {
    const list = await departmentApi.all()
    deptCount.value = list.length || 0
  } catch (e) {}
}

const loadRecentBatches = async () => {
  batchLoading.value = true
  try {
    const list = await scheduleApi.batches({})
    recentBatches.value = list.slice(0, 5)
  } catch (e) {} finally {
    batchLoading.value = false
  }
}

onMounted(() => {
  loadSemesters().then(() => {
    loadStats()
    loadRecentBatches()
  })
  loadDeptCount()
})
</script>

<style lang="scss" scoped>
.dashboard {
  .stat-card {
    .stat-content {
      display: flex;
      align-items: center;
      gap: 14px;

      .stat-icon {
        width: 52px;
        height: 52px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;

        &.icon-blue { background: #ecf5ff; color: #409eff; }
        &.icon-green { background: #f0f9eb; color: #67c23a; }
        &.icon-orange { background: #fdf6ec; color: #e6a23c; }
        &.icon-red { background: #fef0f0; color: #f56c6c; }
        &.icon-purple { background: #f9f0ff; color: #9254de; }
        &.icon-cyan { background: #e6fffb; color: #13c2c2; }
      }

      .stat-info {
        .stat-label {
          font-size: 13px;
          color: #909399;
          margin-bottom: 4px;
        }
        .stat-value {
          font-size: 22px;
          font-weight: 600;
          color: #303133;
        }
      }
    }
  }

  .schedule-card {
    .schedule-stats {
      padding: 10px 0;

      .progress-item {
        text-align: center;

        .progress-label {
          font-size: 13px;
          color: #606266;
          margin-bottom: 10px;
          font-weight: 600;
        }
      }

      .stat-block {
        text-align: center;
        padding: 30px 0;

        .stat-block-value {
          font-size: 28px;
          font-weight: 600;
          color: #303133;
          margin-bottom: 6px;

          &.danger {
            color: #f56c6c;
          }

          .stat-block-unit {
            font-size: 14px;
            font-weight: normal;
            color: #909399;
            margin-left: 2px;
          }
        }

        .stat-block-label {
          font-size: 13px;
          color: #909399;
        }
      }
    }
  }

  .quick-actions {
    .action-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;

      .action-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        padding: 16px 8px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 13px;
        color: #606266;

        &:hover {
          background: #f5f7fa;
          transform: translateY(-2px);
        }
      }
    }
  }
}
</style>

<template>
  <div class="batch-compare">
    <!-- 批次选择 -->
    <BatchSelector
      :batches="batches"
      v-model:selectedCodes="selectedCodes"
      @update:selectedCodes="onSelectionChange"
    />

    <!-- 对比区域 -->
    <div v-if="compareData" class="compare-area">
      <!-- 对比结论 -->
      <div class="compare-summary" v-if="compareData.best_batch_code">
        <el-alert type="success" :closable="false" show-icon>
          <template #title>
            <span>
              最优批次：<strong>{{ compareData.best_batch_code }}</strong>
              （惩罚分 {{ bestBatchScore }}，总分最低）
            </span>
          </template>
        </el-alert>
      </div>

      <el-row :gutter="16" style="margin-top: 16px;">
        <!-- 左侧：图表区 -->
        <el-col :span="15">
          <el-card shadow="never" class="chart-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">评分对比图</span>
                <el-radio-group v-model="chartType" size="small">
                  <el-radio-button value="radar">雷达图</el-radio-button>
                  <el-radio-button value="bar">柱状图</el-radio-button>
                </el-radio-group>
              </div>
            </template>

            <ScoreRadarChart
              v-if="chartType === 'radar'"
              :batches="compareData.batches"
            />
            <ScoreBarChart
              v-else
              :batches="compareData.batches"
            />

            <div class="chart-note">
              <el-icon><InfoFilled /></el-icon>
              <span v-if="chartType === 'radar'">雷达图为优良度得分（0-100，越高越好），基于对比批次归一化</span>
              <span v-else>柱状图为惩罚分（越低越好），高亮柱子为该维度最优</span>
            </div>
          </el-card>
        </el-col>

        <!-- 右侧：评分明细 -->
        <el-col :span="9">
          <el-card shadow="never" class="detail-card">
            <template #header>
              <span class="card-title">评分明细</span>
            </template>
            <ScoreDetailTable
              :batches="compareData.batches"
              @activate="handleActivate"
            />
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 不足2个批次时的提示 -->
    <el-empty
      v-else-if="!loading && selectedCodes.length < 2"
      description="请选择至少 2 个批次进行对比"
      :image-size="80"
    />

    <el-empty v-else-if="loading" description="加载中..." :image-size="60" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled } from '@element-plus/icons-vue'
import { scheduleApi } from '@/api'
import BatchSelector from './BatchSelector.vue'
import ScoreRadarChart from './ScoreRadarChart.vue'
import ScoreBarChart from './ScoreBarChart.vue'
import ScoreDetailTable from './ScoreDetailTable.vue'

const props = defineProps({
  batches: { type: Array, default: () => [] },
  semesterId: { type: Number, default: null },
})

const emit = defineEmits(['activated'])

const selectedCodes = ref([])
const chartType = ref('radar')
const compareData = ref(null)
const loading = ref(false)

const bestBatchScore = computed(() => {
  if (!compareData.value?.best_batch_code) return '-'
  const best = compareData.value.batches.find(b => b.batch_code === compareData.value.best_batch_code)
  return best?.total_score ?? '-'
})

// 默认选中最近2个已完成批次
function initSelection() {
  const completed = props.batches.filter(b => b.status === 'completed').sort((a, b) => b.id - a.id)
  if (completed.length >= 2) {
    selectedCodes.value = completed.slice(0, 2).map(b => b.batch_code)
    loadCompareData()
  }
}

function onSelectionChange() {
  if (selectedCodes.value.length >= 2) {
    loadCompareData()
  } else {
    compareData.value = null
  }
}

async function loadCompareData() {
  if (selectedCodes.value.length < 2) return
  loading.value = true
  try {
    const res = await scheduleApi.compareBatches(selectedCodes.value)
    compareData.value = res
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '对比数据加载失败')
    compareData.value = null
  } finally {
    loading.value = false
  }
}

async function handleActivate(batchCode) {
  try {
    await ElMessageBox.confirm(
      '确定将此批次设为当前使用吗？当前排课结果将切换到该批次。',
      '切换排课结果',
      { type: 'warning', confirmButtonText: '确定切换', cancelButtonText: '取消' }
    )
    const res = await scheduleApi.activateBatch(batchCode)
    ElMessage.success(res.message || '切换成功')
    emit('activated', batchCode)
    // 刷新对比数据（更新 is_current 标记）
    loadCompareData()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.detail || '切换失败')
    }
  }
}

// 外部刷新对比数据
function refresh() {
  loadCompareData()
}

defineExpose({ refresh })

onMounted(() => {
  initSelection()
})

// 监听批次列表变化（新排课完成后）
watch(() => props.batches, () => {
  // 如果已选批次都存在，则保持选择并刷新
  const allExists = selectedCodes.value.every(code =>
    props.batches.some(b => b.batch_code === code)
  )
  if (allExists && selectedCodes.value.length >= 2) {
    loadCompareData()
  } else {
    initSelection()
  }
}, { deep: true })
</script>

<style scoped>
.batch-compare {
  width: 100%;
}
.compare-area {
  margin-top: 8px;
}
.compare-summary {
  margin-bottom: 4px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}
.chart-card {
  height: 100%;
}
.detail-card {
  height: 100%;
}
.chart-note {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
}
</style>

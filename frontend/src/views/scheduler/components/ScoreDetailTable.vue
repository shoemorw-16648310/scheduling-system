<template>
  <div class="score-detail-table">
    <el-table :data="tableData" border stripe size="default">
      <el-table-column prop="label" label="评分维度" width="130" fixed>
        <template #default="{ row }">
          <div class="dim-cell">
            <span class="dim-label">{{ row.label }}</span>
            <el-tooltip :content="row.description" placement="top">
              <el-icon class="dim-tip"><QuestionFilled /></el-icon>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        v-for="(batch, idx) in batches"
        :key="batch.batch_code"
        :label="batch.batch_code"
        align="center"
      >
        <template #header>
          <div class="header-cell">
            <span class="batch-code-text">{{ batch.batch_code }}</span>
            <el-tag v-if="batch.is_current" type="success" size="small" effect="dark">当前</el-tag>
          </div>
        </template>
        <template #default="{ row }">
          <div class="score-cell" :class="{ 'is-best': isBest(row.key, idx) }">
            <span class="score">{{ getScore(row.key, idx) }}</span>
            <el-icon v-if="isBest(row.key, idx) && getScore(row.key, idx) > 0" class="best-icon"><Trophy /></el-icon>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- 操作区 -->
    <div class="table-actions">
      <div
        v-for="(batch, idx) in batches"
        :key="batch.batch_code"
        class="action-col"
        :style="{ marginLeft: idx === 0 ? '130px' : '0' }"
      >
        <el-button
          :type="batch.is_current ? 'success' : 'primary'"
          :disabled="batch.is_current"
          size="small"
          @click="$emit('activate', batch.batch_code)"
        >
          {{ batch.is_current ? '已激活' : '设为当前使用' }}
        </el-button>
        <div class="action-meta">
          <span v-if="batch.solve_time != null">用时 {{ batch.solve_time }}s</span>
          <span v-if="batch.scheduled_tasks != null && batch.total_tasks != null">
            {{ batch.scheduled_tasks }}/{{ batch.total_tasks }}任务
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { QuestionFilled, Trophy } from '@element-plus/icons-vue'
import { SCORE_DIMENSIONS } from './scoreUtils'

const props = defineProps({
  batches: { type: Array, default: () => [] },
})

defineEmits(['activate'])

const tableData = computed(() =>
  SCORE_DIMENSIONS.map(dim => ({
    key: dim.key,
    label: dim.label,
    description: dim.description,
  }))
)

function getScore(dimKey, batchIdx) {
  const batch = props.batches[batchIdx]
  if (!batch || !batch.dimensions) return 0
  return batch.dimensions[dimKey] ?? 0
}

function isBest(dimKey, batchIdx) {
  const scores = props.batches.map((b, i) => getScore(dimKey, i))
  const best = Math.min(...scores.filter(s => s > 0))
  if (best === Infinity) return false
  return getScore(dimKey, batchIdx) === best && getScore(dimKey, batchIdx) > 0
}
</script>

<style scoped>
.score-detail-table {
  width: 100%;
}
.dim-cell {
  display: flex;
  align-items: center;
  gap: 4px;
}
.dim-label {
  font-size: 13px;
  color: #303133;
}
.dim-tip {
  color: #c0c4cc;
  font-size: 13px;
  cursor: help;
}
.header-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.batch-code-text {
  font-size: 12px;
  font-family: monospace;
  color: #606266;
}
.score-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px 0;
}
.score {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}
.score-cell.is-best .score {
  color: #67c23a;
  font-weight: 700;
}
.best-icon {
  color: #e6a23c;
  font-size: 14px;
}
.table-actions {
  display: flex;
  margin-top: 12px;
}
.action-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}
.action-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 10px;
}
</style>

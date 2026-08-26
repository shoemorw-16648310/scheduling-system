<template>
  <div class="batch-selector">
    <div class="selector-header">
      <span class="title">选择对比批次</span>
      <span class="hint">已选 <em>{{ selectedCount }}</em> / 3 个（至少 2 个）</span>
    </div>
    <div class="batch-cards">
      <div
        v-for="batch in completedBatches"
        :key="batch.id"
        class="batch-card"
        :class="{
          selected: selectedCodes.includes(batch.batch_code),
          disabled: !selectedCodes.includes(batch.batch_code) && selectedCount >= 3,
          current: batch.is_current,
        }"
        @click="toggleBatch(batch)"
      >
        <div class="card-top">
          <el-tag v-if="batch.is_current" type="success" size="small" effect="dark">当前使用</el-tag>
          <span class="batch-code">{{ batch.batch_code }}</span>
        </div>
        <div class="card-score">
          <span class="score-label">惩罚分</span>
          <span class="score-value">{{ batch.score ?? '-' }}</span>
          <span class="score-hint">越低越好</span>
        </div>
        <div class="card-meta">
          <span>{{ formatTime(batch.created_at) }}</span>
        </div>
        <div class="card-check">
          <el-checkbox :model-value="selectedCodes.includes(batch.batch_code)" :disabled="!selectedCodes.includes(batch.batch_code) && selectedCount >= 3" />
        </div>
      </div>
      <el-empty v-if="completedBatches.length === 0" description="暂无已完成的排课批次" :image-size="80" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  batches: { type: Array, default: () => [] },
  selectedCodes: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:selectedCodes'])

const completedBatches = computed(() =>
  props.batches.filter(b => b.status === 'completed').sort((a, b) => b.id - a.id)
)

const selectedCount = computed(() => props.selectedCodes.length)

function toggleBatch(batch) {
  const code = batch.batch_code
  const codes = [...props.selectedCodes]
  const idx = codes.indexOf(code)
  if (idx > -1) {
    codes.splice(idx, 1)
  } else {
    if (codes.length >= 3) return
    codes.push(code)
  }
  emit('update:selectedCodes', codes)
}

function formatTime(t) {
  if (!t) return '-'
  const d = new Date(t)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.batch-selector {
  margin-bottom: 20px;
}
.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.selector-header .title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.selector-header .hint {
  font-size: 13px;
  color: #909399;
}
.selector-header .hint em {
  color: #409eff;
  font-style: normal;
  font-weight: 600;
}
.batch-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.batch-card {
  position: relative;
  width: 200px;
  padding: 14px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: all 0.2s;
}
.batch-card:hover {
  border-color: #c6e2ff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}
.batch-card.selected {
  border-color: #409eff;
  background: #ecf5ff;
}
.batch-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.batch-card.current {
  border-color: #67c23a;
}
.batch-card.current.selected {
  background: #f0f9eb;
  border-color: #67c23a;
}
.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.batch-code {
  font-size: 13px;
  color: #606266;
  font-family: monospace;
}
.card-score {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 6px;
}
.score-label {
  font-size: 12px;
  color: #909399;
}
.score-value {
  font-size: 22px;
  font-weight: 700;
  color: #409eff;
}
.score-hint {
  font-size: 11px;
  color: #c0c4cc;
}
.card-meta {
  font-size: 12px;
  color: #909399;
}
.card-check {
  position: absolute;
  top: 10px;
  right: 10px;
}
</style>

// 评分维度元信息（与后端 SCORE_DIMENSIONS_INFO 保持一致）
export const SCORE_DIMENSIONS = [
  { key: 'main_course_morning', label: '主课上午优先', weight: 60, description: '主课尽量安排在上午时段' },
  { key: 'teacher_daily_hours', label: '教师日课时均衡', weight: 50, description: '教师每日课时不超过上限' },
  { key: 'uniform_distribution', label: '课程均匀分布', weight: 40, description: '同一课程在周内均匀分布' },
  { key: 'teacher_consecutive', label: '教师连堂限制', weight: 30, description: '教师连续课时不超过上限' },
  { key: 'noon_break', label: '教师午休保护', weight: 25, description: '课程不跨越午休时段' },
  { key: 'class_daily_hours', label: '班级日课时均衡', weight: 20, description: '班级每日课时相对均衡' },
  { key: 'room_balance', label: '教室使用均衡', weight: 15, description: '各教室使用频次均衡' },
]

/**
 * 将惩罚分（越低越好）归一化为优良度分数（0-100，越高越好）
 * @param {Object} dimensionScores - 各维度惩罚分 { key: score }
 * @param {Array<number>} maxScores - 各维度在对比批次中的最大值（用于归一化基准）
 * @returns {Object} 各维度优良度分数 { key: 0-100 }
 */
export function normalizeToQuality(dimensionScores, maxScores) {
  const result = {}
  for (const dim of SCORE_DIMENSIONS) {
    const score = dimensionScores[dim.key] || 0
    const max = maxScores[dim.key] || 1
    // 越低越好 -> 越高越好：100 * (1 - score/max)
    result[dim.key] = Math.max(0, Math.round(100 * (1 - score / max)))
  }
  return result
}

/**
 * 计算多批次各维度的最大惩罚分（用于归一化基准）
 * @param {Array<Object>} batches - 批次列表，每个包含 dimensions: { key: score }
 * @returns {Object} { key: maxScore }
 */
export function calcMaxScores(batches) {
  const maxScores = {}
  for (const dim of SCORE_DIMENSIONS) {
    maxScores[dim.key] = 1 // 最小值为1避免除零
  }
  for (const batch of batches) {
    if (!batch.dimensions) continue
    for (const dim of SCORE_DIMENSIONS) {
      const v = batch.dimensions[dim.key] || 0
      if (v > maxScores[dim.key]) {
        maxScores[dim.key] = v
      }
    }
  }
  return maxScores
}

// 批次状态文字映射
export const BATCH_STATUS_MAP = {
  pending: { text: '排队中', type: 'info' },
  running: { text: '排课中', type: 'warning' },
  completed: { text: '已完成', type: 'success' },
  failed: { text: '失败', type: 'danger' },
}

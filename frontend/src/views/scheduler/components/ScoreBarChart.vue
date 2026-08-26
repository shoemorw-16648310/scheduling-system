<template>
  <div class="score-bar-chart">
    <v-chart :option="chartOption" :autoresize="true" style="width: 100%; height: 360px;" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { SCORE_DIMENSIONS } from './scoreUtils'

use([BarChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent, CanvasRenderer])

const props = defineProps({
  batches: { type: Array, default: () => [] },
})

const COLORS = ['#409eff', '#67c23a', '#e6a23c']

const chartOption = computed(() => {
  if (!props.batches.length) {
    return {}
  }

  const xAxisData = SCORE_DIMENSIONS.map(d => d.label)

  // 找每个维度的最低分（最优），用于高亮
  const bestScores = {}
  for (const dim of SCORE_DIMENSIONS) {
    let best = Infinity
    for (const batch of props.batches) {
      if (batch.dimensions) {
        const v = batch.dimensions[dim.key] ?? 0
        if (v < best) best = v
      }
    }
    bestScores[dim.key] = best === Infinity ? 0 : best
  }

  const series = props.batches.map((batch, idx) => {
    const data = SCORE_DIMENSIONS.map(dim => {
      const v = batch.dimensions ? (batch.dimensions[dim.key] ?? 0) : 0
      return {
        value: v,
        itemStyle: v === bestScores[dim.key] && v > 0
          ? { color: COLORS[idx % COLORS.length], shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.2)' }
          : { color: COLORS[idx % COLORS.length], opacity: 0.85 },
      }
    })
    return {
      name: batch.batch_code,
      type: 'bar',
      data,
      barMaxWidth: 28,
    }
  })

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const dimIdx = params[0].dataIndex
        const dim = SCORE_DIMENSIONS[dimIdx]
        let html = `<div style="font-weight:600;margin-bottom:6px">${dim.label}</div>`
        params.forEach(p => {
          const isBest = p.data.value === bestScores[dim.key] && p.data.value > 0
          html += `<div style="display:flex;justify-content:space-between;gap:20px;font-size:12px;align-items:center">
            <span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};margin-right:6px"></span>${p.seriesName}</span>
            <span style="font-weight:600">${p.data.value}${isBest ? ' ✓' : ''}</span>
          </div>`
        })
        html += `<div style="margin-top:4px;font-size:11px;color:#909399">${dim.description}</div>`
        return html
      },
    },
    legend: {
      data: props.batches.map(b => b.batch_code),
      bottom: 0,
      type: 'scroll',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLabel: {
        interval: 0,
        rotate: 20,
        fontSize: 11,
        color: '#606266',
      },
      axisLine: { lineStyle: { color: '#e4e7ed' } },
    },
    yAxis: {
      type: 'value',
      name: '惩罚分（越低越好）',
      nameTextStyle: { fontSize: 12, color: '#909399' },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#f0f2f5' } },
      axisLabel: { fontSize: 11, color: '#909399' },
    },
    series,
  }
})
</script>

<style scoped>
.score-bar-chart {
  width: 100%;
  background: #fff;
  border-radius: 6px;
}
</style>

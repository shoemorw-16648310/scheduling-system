<template>
  <div class="score-radar-chart">
    <v-chart :option="chartOption" :autoresize="true" style="width: 100%; height: 360px;" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { SCORE_DIMENSIONS, calcMaxScores, normalizeToQuality } from './scoreUtils'

use([RadarChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  batches: { type: Array, default: () => [] },
})

const COLORS = ['#409eff', '#67c23a', '#e6a23c']

const chartOption = computed(() => {
  if (!props.batches.length) {
    return {}
  }

  const maxScores = calcMaxScores(props.batches)

  const indicator = SCORE_DIMENSIONS.map(dim => ({
    name: dim.label,
    max: 100,
  }))

  const seriesData = props.batches.map((batch, idx) => {
    const quality = batch.dimensions ? normalizeToQuality(batch.dimensions, maxScores) : {}
    const values = SCORE_DIMENSIONS.map(dim => quality[dim.key] ?? 0)
    return {
      value: values,
      name: batch.batch_code,
      itemStyle: { color: COLORS[idx % COLORS.length] },
      areaStyle: { opacity: 0.15 },
    }
  })

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const values = params.value
        let html = `<div style="font-weight:600;margin-bottom:6px">${params.name}</div>`
        SCORE_DIMENSIONS.forEach((dim, i) => {
          html += `<div style="display:flex;justify-content:space-between;gap:20px;font-size:12px">
            <span>${dim.label}</span>
            <span style="font-weight:600">${values[i]} 分</span>
          </div>`
        })
        return html
      },
    },
    legend: {
      data: props.batches.map(b => b.batch_code),
      bottom: 0,
      type: 'scroll',
    },
    radar: {
      indicator,
      shape: 'polygon',
      splitNumber: 4,
      axisName: {
        color: '#606266',
        fontSize: 12,
      },
      splitLine: {
        lineStyle: { color: '#e4e7ed' },
      },
      splitArea: {
        show: true,
        areaStyle: { color: ['#fafafa', '#fff'] },
      },
      radius: '65%',
      center: ['50%', '45%'],
    },
    series: [{
      type: 'radar',
      data: seriesData,
      emphasis: {
        lineStyle: { width: 3 },
      },
    }],
  }
})
</script>

<style scoped>
.score-radar-chart {
  width: 100%;
  background: #fff;
  border-radius: 6px;
}
</style>

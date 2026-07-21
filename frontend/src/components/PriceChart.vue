<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent,
  TitleComponent, MarkLineComponent, DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  LineChart, GridComponent, TooltipComponent, LegendComponent,
  TitleComponent, MarkLineComponent, DataZoomComponent, CanvasRenderer,
])

const props = defineProps({
  // ECharts 数据
  daily: { type: Array, default: () => [] },
  history: { type: Array, default: () => [] },
  target: { type: Number, default: 0 },
  purchase: { type: Number, default: 0 },
})

const chartEl = ref(null)
let chart = null

function buildOption() {
  // daily 为本机自抓（每天 1 个点），history 为 BUFF 自带 30 天曲线
  const series = []

  if (props.history && props.history.length) {
    series.push({
      name: 'BUFF 30天均价',
      type: 'line',
      smooth: true,
      showSymbol: false,
      lineStyle: { width: 1, color: '#4a90e2', opacity: 0.7, type: 'dashed' },
      itemStyle: { color: '#4a90e2' },
      data: props.history.map(p => [p.date, p.price]),
    })
  }

  if (props.daily && props.daily.length) {
    series.push({
      name: '每日最低在售',
      type: 'line',
      smooth: false,
      showSymbol: true,
      symbolSize: 8,
      lineStyle: { width: 3, color: '#ff7043' },
      itemStyle: { color: '#ff7043' },
      data: props.daily.map(p => [p.date, p.price]),
      markLine: {
        symbol: 'none',
        silent: true,
        lineStyle: { type: 'dashed', width: 1.5 },
        data: [
          {
            yAxis: props.target,
            name: `目标价 ¥${props.target}`,
            label: {
              formatter: `目标 ¥${props.target}`,
              color: '#fbc02d',
              position: 'insideEndTop',
            },
            lineStyle: { color: '#fbc02d' },
          },
          {
            yAxis: props.purchase,
            name: `购入价 ¥${props.purchase}`,
            label: {
              formatter: `购入 ¥${props.purchase}`,
              color: '#26a69a',
              position: 'insideEndBottom',
            },
            lineStyle: { color: '#26a69a' },
          },
        ],
      },
    })
  }

  return {
    backgroundColor: 'transparent',
    textStyle: { color: '#cfd3dc' },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(20,24,32,0.92)',
      borderColor: '#2a2f3a',
      textStyle: { color: '#e6e8eb' },
      valueFormatter: (v) => v == null ? '-' : `¥${Number(v).toFixed(2)}`,
    },
    legend: {
      data: series.map(s => s.name),
      textStyle: { color: '#cfd3dc' },
      top: 0,
    },
    grid: { left: 60, right: 30, top: 40, bottom: 60 },
    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: '#2a2f3a' } },
      axisLabel: { color: '#8a8f99' },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: { lineStyle: { color: '#2a2f3a' } },
      splitLine: { lineStyle: { color: '#1c2029' } },
      axisLabel: {
        color: '#8a8f99',
        formatter: (v) => `¥${v}`,
      },
    },
    dataZoom: [
      { type: 'inside' },
      {
        type: 'slider',
        height: 18,
        bottom: 16,
        backgroundColor: '#161a22',
        fillerColor: 'rgba(255,112,67,0.15)',
        borderColor: '#2a2f3a',
        handleStyle: { color: '#ff7043' },
        textStyle: { color: '#8a8f99' },
      },
    ],
    series,
  }
}

function render() {
  if (!chartEl.value) return
  if (!chart) {
    chart = echarts.init(chartEl.value, null, { renderer: 'canvas' })
  }
  chart.setOption(buildOption(), true)
}

function resize() {
  chart && chart.resize()
}

onMounted(async () => {
  await nextTick()
  render()
  window.addEventListener('resize', resize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  chart && chart.dispose()
  chart = null
})

watch(
  () => [props.daily, props.history, props.target, props.purchase],
  () => render(),
  { deep: true }
)
</script>

<template>
  <div ref="chartEl" class="chart"></div>
</template>

<style scoped>
.chart {
  width: 100%;
  height: 460px;
}
</style>

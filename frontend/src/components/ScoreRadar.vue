<template>
  <div class="score-radar">
    <canvas ref="radarChart"></canvas>
    <div class="score-legend">
      <div v-for="(value, key) in scores" :key="key" class="legend-item">
        <span class="legend-label">{{ formatLabel(key) }}</span>
        <span class="legend-value">{{ value }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { Chart, RadarController, RadialLinearScale, PointElement, LineElement, Filler, Tooltip } from 'chart.js'

Chart.register(RadarController, RadialLinearScale, PointElement, LineElement, Filler, Tooltip)

const props = defineProps({
  scores: {
    type: Object,
    default: () => ({})
  }
})

const radarChart = ref(null)
let chartInstance = null

const formatLabel = (key) => {
  const labels = {
    accuracy: '准确率',
    format: '格式合规',
    domain: '领域匹配',
    hallucination: '幻觉检测',
    length: '长度控制'
  }
  return labels[key] || key
}

const initChart = () => {
  if (chartInstance) {
    chartInstance.destroy()
  }

  const ctx = radarChart.value.getContext('2d')
  const data = {
    labels: ['准确率', '格式合规', '领域匹配', '幻觉检测', '长度控制'],
    datasets: [{
      label: '评分',
      data: [
        props.scores.accuracy || 0,
        props.scores.format || 0,
        props.scores.domain || 0,
        props.scores.hallucination || 0,
        props.scores.length || 0
      ],
      backgroundColor: 'rgba(102, 126, 234, 0.2)',
      borderColor: 'rgba(102, 126, 234, 1)',
      borderWidth: 2,
      pointBackgroundColor: 'rgba(102, 126, 234, 1)',
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
    }]
  }

  chartInstance = new Chart(ctx, {
    type: 'radar',
    data,
    options: {
      responsive: true,
      maintainAspectRatio: true,
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20
          }
        }
      }
    }
  })
}

onMounted(() => {
  if (props.scores && Object.keys(props.scores).length > 0) {
    initChart()
  }
})

watch(() => props.scores, () => {
  if (props.scores && Object.keys(props.scores).length > 0) {
    initChart()
  }
}, { deep: true })
</script>

<style scoped>
.score-radar {
  margin-bottom: 20px;
}

canvas {
  max-width: 400px;
  margin: 0 auto;
  display: block;
}

.score-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: center;
  margin-top: 20px;
}

.legend-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.legend-label {
  font-size: 12px;
  opacity: 0.9;
}

.legend-value {
  font-size: 24px;
  font-weight: bold;
}
</style>
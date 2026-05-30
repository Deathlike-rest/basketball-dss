<script setup>
import { onMounted, ref, watch } from 'vue'
import { Chart, RadarController, RadialLinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js'

Chart.register(RadarController, RadialLinearScale, PointElement, LineElement, Tooltip, Legend)

// Радар по 21 атрибуту с подсветкой категорий (раздел 2.5.2, рисунок 9).
const props = defineProps({ rows: { type: Array, required: true } })
const canvas = ref(null)
let chart = null

function render() {
  if (!canvas.value) return
  const labels = props.rows.map((r) => r.name)
  const data = props.rows.map((r) => r.score)
  if (chart) chart.destroy()
  chart = new Chart(canvas.value, {
    type: 'radar',
    data: {
      labels,
      datasets: [{
        label: 'Балл (25–99)',
        data,
        backgroundColor: 'rgba(232,116,30,0.25)',
        borderColor: '#e8741e',
        borderWidth: 2,
        pointBackgroundColor: '#e8741e',
        pointRadius: 3,
      }],
    },
    options: {
      responsive: true,
      scales: {
        r: {
          min: 25, max: 99,
          ticks: { stepSize: 25, color: '#8b99a7', backdropColor: 'transparent' },
          grid: { color: '#2e3a47' },
          angleLines: { color: '#2e3a47' },
          pointLabels: { color: '#e6edf3', font: { size: 10 } },
        },
      },
      plugins: { legend: { labels: { color: '#e6edf3' } } },
    },
  })
}

onMounted(render)
watch(() => props.rows, render, { deep: true })
</script>

<template>
  <canvas ref="canvas" height="380"></canvas>
</template>

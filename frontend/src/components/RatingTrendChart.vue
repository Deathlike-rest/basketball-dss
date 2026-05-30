<script setup>
import { onMounted, ref, watch } from 'vue'
import { Chart, LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend } from 'chart.js'

Chart.register(LineController, LineElement, PointElement, LinearScale, CategoryScale, Tooltip, Legend)

// Динамика интегрального рейтинга за период (вкладка «История», раздел 2.5.2).
const props = defineProps({ ratings: { type: Array, required: true } })
const canvas = ref(null)
let chart = null

function render() {
  if (!canvas.value) return
  if (chart) chart.destroy()
  chart = new Chart(canvas.value, {
    type: 'line',
    data: {
      labels: props.ratings.map((r) => r.date),
      datasets: [
        { label: 'R* (скорректированный)', data: props.ratings.map((r) => r.R_star), borderColor: '#e8741e', tension: 0.25 },
        { label: 'R (базовый)', data: props.ratings.map((r) => r.R_P), borderColor: '#3b82f6', tension: 0.25 },
      ],
    },
    options: {
      responsive: true,
      scales: {
        y: { min: 25, max: 99, grid: { color: '#2e3a47' }, ticks: { color: '#8b99a7' } },
        x: { grid: { color: '#2e3a47' }, ticks: { color: '#8b99a7' } },
      },
      plugins: { legend: { labels: { color: '#e6edf3' } } },
    },
  })
}

onMounted(render)
watch(() => props.ratings, render, { deep: true })
</script>

<template>
  <canvas ref="canvas" height="240"></canvas>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

// Печатный отчёт по составу (раздел 2.4.1, этап 7; блоки A5/A6 рис. 4):
// «итоговый рейтинг ... на экран либо на печать». Кнопка «Печать» открывает
// системный диалог печати (можно сохранить в PDF).
const router = useRouter()
const team = ref([])
const today = new Date().toLocaleDateString('ru-RU')

onMounted(async () => {
  const { data } = await api.teamRatings()
  team.value = data.sort((a, b) => b.R_star - a.R_star)
})

const trendSign = { up: '▲', down: '▼', flat: '–' }
const doPrint = () => window.print()
</script>

<template>
  <div class="container report">
    <div class="no-print" style="display:flex; gap:10px; margin-bottom:16px">
      <button class="btn secondary" @click="router.back()">‹ Назад</button>
      <button class="btn" @click="doPrint">Печать / Сохранить в PDF</button>
    </div>

    <div class="report-doc">
      <h1>Отчёт по составу команды</h1>
      <p class="muted">Система поддержки принятия решений · {{ today }}</p>
      <table>
        <thead>
          <tr>
            <th>№</th><th>Игрок</th><th>Позиция</th>
            <th>R*</th><th>R</th><th>M_IQ</th><th>M_S</th><th>M_L</th><th>Тренд</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(p, i) in team" :key="p.player_id">
            <td>{{ i + 1 }}</td>
            <td>{{ p.name }}</td>
            <td>{{ p.position }}</td>
            <td class="b">{{ p.R_star }}</td>
            <td>{{ p.R_P }}</td>
            <td>{{ p.M_IQ ?? '' }}</td>
            <td>{{ p.M_S ?? '' }}</td>
            <td>{{ p.M_L ?? '' }}</td>
            <td>{{ trendSign[p.trend] }}</td>
          </tr>
        </tbody>
      </table>
      <p class="muted" style="margin-top:16px">
        R* — скорректированный интегральный рейтинг (с модификаторами), R — базовый.
        Шкала 25–99. Рейтинг рассчитан по основной позиции игрока.
      </p>
    </div>
  </div>
</template>

<style scoped>
.report-doc h1 { margin-bottom: 4px; }
.b { font-weight: 700; color: var(--accent); }
.report table { width: 100%; }
@media print {
  .no-print { display: none !important; }
  .report-doc { color: #000; }
}
</style>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../store/auth'

// Сценарий 1 — конструктор стартовой пятёрки (раздел 2.4.3).
// Система предлагает основного игрока и две альтернативы на каждую позицию;
// главный тренер выбирает и утверждает состав на матч.
const auth = useAuthStore()
const suggestion = ref({})
const selected = ref({})           // позиция -> id выбранного игрока
const opponent = ref('')
const matchDate = ref(new Date().toISOString().slice(0, 10))
const saved = ref(false)

const POS_ORDER = ['PG', 'SG', 'SF', 'PF', 'C']

onMounted(async () => {
  const { data } = await api.lineupSuggestion()
  suggestion.value = data
  for (const pos of POS_ORDER) {
    selected.value[pos] = data[pos]?.starter?.id ?? null
  }
})

function optionsFor(pos) {
  const s = suggestion.value[pos]
  if (!s || !s.starter) return []
  return [s.starter, ...(s.alternatives || [])]
}

function matchesSuggestion() {
  return POS_ORDER.every((pos) => selected.value[pos] === suggestion.value[pos]?.starter?.id)
}

async function approve() {
  const ids = POS_ORDER.map((pos) => selected.value[pos]).filter(Boolean)
  await api.approveLineup({
    player_ids: ids,
    opponent: opponent.value,
    match_date: matchDate.value,
    matches_system_suggestion: matchesSuggestion(),
  })
  saved.value = true
}
</script>

<template>
  <div class="container">
    <h1>Стартовая пятёрка</h1>
    <p class="muted">
      Базовое предложение системы — игрок с максимальным R* на каждую позицию.
      Окончательное решение принимает тренер с учётом контекста матча.
    </p>

    <div class="panel">
      <table>
        <thead><tr><th>Позиция</th><th>Выбор</th><th>R*</th><th>Альтернативы (разрыв)</th></tr></thead>
        <tbody>
          <tr v-for="pos in POS_ORDER" :key="pos">
            <td><span class="badge pos">{{ pos }}</span></td>
            <td>
              <select v-model="selected[pos]">
                <option v-for="o in optionsFor(pos)" :key="o.id" :value="o.id">
                  {{ o.name }} (R* {{ o.R_star }})
                </option>
              </select>
            </td>
            <td class="rating" style="font-size:14px">
              {{ optionsFor(pos).find((o) => o.id === selected[pos])?.R_star ?? '' }}
            </td>
            <td class="muted">
              <span v-if="suggestion[pos]?.margin != null">разрыв с альтернативой: {{ suggestion[pos].margin }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="panel" v-if="auth.isHeadCoach">
      <h3>Утверждение состава на матч</h3>
      <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end">
        <div><label class="hint">Дата матча</label><br /><input type="date" v-model="matchDate" /></div>
        <div><label class="hint">Соперник</label><br /><input v-model="opponent" placeholder="название команды" /></div>
        <button class="btn" @click="approve">Утвердить пятёрку</button>
      </div>
      <p v-if="saved" style="color:var(--good)">
        Состав утверждён{{ matchesSuggestion() ? ' (совпадает с предложением системы)' : ' (с корректировкой тренера)' }}.
      </p>
    </div>
    <p v-else class="muted">Утвердить состав может только главный тренер (раздел 2.5.2).</p>
  </div>
</template>

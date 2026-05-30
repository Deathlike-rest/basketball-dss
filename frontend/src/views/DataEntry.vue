<script setup>
import { onMounted, ref, computed } from 'vue'
import { api } from '../api/client'

// Ввод данных (раздел 2.5.3).
// Прогрессивное раскрытие: сначала только выбор игрока; после выбора появляются
// дата и поля по всем 21 атрибуту (таблицы 1, 3, 5), сгруппированные по категориям.
const players = ref([])
const schema = ref([])              // категории с атрибутами (с бэкенда)
const selectedPlayer = ref('')
const measuredOn = ref(new Date().toISOString().slice(0, 10))
const values = ref({})              // код атрибута -> введённое значение
const message = ref('')
const error = ref('')
const saving = ref(false)

const EXPERT_LEVELS = [
  { v: 1, label: '1 — Начальный' },
  { v: 2, label: '2 — Базовый' },
  { v: 3, label: '3 — Средний' },
  { v: 4, label: '4 — Выше среднего' },
  { v: 5, label: '5 — Продвинутый' },
]

const playerSelected = computed(() => !!selectedPlayer.value)
const filledCount = computed(
  () => Object.values(values.value).filter((v) => v !== '' && v != null).length,
)

onMounted(async () => {
  const [p, s] = await Promise.all([api.players(), api.dataSchema()])
  players.value = p.data
  schema.value = s.data
})

function onPlayerChange() {
  // При смене игрока очищаем форму.
  values.value = {}
  message.value = ''
  error.value = ''
}

async function save() {
  error.value = ''
  message.value = ''
  saving.value = true
  try {
    const { data } = await api.addRawBatch({
      player_id: selectedPlayer.value,
      date: measuredOn.value,
      values: values.value,
    })
    message.value = `Сохранено показателей: ${data.saved} (пропущено пустых: ${data.skipped}).`
    values.value = {}
  } catch (e) {
    error.value = e?.response?.data?.error || 'Ошибка сохранения'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="container">
    <h1>Ввод данных</h1>

    <!-- Шаг 1: выбор игрока (до выбора больше ничего не показываем) -->
    <div class="panel">
      <label class="hint">Игрок</label>
      <div>
        <select v-model="selectedPlayer" @change="onPlayerChange" style="min-width:280px">
          <option value="" disabled>— выберите игрока —</option>
          <option v-for="p in players" :key="p.id" :value="p.id">
            {{ p.full_name }} ({{ p.position }})
          </option>
        </select>
      </div>
      <p v-if="!playerSelected" class="hint" style="margin-top:10px">
        Выберите игрока, чтобы заполнить показатели по атрибутам.
      </p>
    </div>

    <!-- Шаг 2: после выбора игрока — дата и поля по всем атрибутам -->
    <template v-if="playerSelected">
      <div class="panel">
        <label class="hint">Дата измерения</label>
        <div><input type="date" v-model="measuredOn" /></div>
      </div>

      <div v-for="group in schema" :key="group.category" class="panel">
        <h3>{{ group.category }}</h3>
        <table>
          <thead>
            <tr><th>Атрибут</th><th>Что вводится</th><th style="width:200px">Значение</th></tr>
          </thead>
          <tbody>
            <tr v-for="attr in group.attributes" :key="attr.code">
              <td>{{ attr.name }} <span class="muted">({{ attr.code }})</span></td>
              <td class="muted">{{ attr.metric }}</td>
              <td>
                <select v-if="attr.kind === 'expert'" v-model.number="values[attr.code]" style="width:100%">
                  <option value="">—</option>
                  <option v-for="lvl in EXPERT_LEVELS" :key="lvl.v" :value="lvl.v">{{ lvl.label }}</option>
                </select>
                <span v-else style="display:flex; align-items:center; gap:6px">
                  <input type="number" step="0.01" v-model="values[attr.code]" style="width:110px" />
                  <span class="muted">{{ attr.unit }}</span>
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="panel" style="position:sticky; bottom:0">
        <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap">
          <button class="btn" :disabled="saving || filledCount === 0" @click="save">
            Сохранить показатели
          </button>
          <span class="muted">Заполнено полей: {{ filledCount }} из 21</span>
          <span v-if="message" style="color:var(--good)">{{ message }}</span>
          <span v-if="error" style="color:var(--bad)">{{ error }}</span>
        </div>
        <p class="hint">Незаполненные поля не сохраняются. Данные поступают как сырые показатели (этап 1 алгоритма, раздел 2.4.1).</p>
      </div>
    </template>
  </div>
</template>

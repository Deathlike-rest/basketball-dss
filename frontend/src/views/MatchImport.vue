<script setup>
import { ref, computed } from 'vue'
import { api } from '../api/client'

// Импорт матчевого протокола (раздел 2.5.3): загрузка CSV игры → автосопоставление
// игроков по id → валидация → превью → запись в БД (сырые показатели, source_type=1).
const matchDate = ref(new Date().toISOString().slice(0, 10))
const opponent = ref('')
const csv = ref(
  `player_id,player_name,minutes,pts,fgm,fga,tpm,tpa,ftm,fta,oreb,dreb,ast,tov,stl,blk,pf
1,Соколов Артём,32,18,6,13,3,7,3,4,1,4,7,2,2,0,2
5,Волков Максим,28,22,8,15,4,9,2,2,0,3,3,3,1,1,3`,
)
const preview = ref(null)
const result = ref(null)
const error = ref('')
const busy = ref(false)

const canImport = computed(() => preview.value && preview.value.summary.valid > 0)

async function doPreview() {
  error.value = ''
  result.value = null
  busy.value = true
  try {
    const { data } = await api.matchImportPreview(csv.value)
    preview.value = data
  } catch (e) {
    error.value = e?.response?.data?.error || 'Ошибка превью'
  } finally {
    busy.value = false
  }
}

async function doImport() {
  error.value = ''
  busy.value = true
  try {
    const { data } = await api.matchImportCommit({
      date: matchDate.value,
      opponent: opponent.value,
      csv: csv.value,
    })
    result.value = data
    preview.value = null
  } catch (e) {
    error.value = e?.response?.data?.error || 'Ошибка импорта'
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="container">
    <h1>Импорт данных с игры</h1>
    <p class="muted">
      Загрузка официального протокола матча (тип 1, раздел 2.3.1). Игроки сопоставляются
      по идентификатору, данные проверяются, превью показывается перед записью в БД.
    </p>

    <div class="panel">
      <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:flex-end; margin-bottom:12px">
        <div><label class="hint">Дата матча</label><br /><input type="date" v-model="matchDate" /></div>
        <div><label class="hint">Соперник</label><br /><input v-model="opponent" placeholder="название команды" /></div>
      </div>
      <label class="hint">CSV-протокол (колонки: player_id, player_name, minutes, pts, fgm, fga, tpm, tpa, ftm, fta, oreb, dreb, ast, tov, stl, blk, pf)</label>
      <textarea v-model="csv" rows="7" style="width:100%; font-family:monospace; font-size:12px; margin-top:6px"></textarea>
      <div style="display:flex; gap:10px; margin-top:10px">
        <button class="btn secondary" :disabled="busy" @click="doPreview">Превью</button>
        <button class="btn" :disabled="busy || !canImport" @click="doImport">
          Импортировать{{ preview ? ` (${preview.summary.valid})` : '' }}
        </button>
      </div>
      <p v-if="error" style="color:var(--bad)">{{ error }}</p>
    </div>

    <!-- Превью с результатом сопоставления и валидации -->
    <div v-if="preview" class="panel">
      <h3>
        Превью: всего {{ preview.summary.total }},
        корректных <span style="color:var(--good)">{{ preview.summary.valid }}</span>,
        с ошибками <span style="color:var(--bad)">{{ preview.summary.invalid }}</span>
      </h3>
      <table>
        <thead>
          <tr><th></th><th>Игрок</th><th>МИН</th><th>ОЧ</th><th>FG%</th><th>3P%</th><th>FT%</th><th>AST/TO</th><th>Проблемы</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in preview.rows" :key="r.line">
            <td>{{ r.valid ? '✓' : '✕' }}</td>
            <td :style="{ color: r.valid ? 'var(--text)' : 'var(--bad)' }">{{ r.player_name }}</td>
            <td>{{ r.stats.minutes }}</td>
            <td>{{ r.stats.pts }}</td>
            <td>{{ r.fg_pct ?? '—' }}</td>
            <td>{{ r.tp_pct ?? '—' }}</td>
            <td>{{ r.ft_pct ?? '—' }}</td>
            <td>{{ r.stats.ast }}/{{ r.stats.tov }}</td>
            <td style="color:var(--bad); font-size:12px">{{ r.errors.join('; ') }}</td>
          </tr>
        </tbody>
      </table>
      <p class="hint">Невалидные строки при импорте пропускаются.</p>
    </div>

    <!-- Результат импорта -->
    <div v-if="result" class="panel">
      <p style="color:var(--good)">
        Импортировано игроков: {{ result.saved_players }}, показателей: {{ result.saved_metrics }}.
      </p>
      <p class="hint">
        Записаны сырые показатели матча (этап 1 алгоритма). Их можно увидеть в карточке игрока на вкладке «Данные».
      </p>
    </div>
  </div>
</template>

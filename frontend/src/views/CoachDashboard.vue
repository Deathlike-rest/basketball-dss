<script setup>
import { onMounted, ref } from 'vue'
import client, { api } from '../api/client'

// Экран главного тренера: четыре блока (раздел 2.5.2, рисунок 8):
// стартовая пятёрка · список игроков с R* и трендом · лента предупреждений · ближайший матч.
const team = ref([])
const lineup = ref({})
const alerts = ref([])
const validation = ref(null)
const loading = ref(true)

const POS_ORDER = ['PG', 'SG', 'SF', 'PF', 'C']
const trendSign = { up: '▲', down: '▼', flat: '–' }

onMounted(async () => {
  const [t, l, a, v] = await Promise.all([
    api.teamRatings(),
    api.lineupSuggestion(),
    api.alerts().catch(() => ({ data: [] })),
    client.get('/ratings/validation').catch(() => ({ data: null })),
  ])
  team.value = t.data.sort((x, y) => y.R_star - x.R_star)
  lineup.value = l.data
  alerts.value = a.data
  validation.value = v.data
  loading.value = false
})
</script>

<template>
  <div class="container">
    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px">
      <h1>Экран тренера</h1>
      <div style="display:flex; gap:10px">
        <a class="btn secondary" :href="api.teamCsvUrl()">Экспорт CSV</a>
        <router-link class="btn" to="/report">Отчёт / печать</router-link>
      </div>
    </div>
    <div v-if="loading" class="muted">Загрузка…</div>
    <div v-else class="grid grid-dash">
      <!-- Блок 1: список игроков команды с R* и тенденцией -->
      <div class="panel">
        <h3>Состав команды</h3>
        <p v-if="validation" class="hint">
          Согласованность с экспертной оценкой (ρ Спирмена): <strong>{{ validation.spearman }}</strong>
          (p = {{ validation.p_value < 0.001 ? '< 0,001' : validation.p_value.toFixed(3) }})
        </p>
        <table>
          <thead>
            <tr><th>Игрок</th><th>Поз.</th><th>R*</th><th>Тренд</th></tr>
          </thead>
          <tbody>
            <tr v-for="p in team" :key="p.player_id">
              <td><router-link :to="`/player/${p.player_id}`">{{ p.name }}</router-link></td>
              <td><span class="badge pos">{{ p.position }}</span></td>
              <td class="rating">{{ p.R_star }}</td>
              <td :class="`trend-${p.trend}`">{{ trendSign[p.trend] }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div>
        <!-- Блок 2: предложенная стартовая пятёрка на ближайший матч -->
        <div class="panel">
          <h3>Предложенная стартовая пятёрка</h3>
          <table>
            <tbody>
              <tr v-for="pos in POS_ORDER" :key="pos">
                <td><span class="badge pos">{{ pos }}</span></td>
                <td>
                  <template v-if="lineup[pos] && lineup[pos].starter">
                    <router-link :to="`/player/${lineup[pos].starter.id}`">{{ lineup[pos].starter.name }}</router-link>
                  </template>
                  <span v-else class="muted">нет игрока</span>
                </td>
                <td class="rating">{{ lineup[pos]?.starter?.R_star ?? '' }}</td>
              </tr>
            </tbody>
          </table>
          <router-link to="/lineup" class="hint">Открыть конструктор состава →</router-link>
        </div>

        <!-- Блок 3: лента раннего предупреждения (сценарий 3) -->
        <div class="panel">
          <h3>Раннее предупреждение</h3>
          <p v-if="!alerts.length" class="muted">Нет активных предупреждений.</p>
          <div v-for="(a, i) in alerts" :key="i" class="alert-item" :class="{ high: a.priority === 'high' }">
            <strong>
              <router-link :to="`/player/${a.player_id}`">{{ a.player_name }}</router-link>
            </strong>
            <span v-if="a.priority === 'high'" style="color:var(--bad)"> · атлетический</span>
            <div style="font-size:13px">
              «{{ a.name }}»: {{ a.baseline }} → {{ a.current }}
              (−{{ a.drop }}{{ a.sigma ? `, ${a.sigma}σ` : '' }})
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

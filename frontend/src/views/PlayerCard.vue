<script setup>
import { onMounted, ref, computed } from 'vue'
import { api } from '../api/client'
import { useAuthStore } from '../store/auth'
import AttributeRadar from '../components/AttributeRadar.vue'
import RatingTrendChart from '../components/RatingTrendChart.vue'

// Карточка игрока — пять вкладок (раздел 2.5.2):
// Профиль · Атрибуты · История · Рекомендации · Данные (последняя — только штаб).
const props = defineProps({ id: { type: String, required: true } })
const auth = useAuthStore()
const data = ref(null)
const tab = ref('attributes')

const tabs = computed(() => {
  const base = [
    ['profile', 'Профиль'],
    ['attributes', 'Атрибуты'],
    ['history', 'История'],
    ['recommendations', 'Рекомендации'],
  ]
  if (auth.isStaff) base.push(['data', 'Данные'])
  return base
})

const sourceNames = {
  1: 'Матчевая статистика', 2: 'Продвинутая статистика', 3: 'Физические тесты',
  4: 'Видеоанализ', 5: 'Трекинг', 6: 'Экспертная оценка',
}

onMounted(async () => {
  const { data: d } = await api.player(props.id)
  data.value = d
})

const rating = computed(() => data.value?.attributes?.rating)
</script>

<template>
  <div class="container" v-if="data">
    <h1>
      {{ data.profile.full_name }}
      <span class="badge pos">{{ data.profile.primary_position }}</span>
      <span class="rating" style="float:right">R* {{ rating?.R_star }}</span>
    </h1>
    <p class="muted">{{ data.profile.position_name }} · {{ data.profile.team }}</p>

    <a class="btn secondary" :href="api.playerCsvUrl(id)" style="display:inline-block; margin-bottom:12px">Экспорт игрока (CSV)</a>

    <div class="tabs">
      <div v-for="[key, label] in tabs" :key="key"
           class="tab" :class="{ active: tab === key }" @click="tab = key">{{ label }}</div>
    </div>

    <!-- Профиль -->
    <div v-if="tab === 'profile'" class="panel">
      <table>
        <tbody>
          <tr><th>Позиция</th><td>{{ data.profile.position_name }} ({{ data.profile.primary_position }})</td></tr>
          <tr><th>Дата рождения</th><td>{{ data.profile.birth_date }}</td></tr>
          <tr><th>Рост</th><td>{{ data.profile.height_cm }} см</td></tr>
          <tr><th>Вес</th><td>{{ data.profile.weight_kg }} кг</td></tr>
          <tr><th>Размах рук</th><td>{{ data.profile.wingspan_cm }} см</td></tr>
          <tr><th>Согласие на обработку ПДн</th><td>{{ data.profile.consent_signed ? 'подписано' : 'нет' }}</td></tr>
        </tbody>
      </table>
    </div>

    <!-- Атрибуты: радар + таблица процентилей + вектор позиций -->
    <div v-if="tab === 'attributes'" class="grid grid-2">
      <div class="panel"><AttributeRadar :rows="data.attributes.rows" /></div>
      <div class="panel">
        <h3>Баллы по атрибутам</h3>
        <table>
          <thead><tr><th>Атрибут</th><th>Категория</th><th>Балл</th><th>Проц.</th></tr></thead>
          <tbody>
            <tr v-for="r in data.attributes.rows" :key="r.code">
              <td>{{ r.name }}</td>
              <td class="muted">{{ r.category }}</td>
              <td class="rating" style="font-size:14px">{{ r.score }}</td>
              <td>
                {{ r.percentile }}
                <span v-if="r.is_indicative" class="indicative">ориент.</span>
              </td>
            </tr>
          </tbody>
        </table>
        <h3 style="margin-top:16px">Вектор позиций (универсальность)</h3>
        <table>
          <tbody>
            <tr v-for="(val, pos) in rating.position_vector" :key="pos">
              <td><span class="badge pos">{{ pos }}</span></td>
              <td class="rating" style="font-size:14px">{{ val }}</td>
            </tr>
          </tbody>
        </table>
        <p class="hint">Модификаторы: M_IQ {{ rating.modifiers.M_IQ }} · M_S {{ rating.modifiers.M_S }} · M_L {{ rating.modifiers.M_L }}</p>
      </div>
    </div>

    <!-- История: динамика рейтинга -->
    <div v-if="tab === 'history'" class="panel">
      <h3>Динамика рейтинга за сезон</h3>
      <RatingTrendChart :ratings="data.history.ratings" />
    </div>

    <!-- Рекомендации (сценарий 2) -->
    <div v-if="tab === 'recommendations'" class="panel">
      <h3>Индивидуальные рекомендации</h3>
      <p v-if="!data.recommendations.length" class="muted">
        Все атрибуты на уровне или выше среднего по позиции в команде.
      </p>
      <div v-for="rec in data.recommendations" :key="rec.attribute" class="alert-item">
        <strong>{{ rec.name }}</strong> ({{ rec.category }})
        — балл {{ rec.score }} при среднем по позиции {{ rec.team_avg }}
        <span style="color:var(--bad)">(−{{ rec.gap }})</span>
        <ul style="margin:6px 0 0 18px">
          <li v-for="ex in rec.exercises" :key="ex">{{ ex }}</li>
        </ul>
      </div>
    </div>

    <!-- Данные (только штаб) -->
    <div v-if="tab === 'data' && data.data" class="panel">
      <h3>Сырые показатели</h3>
      <table>
        <thead><tr><th>Дата</th><th>Источник</th><th>Показатель</th><th>Значение</th></tr></thead>
        <tbody>
          <tr v-for="(d, i) in data.data" :key="i">
            <td>{{ d.date }}</td>
            <td class="muted">{{ sourceNames[d.source_type] }}</td>
            <td>{{ d.metric }}</td>
            <td>{{ d.value }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

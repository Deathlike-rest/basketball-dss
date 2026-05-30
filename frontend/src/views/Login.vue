<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const router = useRouter()
const login = ref('coach')
const password = ref('coach123')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    const user = await auth.login(login.value, password.value)
    router.push(user.role === 'player' ? `/player/${user.player_id}` : '/')
  } catch (e) {
    error.value = e?.response?.data?.error || 'Ошибка входа'
  }
}
</script>

<template>
  <div class="container">
    <div class="panel login-box">
      <h2>СППР · Оценка баскетболистов</h2>
      <p class="muted">Система поддержки принятия решений тренерского штаба</p>
      <form @submit.prevent="submit">
        <div class="field">
          <label>Логин</label>
          <input v-model="login" autocomplete="username" />
        </div>
        <div class="field">
          <label>Пароль</label>
          <input v-model="password" type="password" autocomplete="current-password" />
        </div>
        <button class="btn" type="submit" style="width:100%">Войти</button>
        <p v-if="error" style="color:var(--bad)">{{ error }}</p>
      </form>
      <div class="hint">
        Демо-доступы: coach/coach123 · assist/assist123 · analyst/analyst123 · player1/player123
      </div>
    </div>
  </div>
</template>

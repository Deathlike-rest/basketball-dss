<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from './store/auth'

const auth = useAuthStore()
const router = useRouter()

async function doLogout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div v-if="auth.isAuthenticated" class="app-header">
    <nav>
      <router-link v-if="auth.isStaff" to="/">Команда</router-link>
      <router-link v-if="auth.isStaff" to="/lineup">Стартовая пятёрка</router-link>
      <router-link v-if="auth.isStaff" to="/data">Ввод данных</router-link>
      <router-link v-else :to="`/player/${auth.user.player_id}`">Мой профиль</router-link>
    </nav>
    <div>
      <span class="muted">{{ auth.user.full_name }} · {{ auth.roleName }}</span>
      <button class="btn secondary" style="margin-left:12px" @click="doLogout">Выйти</button>
    </div>
  </div>
  <router-view />
</template>

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'

import App from './App.vue'
import Login from './views/Login.vue'
import CoachDashboard from './views/CoachDashboard.vue'
import PlayerCard from './views/PlayerCard.vue'
import LineupBuilder from './views/LineupBuilder.vue'
import DataEntry from './views/DataEntry.vue'
import { useAuthStore } from './store/auth'
import './style.css'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login, meta: { public: true } },
    { path: '/', component: CoachDashboard },
    { path: '/player/:id', component: PlayerCard, props: true },
    { path: '/lineup', component: LineupBuilder, meta: { staff: true } },
    { path: '/data', component: DataEntry, meta: { staff: true } },
  ],
})

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

const auth = useAuthStore()

// Защита маршрутов по аутентификации и роли (раздел 2.5.2).
router.beforeEach((to) => {
  if (to.meta.public) return true
  if (!auth.isAuthenticated) return '/login'
  // Игрок попадает только на свою карточку.
  if (auth.isPlayer && to.path === '/') return `/player/${auth.user.player_id}`
  if (to.meta.staff && !auth.isStaff) return '/'
  return true
})

// Восстанавливаем сессию до монтирования, затем запускаем приложение.
auth.fetchMe().finally(() => app.mount('#app'))

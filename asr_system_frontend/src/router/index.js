import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../views/Auth/LoginPage.vue';
import RegisterPage from '../views/Auth/RegisterPage.vue';
import Dashboard from '../views/Dashboard.vue';
import FileTranscription from '../views/FileTranscription.vue';
import RealtimeTranscription from '../views/RealtimeTranscription.vue';
// 1. 导入新的简易热词管理页面，而不是旧的
import SimpleHotwordManager from '../views/SimpleHotwordManager.vue';

const routes = [
  { path: '/login', component: LoginPage },
  { path: '/register', component: RegisterPage },
  { path: '/', component: Dashboard, meta: { requiresAuth: true } },
  { path: '/transcribe', component: FileTranscription, meta: { requiresAuth: true } },
  { path: '/realtime', component: RealtimeTranscription, meta: { requiresAuth: true } },
  // 2. 将 /hotwords 路由指向新的简易页面
  { path: '/hotwords', component: SimpleHotwordManager, meta: { requiresAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  // 简化认证逻辑
  const loggedIn = localStorage.getItem('token');
  if (to.matched.some(record => record.meta.requiresAuth) && !loggedIn) {
    next('/login');
  } else {
    next();
  }
});

export default router;
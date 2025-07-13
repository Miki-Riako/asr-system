import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../views/Auth/LoginPage.vue';
import RegisterPage from '../views/Auth/RegisterPage.vue';
import Dashboard from '../views/Dashboard.vue';
import FileTranscription from '../views/FileTranscription.vue';
import RealtimeTranscription from '../views/RealtimeTranscription.vue';
import TaskDetail from '../views/TaskDetail.vue';
import HotwordManagement from '../views/HotwordManagement.vue';

const routes = [
  { path: '/login', component: LoginPage },
  { path: '/register', component: RegisterPage },
  { path: '/', component: Dashboard },
  { path: '/transcribe', component: FileTranscription },
  { path: '/realtime', component: RealtimeTranscription },
  { path: '/task/:id', component: TaskDetail },
  { path: '/hotwords', component: HotwordManagement },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const publicPages = ['/login', '/register'];
  const authRequired = !publicPages.includes(to.path);
  const token = localStorage.getItem('token');
  if (authRequired && !token) {
    return next('/login');
  }
  next();
});

export default router; 
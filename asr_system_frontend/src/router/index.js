import { createRouter, createWebHistory } from 'vue-router';
import LoginPage from '../views/Auth/LoginPage.vue';
import RegisterPage from '../views/Auth/RegisterPage.vue';

const routes = [
  { path: '/login', component: LoginPage },
  { path: '/register', component: RegisterPage },
  { path: '/', redirect: '/login' },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router; 
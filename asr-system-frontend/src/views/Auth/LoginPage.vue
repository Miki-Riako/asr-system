<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="w-full max-w-md p-8 bg-gray-800 rounded-lg shadow-lg border border-gray-700">
      <h1 class="text-3xl font-bold text-center text-blue-400 mb-8">系统登录</h1>
      <el-form :model="form" ref="loginForm" class="space-y-4">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名/邮箱" prefix-icon="el-icon-user" size="large" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="el-icon-lock" size="large" show-password clearable />
        </el-form-item>
        <el-form-item>
          <div class="flex items-center gap-2">
            <el-input v-model="form.captcha" placeholder="输入验证码" maxlength="4" class="w-1/2" />
            <div class="captcha-box flex-1 h-12 flex items-center justify-center rounded bg-gray-900 border border-yellow-400 text-yellow-400 text-lg font-mono tracking-widest cursor-pointer select-none" @click="generateCaptcha" :title="'点击刷新'">{{ captcha }}</div>
          </div>
        </el-form-item>
        <div v-if="errorMsg" class="text-red-500 text-sm text-center mb-2">{{ errorMsg }}</div>
        <el-form-item>
          <el-button type="primary" size="large" class="w-full" @click="onSubmit">登录</el-button>
        </el-form-item>
        <div class="text-sm text-center mt-4">
          还没有账号？<router-link to="/register" class="text-blue-400 hover:underline">立即注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const form = ref({ username: '', password: '', captcha: '' });
const errorMsg = ref('');
const captcha = ref('');

function generateCaptcha() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 4; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  captcha.value = result;
}

function onSubmit() {
  if (!form.value.username || !form.value.password || !form.value.captcha) {
    errorMsg.value = '所有字段均为必填项。';
    return;
  }
  if (form.value.captcha.toUpperCase() !== captcha.value) {
    errorMsg.value = '验证码不正确。';
    generateCaptcha();
    return;
  }
  errorMsg.value = '';
  // 这里预留API集成，成功后跳转主页
  router.push('/');
}

generateCaptcha();
</script>

<style scoped>
.captcha-box {
  min-width: 80px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-family: 'Courier New', Courier, monospace;
  letter-spacing: 5px;
  user-select: none;
  cursor: pointer;
  background-color: #18181b;
  border: 1px solid #facc15;
  color: #facc15;
}
</style> 
<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="w-full max-w-md p-8 bg-gray-800 rounded-lg shadow-lg border border-gray-700">
      <h1 class="text-3xl font-bold text-center text-blue-400 mb-8">用户注册</h1>
      <el-form :model="form" ref="registerForm" class="space-y-4">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="el-icon-user" size="large" clearable />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="el-icon-lock" size="large" show-password clearable />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" placeholder="请再次输入密码" size="large" show-password clearable />
        </el-form-item>
        <div v-if="errorMsg" class="text-red-500 text-sm text-center mb-2">{{ errorMsg }}</div>
        <el-form-item>
          <el-button type="primary" size="large" class="w-full" @click="onSubmit" :loading="loading">注册</el-button>
        </el-form-item>
        <div class="text-sm text-center mt-4">
          已有账号？<router-link to="/login" class="text-blue-400 hover:underline">立即登录</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { authAPI } from '../../services/api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const form = ref({ username: '', password: '', confirmPassword: '' });
const errorMsg = ref('');
const loading = ref(false);

async function onSubmit() {
  if (!form.value.username || !form.value.password || !form.value.confirmPassword) {
    errorMsg.value = '所有字段均为必填项。';
    return;
  }
  if (form.value.password !== form.value.confirmPassword) {
    errorMsg.value = '两次输入的密码不一致。';
    return;
  }
  
  loading.value = true;
  errorMsg.value = '';
  
  try {
    await authAPI.register(form.value.username, form.value.password);
    ElMessage({
      message: '注册成功！将返回登录页面。',
      type: 'success'
    });
    router.push('/login');
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '注册失败';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
</style> 
<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">支持热词预测的语音识别系统</h1>
        <div class="flex items-center gap-4">
          <span>{{ username }}</span>
          <el-button type="danger" size="small" @click="logout">退出登录</el-button>
        </div>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4">
      <h2 class="text-2xl font-bold mb-6">欢迎使用语音识别系统</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <!-- 卡片1: 离线文件转写 -->
        <el-card class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all">
          <template #header>
            <div class="flex items-center">
              <span>离线文件转写</span>
            </div>
          </template>
          <div class="text-gray-400">
            上传音频文件，系统会自动进行转写并返回文本结果。
          </div>
          <el-button type="primary" class="mt-4 w-full" @click="$router.push('/transcribe')">开始转写</el-button>
        </el-card>
        
        <!-- 卡片2: 实时语音转写 -->
        <el-card class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all">
          <template #header>
            <div class="flex items-center">
              <span>实时语音转写</span>
            </div>
          </template>
          <div class="text-gray-400">
            使用麦克风进行实时录音，系统会即时转写您的语音内容。
          </div>
          <el-button type="success" class="mt-4 w-full" @click="$router.push('/realtime')">开始实时转写</el-button>
        </el-card>
        
        <!-- 卡片3: 热词管理 (已修改) -->
        <el-card class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all">
          <template #header>
            <div class="flex items-center">
              <span>热词管理</span>
            </div>
          </template>
          <div class="text-gray-400">
            添加和管理您的专业领域词汇，提高语音识别准确率。
          </div>
          <!-- 
            !!! 这是唯一的修改 !!!
            我们将按钮包裹在一个 <a> 标签里，让它可以打开一个新的页面。
            target="_blank" 会在新标签页中打开，体验更好。
          -->
          <a href="http://127.0.0.1:8765" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">
            <el-button type="warning" class="mt-4 w-full">管理热词</el-button>
          </a>
        </el-card>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { authAPI } from '../services/api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const username = ref('用户');

onMounted(async () => {
  try {
    const userData = await authAPI.getCurrentUser();
    username.value = userData.username;
  } catch (err) {
    if (err.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录');
      logout();
    }
  }
});

function logout() {
  localStorage.removeItem('token');
  router.push('/login');
}
</script>

<style scoped>
:deep(.el-card) {
  background-color: #374151;
  border: none;
}
:deep(.el-card__header) {
  background-color: rgba(17, 24, 39, 0.4);
  padding: 12px 16px;
}
</style>
<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-purple-900 to-pink-900 relative overflow-hidden">
    <!-- 动态背景粒子 -->
    <div class="fixed inset-0 pointer-events-none">
      <div
        v-for="particle in particles"
        :key="particle.id"
        class="absolute rounded-full opacity-40"
        :style="{
          left: particle.x + '%',
          top: particle.y + '%',
          width: particle.size + 'px',
          height: particle.size + 'px',
          backgroundColor: particle.color,
          animation: `twinkle ${particle.duration}s ease-in-out infinite alternate`
        }"
      />
    </div>

    <!-- 背景网格 -->
    <div class="absolute inset-0 opacity-10">
      <div class="w-full h-full grid-background"></div>
    </div>

    <!-- 主要内容区域 -->
    <div class="relative z-10 w-full max-w-md mx-4">
      <!-- 顶部Logo区域 -->
      <div class="text-center mb-8">
        <div 
          class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-r from-purple-500 to-pink-600 mb-4 transition-all duration-500 shadow-2xl"
          :class="glowEffect ? 'shadow-purple-500/50 scale-110' : 'shadow-lg'"
        >
          <el-icon class="text-white" size="32"><UserFilled /></el-icon>
        </div>
        <h1 class="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          语音识别系统
        </h1>
        <p class="text-gray-300">加入我们，开启智能语音新体验</p>
      </div>

      <!-- 注册卡片 -->
      <div class="bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 shadow-2xl p-8 relative overflow-hidden">
        <!-- 卡片内部光效 -->
        <div class="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-2xl"></div>
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 to-pink-500"></div>
        
        <div class="relative z-10">
          <h1 class="text-2xl font-bold text-center text-white mb-8">用户注册</h1>
          
          <div class="space-y-6">
            <!-- 用户名输入 -->
            <div class="relative group">
              <el-icon class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-purple-400 transition-colors z-10" size="20">
                <User />
              </el-icon>
              <input
                v-model="form.username"
                type="text"
                placeholder="请输入用户名"
                class="w-full pl-12 pr-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-purple-400 focus:bg-white/20 transition-all duration-300"
                style="backdrop-filter: blur(4px);"
              />
              <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/20 to-pink-500/20 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            <!-- 密码输入 -->
            <div class="relative group">
              <el-icon class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-green-400 transition-colors z-10" size="20">
                <Lock />
              </el-icon>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                class="w-full pl-12 pr-12 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-green-400 focus:bg-white/20 transition-all duration-300"
                style="backdrop-filter: blur(4px);"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors z-10"
              >
                <el-icon size="20">
                  <View v-if="!showPassword" />
                  <Hide v-else />
                </el-icon>
              </button>
              <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-green-500/20 to-teal-500/20 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            <!-- 确认密码输入 -->
            <div class="relative group">
              <el-icon class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-orange-400 transition-colors z-10" size="20">
                <Lock />
              </el-icon>
              <input
                v-model="form.confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                placeholder="请再次输入密码"
                class="w-full pl-12 pr-12 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-orange-400 focus:bg-white/20 transition-all duration-300"
                style="backdrop-filter: blur(4px);"
              />
              <button
                type="button"
                @click="showConfirmPassword = !showConfirmPassword"
                class="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors z-10"
              >
                <el-icon size="20">
                  <View v-if="!showConfirmPassword" />
                  <Hide v-else />
                </el-icon>
              </button>
              <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-orange-500/20 to-red-500/20 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            </div>

            <!-- 错误信息 -->
            <div v-if="errorMsg" class="text-red-400 text-sm text-center mb-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg backdrop-blur-sm">
              {{ errorMsg }}
            </div>

            <!-- 注册按钮 -->
            <button
              type="button"
              @click="onSubmit"
              :disabled="loading"
              class="w-full py-4 bg-gradient-to-r from-purple-500 to-pink-600 text-white font-semibold rounded-xl hover:from-purple-600 hover:to-pink-700 transform hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-2xl focus:outline-none focus:ring-4 focus:ring-purple-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="!loading" class="flex items-center justify-center">
                注册
                <el-icon class="ml-2" size="20"><Plus /></el-icon>
              </span>
              <span v-else class="flex items-center justify-center">
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                注册中...
              </span>
            </button>

            <!-- 登录链接 -->
            <div class="text-sm text-center mt-6">
              <p class="text-gray-300">
                已有账号？
                <router-link to="/login" class="ml-2 text-purple-400 hover:text-purple-300 font-semibold transition-colors">
                  立即登录
                </router-link>
              </p>
            </div>
          </div>

          <!-- 装饰性元素 -->
          <div class="absolute -top-4 -right-4 w-24 h-24 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full blur-xl"></div>
          <div class="absolute -bottom-4 -left-4 w-32 h-32 bg-gradient-to-br from-pink-500/20 to-red-500/20 rounded-full blur-xl"></div>
        </div>
      </div>

      <!-- 底部装饰 -->
      <div class="text-center mt-8 text-gray-400">
        <p class="text-sm">© 2025 语音识别系统. 保留所有权利.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { authAPI } from '../../services/api';
import { ElMessage } from 'element-plus';
import { User, Lock, View, Hide, Plus, UserFilled } from '@element-plus/icons-vue';

const router = useRouter();
const form = ref({ username: '', password: '', confirmPassword: '' });
const errorMsg = ref('');
const loading = ref(false);
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const particles = ref([]);
const glowEffect = ref(false);

let animationIntervals = [];

// 生成背景粒子
function generateParticles() {
  const newParticles = [];
  for (let i = 0; i < 50; i++) {
    newParticles.push({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      duration: Math.random() * 3 + 2,
      color: `hsl(${Math.random() * 60 + 280}, 70%, 60%)` // 紫色-粉色范围
    });
  }
  particles.value = newParticles;
}

// 注册提交
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

onMounted(() => {
  generateParticles();
  
  // 粒子动画
  const particleInterval = setInterval(() => {
    generateParticles();
  }, 5000);
  
  // 光效动画
  const glowInterval = setInterval(() => {
    glowEffect.value = !glowEffect.value;
  }, 2000);
  
  animationIntervals.push(particleInterval, glowInterval);
});

onUnmounted(() => {
  animationIntervals.forEach(interval => clearInterval(interval));
});
</script>

<style scoped>
.grid-background {
  background-image: 
    linear-gradient(rgba(147, 51, 234, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(147, 51, 234, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
}

/* 自定义动画 */
@keyframes twinkle {
  0% { opacity: 0.3; transform: scale(0.8); }
  100% { opacity: 0.8; transform: scale(1.2); }
}

/* 背景模糊效果 */
.backdrop-blur-lg {
  backdrop-filter: blur(16px);
}

/* 渐变文字效果 */
.bg-clip-text {
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
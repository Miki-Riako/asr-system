<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 relative overflow-hidden">
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
          class="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 mb-4 transition-all duration-500 shadow-2xl"
          :class="glowEffect ? 'shadow-blue-500/50 scale-110' : 'shadow-lg'"
        >
          <el-icon class="text-white" size="32"><Headset /></el-icon>
        </div>
        <h1 class="text-4xl font-bold text-white mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          语音识别系统
        </h1>
        <p class="text-gray-300">智能语音，未来科技</p>
      </div>

      <!-- 登录卡片 -->
      <div class="bg-white/10 backdrop-blur-lg rounded-2xl border border-white/20 shadow-2xl p-8 relative overflow-hidden">
        <!-- 卡片内部光效 -->
        <div class="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-2xl"></div>
        <div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-purple-500"></div>
        
        <div class="relative z-10">
          <h1 class="text-2xl font-bold text-center text-white mb-8">系统登录</h1>
          
          <div class="space-y-6">
            <!-- 用户名输入 -->
            <div prop="username">
              <div class="relative group">
                <el-icon class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-blue-400 transition-colors z-10" size="20">
                  <User />
                </el-icon>
                <input
                  v-model="form.username"
                  type="text"
                  placeholder="请输入用户名/邮箱"
                  class="w-full pl-12 pr-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-blue-400 focus:bg-white/20 transition-all duration-300"
                  style="backdrop-filter: blur(4px);"
                />
                <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/20 to-purple-500/20 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
              </div>
            </div>

            <!-- 密码输入 -->
            <div prop="password">
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
            </div>

            <!-- 验证码输入 -->
            <div>
              <div class="flex items-center gap-3">
                <div class="relative group flex-1">
                  <el-icon class="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 group-focus-within:text-yellow-400 transition-colors z-10" size="20">
                    <Key />
                  </el-icon>
                  <input
                    v-model="form.captcha"
                    type="text"
                    placeholder="输入验证码"
                    maxlength="4"
                    class="w-full pl-12 pr-4 py-4 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-yellow-400 focus:bg-white/20 transition-all duration-300"
                    style="backdrop-filter: blur(4px);"
                  />
                  <div class="absolute inset-0 rounded-xl bg-gradient-to-r from-yellow-500/20 to-orange-500/20 opacity-0 group-focus-within:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
                </div>
                <div 
                  class="captcha-box h-14 px-4 flex items-center justify-center rounded-xl bg-gradient-to-r from-yellow-400/20 to-orange-400/20 border border-yellow-400/50 text-yellow-300 text-xl font-mono tracking-widest cursor-pointer select-none backdrop-blur-sm hover:shadow-lg hover:shadow-yellow-500/25 transition-all duration-300 transform hover:scale-105"
                  @click="generateCaptcha"
                  :title="'点击刷新'"
                >
                  {{ captcha }}
                </div>
              </div>
            </div>

            <!-- 错误信息 -->
            <div v-if="errorMsg" class="text-red-400 text-sm text-center mb-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg backdrop-blur-sm">
              {{ errorMsg }}
            </div>

            <!-- 登录按钮 -->
            <div>
              <button
                type="button"
                @click="onSubmit"
                :disabled="loading"
                class="w-full py-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-600 hover:to-purple-700 transform hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-2xl focus:outline-none focus:ring-4 focus:ring-blue-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span v-if="!loading" class="flex items-center justify-center">
                  登录
                  <el-icon class="ml-2" size="20"><Promotion /></el-icon>
                </span>
                <span v-else class="flex items-center justify-center">
                  <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  登录中...
                </span>
              </button>
            </div>

            <!-- 注册链接 -->
            <div class="text-sm text-center mt-6">
              <p class="text-gray-300">
                还没有账号？
                <router-link to="/register" class="ml-2 text-blue-400 hover:text-blue-300 font-semibold transition-colors">
                  立即注册
                </router-link>
              </p>
            </div>
          </div>

          <!-- 装饰性元素 -->
          <div class="absolute -top-4 -right-4 w-24 h-24 bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-full blur-xl"></div>
          <div class="absolute -bottom-4 -left-4 w-32 h-32 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full blur-xl"></div>
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
import { User, Lock, Key, View, Hide, Promotion, Headset } from '@element-plus/icons-vue';

const router = useRouter();
const form = ref({ username: '', password: '', captcha: '' });
const errorMsg = ref('');
const captcha = ref('');
const loading = ref(false);
const showPassword = ref(false);
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
      color: `hsl(${Math.random() * 60 + 200}, 70%, 60%)`
    });
  }
  particles.value = newParticles;
}

// 生成验证码
function generateCaptcha() {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
  let result = '';
  for (let i = 0; i < 4; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  captcha.value = result;
}

// 登录提交
async function onSubmit() {
  if (!form.value.username || !form.value.password || !form.value.captcha) {
    errorMsg.value = '所有字段均为必填项。';
    return;
  }
  if (form.value.captcha.toUpperCase() !== captcha.value) {
    errorMsg.value = '验证码不正确。';
    generateCaptcha();
    return;
  }

  loading.value = true;
  errorMsg.value = '';

  try {
    const res = await authAPI.login(form.value.username, form.value.password);
    localStorage.setItem('token', res.access_token);
    router.push('/');
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || '登录失败，请检查用户名和密码';
    generateCaptcha();
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  generateCaptcha();
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
    linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
    linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px);
  background-size: 50px 50px;
}

.captcha-box {
  min-width: 100px;
  font-family: 'Courier New', Courier, monospace;
  user-select: none;
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

/* 隐藏 Element Plus 默认的 input 样式 */
:deep(.el-form-item) {
  margin-bottom: 0;
}

:deep(.el-form-item__content) {
  line-height: normal;
}

/* 渐变文字效果 */
.bg-clip-text {
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
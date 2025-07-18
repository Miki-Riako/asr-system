<template>
  <div class="min-h-screen bg-gray-900 text-gray-200 relative overflow-hidden">
    <!-- 动态背景粒子 -->
    <div class="fixed inset-0 pointer-events-none">
      <div
        v-for="particle in particles"
        :key="particle.id"
        class="absolute rounded-full bg-blue-400 opacity-30"
        :style="{
          left: particle.x + '%',
          top: particle.y + '%',
          width: particle.size + 'px',
          height: particle.size + 'px',
          animation: `float ${particle.duration}s ease-in-out infinite ${particle.delay}s`
        }"
      />
    </div>

    <header class="bg-gray-800 py-4 shadow-md relative z-10">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">支持热词预测的语音识别系统</h1>
        <div class="flex items-center gap-4">
          <span>{{ username }}</span>
          <el-button type="danger" size="small" @click="logout">退出登录</el-button>
        </div>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 relative z-10">
      <h2 class="text-2xl font-bold mb-6 text-center">欢迎使用语音识别系统</h2>
      
      <!-- 功能卡片 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <!-- 卡片1: 离线文件转写 -->
        <el-card 
          class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 cursor-pointer border border-gray-700"
          @click="$router.push('/transcribe')"
        >
          <template #header>
            <div class="flex items-center">
              <el-icon class="text-blue-400 mr-3" size="24"><Document /></el-icon>
              <span>离线文件转写</span>
            </div>
          </template>
          <div class="text-gray-400 mb-4">
            上传音频文件，系统会自动进行转写并返回文本结果。
          </div>
          <el-button type="primary" class="w-full" @click.stop="$router.push('/transcribe')">开始转写</el-button>
        </el-card>
        
        <!-- 卡片2: 实时语音转写 -->
        <el-card 
          class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 cursor-pointer border border-gray-700"
          @click="$router.push('/realtime')"
        >
          <template #header>
            <div class="flex items-center">
              <el-icon 
                class="mr-3 transition-colors" 
                :class="isRecording ? 'text-red-400' : 'text-green-400'" 
                size="24"
              >
                <Microphone />
              </el-icon>
              <span>实时语音转写</span>
            </div>
          </template>
          <div class="text-gray-400 mb-4">
            使用麦克风进行实时录音，系统会即时转写您的语音内容。
          </div>
          <el-button 
            type="success" 
            class="w-full" 
            @click.stop="$router.push('/realtime')"
          >
            开始实时转写
          </el-button>
        </el-card>
        
        <!-- 卡片3: 热词管理 -->
        <el-card 
          class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105 cursor-pointer border border-gray-700"
        >
          <template #header>
            <div class="flex items-center">
              <el-icon class="text-orange-400 mr-3" size="24"><Setting /></el-icon>
              <span>热词管理</span>
            </div>
          </template>
          <div class="text-gray-400 mb-4">
            添加和管理您的专业领域词汇，提高语音识别准确率。
          </div>
          <a href="http://127.0.0.1:8765" target="_blank" rel="noopener noreferrer" style="text-decoration: none;">
            <el-button type="warning" class="w-full">管理热词</el-button>
          </a>
        </el-card>
      </div>

      <!-- 酷炫的音频可视化区域 -->
      <el-card class="bg-gray-800 border-none shadow-lg border border-gray-700">
        <template #header>
          <h3 class="text-xl font-bold text-center">音频可视化</h3>
        </template>
        
        <div class="p-8">
          <!-- 中央音频波形 -->
          <div class="flex justify-center items-center mb-8">
            <div class="relative">
              <div 
                class="w-24 h-24 rounded-full border-4 border-blue-400 flex items-center justify-center transition-all duration-300"
                :class="isRecording ? 'bg-blue-400 bg-opacity-20 animate-pulse' : 'bg-gray-700'"
              >
                <el-icon 
                  class="transition-colors" 
                  :class="isRecording ? 'text-white' : 'text-blue-400'" 
                  size="32"
                >
                  <VideoPlay />
                </el-icon>
              </div>
              
              <!-- 环形波纹效果 -->
              <div v-if="isRecording" class="absolute inset-0 rounded-full border-2 border-blue-400 animate-ping opacity-75"></div>
              <div v-if="isRecording" class="absolute -inset-2 rounded-full border-2 border-blue-400 animate-ping opacity-50" style="animation-delay: 0.5s"></div>
              <div v-if="isRecording" class="absolute -inset-4 rounded-full border-2 border-blue-400 animate-ping opacity-25" style="animation-delay: 1s"></div>
            </div>
          </div>

          <!-- 音频波形条 -->
          <div class="flex justify-center items-end space-x-2 mb-8">
            <div
              v-for="(height, i) in waveHeights"
              :key="i"
              class="bg-gradient-to-t from-blue-500 to-purple-500 rounded-t transition-all duration-300"
              :class="waveAnimation ? 'animate-pulse' : ''"
              :style="{
                width: '8px',
                height: height + 'px',
                animationDelay: (i * 0.1) + 's'
              }"
            />
          </div>

          <!-- 频谱分析器 -->
          <div class="grid grid-cols-4 md:grid-cols-8 gap-2 mb-8">
            <div 
              v-for="(freq, i) in frequencies" 
              :key="i" 
              class="bg-gray-700 rounded-lg p-4 text-center"
            >
              <el-icon class="text-green-400 mx-auto mb-2" size="20"><TrendCharts /></el-icon>
              <div class="text-sm text-gray-400">
                {{ freq.label }}
              </div>
              <div class="mt-2 bg-gray-600 rounded-full h-2">
                <div 
                  class="bg-green-400 h-2 rounded-full transition-all duration-500"
                  :style="{width: freq.value + '%'}"
                />
              </div>
            </div>
          </div>

          <!-- 实时状态指示器 -->
          <div class="flex justify-center space-x-8">
            <div class="text-center">
              <div class="text-2xl font-bold text-blue-400">{{ stats.accuracy }}</div>
              <div class="text-sm text-gray-400"></div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-green-400">{{ stats.responseTime }}s</div>
              <div class="text-sm text-gray-400">平均响应时间</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-purple-400">{{ stats.characters }}</div>
              <div class="text-sm text-gray-400">处理的字符</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 动态统计信息 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
        <el-card class="bg-gray-800 border-none border border-gray-700">
          <div class="flex items-center justify-between p-4">
            <div>
              <div class="text-2xl font-bold text-blue-400">{{ dailyStats.transcriptions }}</div>
              <div class="text-sm text-gray-400">今日转写次数</div>
            </div>
            <el-icon class="text-blue-400" size="32"><Headset /></el-icon>
          </div>
        </el-card>
        
        <el-card class="bg-gray-800 border-none border border-gray-700">
          <div class="flex items-center justify-between p-4">
            <div>
              <div class="text-2xl font-bold text-green-400">{{ dailyStats.totalTime }}h</div>
              <div class="text-sm text-gray-400">总处理时长</div>
            </div>
            <el-icon class="text-green-400" size="32"><Timer /></el-icon>
          </div>
        </el-card>
        
        <el-card class="bg-gray-800 border-none border border-gray-700">
          <div class="flex items-center justify-between p-4">
            <div>
              <div class="text-2xl font-bold text-purple-400">{{ dailyStats.currentTime }}</div>
              <div class="text-sm text-gray-400">当前时间</div>
            </div>
            <el-icon class="text-purple-400" size="32"><Timer /></el-icon>
          </div>
        </el-card>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { authAPI } from '../services/api';
import { ElMessage } from 'element-plus';
import { 
  Document, 
  Microphone, 
  Setting, 
  VideoPlay, 
  TrendCharts, 
  Headset, 
  Timer 
} from '@element-plus/icons-vue';

const router = useRouter();
const username = ref('用户');
const isRecording = ref(false);
const waveAnimation = ref(false);
const particles = ref([]);
const waveHeights = ref([]);
const frequencies = ref([
  { label: '低频', value: 0 },
  { label: '中低', value: 0 },
  { label: '中频', value: 0 },
  { label: '中高', value: 0 },
  { label: '高频', value: 0 },
  { label: '超高', value: 0 },
  { label: '极高', value: 0 },
  { label: '峰值', value: 0 }
]);

const stats = ref({
  responseTime: 1.2,
  characters: 923
});

const dailyStats = ref({
  transcriptions: 56,
  totalTime: 15.6,
  hotwords: 127
});

// 🔥 新增：更新实时时间
function updateCurrentTime() {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  dailyStats.value.currentTime = `${hours}:${minutes}:${seconds}`;
}

let animationIntervals = [];

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

  // 初始化时间显示
  updateCurrentTime();
  
  // 每秒更新时间
  const timeInterval = setInterval(updateCurrentTime, 1000);
  animationIntervals.push(timeInterval);

  initializeAnimations();
});

onUnmounted(() => {
  // 清理所有定时器
  animationIntervals.forEach(interval => clearInterval(interval));
});

function initializeAnimations() {
  // 生成初始粒子
  generateParticles();
  
  // 生成初始波形高度
  generateWaveHeights();
  
  // 启动各种动画
  startParticleAnimation();
  startWaveAnimation();
  startFrequencyAnimation();
}

function generateParticles() {
  const newParticles = [];
  for (let i = 0; i < 20; i++) {
    newParticles.push({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 4 + 2,
      duration: Math.random() * 3 + 2,
      delay: Math.random() * 2
    });
  }
  particles.value = newParticles;
}

function generateWaveHeights() {
  const heights = [];
  for (let i = 0; i < 20; i++) {
    heights.push(Math.random() * 60 + 20);
  }
  waveHeights.value = heights;
}

function startParticleAnimation() {
  const interval = setInterval(() => {
    generateParticles();
  }, 5000);
  animationIntervals.push(interval);
}

function startWaveAnimation() {
  const interval = setInterval(() => {
    waveAnimation.value = !waveAnimation.value;
    generateWaveHeights();
  }, 1000);
  animationIntervals.push(interval);
}

function startFrequencyAnimation() {
  const interval = setInterval(() => {
    frequencies.value.forEach(freq => {
      freq.value = Math.random() * 100;
    });
  }, 800);
  animationIntervals.push(interval);
}

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
  color: #e5e7eb;
}

:deep(.el-card__body) {
  padding: 16px;
}

/* 自定义动画 */
@keyframes float {
  0%, 100% { 
    transform: translateY(0px); 
  }
  50% { 
    transform: translateY(-20px); 
  }
}

/* 悬停效果 */
.cursor-pointer:hover {
  transform: translateY(-2px);
}

/* 波纹动画 */
@keyframes ping {
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}

.animate-ping {
  animation: ping 1s cubic-bezier(0, 0, 0.2, 1) infinite;
}

/* 脉冲动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: .5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
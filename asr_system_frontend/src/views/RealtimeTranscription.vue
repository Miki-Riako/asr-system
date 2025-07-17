<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">录音转写</h1>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 max-w-6xl">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 左侧：控制面板 (UI保持原样) -->
        <div class="lg:col-span-1">
          <el-card class="bg-gray-800 border-none shadow-lg">
            <template #header>
              <div class="flex items-center">
                <el-icon class="mr-2"><microphone /></el-icon>
                <span>录音控制</span>
              </div>
            </template>
            
            <div class="space-y-4 p-2">
              <!-- 录音控制按钮 -->
              <div class="flex flex-col gap-3">
                <el-button 
                  :type="isRecording ? 'danger' : 'primary'"
                  :disabled="isLoading"
                  :loading="isLoading"
                  @click="toggleRecording"
                  size="large"
                  class="w-full"
                >
                  <el-icon class="mr-2">
                    <component :is="isRecording ? 'VideoPause' : 'VideoPlay'" />
                  </el-icon>
                  {{ buttonText }}
                </el-button>
              </div>

              <!-- 状态和时长显示 -->
              <div class="bg-gray-700 p-3 rounded text-center">
                <div class="text-sm text-gray-400">当前状态</div>
                <div class="text-lg font-semibold mt-1" :class="statusClass">
                  {{ statusText }}
                </div>
                <div v-if="isRecording" class="text-sm text-gray-400 mt-2">
                  录音时长: <span class="font-mono">{{ formatTime(recordingDuration) }}</span>
                </div>
              </div>

            </div>
          </el-card>
        </div>
        
        <!-- 右侧：转写结果 (UI保持原样) -->
        <div class="lg:col-span-2">
          <el-card class="bg-gray-800 border-none shadow-lg">
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <el-icon class="mr-2"><document /></el-icon>
                  <span>转写结果</span>
                </div>
                <div class="flex gap-2">
                  <el-button size="small" @click="clearResult" :disabled="isLoading">清空结果</el-button>
                  <el-button size="small" @click="exportResult" :disabled="!transcriptionResult || isLoading">导出文本</el-button>
                </div>
              </div>
            </template>
            
            <div 
              class="bg-gray-700 p-4 rounded min-h-[400px] max-h-[500px] overflow-y-auto"
            >
              <!-- 加载状态 -->
              <div v-if="isLoading" class="flex flex-col items-center justify-center h-full text-center text-gray-400">
                <el-icon class="is-loading text-4xl mb-4 text-blue-400"><loading /></el-icon>
                <p>正在努力转写中，请稍候...</p>
              </div>
              <!-- 空状态 -->
              <div v-else-if="!transcriptionResult" class="flex flex-col items-center justify-center h-full text-center text-gray-400">
                <el-icon class="text-5xl mb-2"><files /></el-icon>
                <p>点击“开始录音”，结束后结果将显示在这里</p>
              </div>
              <!-- 显示结果 -->
              <div v-else class="text-white text-lg leading-relaxed whitespace-pre-wrap">
                {{ transcriptionResult }}
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue';
import { ElMessage } from 'element-plus';
import { Microphone, Document, VideoPlay, VideoPause, Loading, Files } from '@element-plus/icons-vue';

// --- 状态管理 ---
const isRecording = ref(false);
const isLoading = ref(false);
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const transcriptionResult = ref('');
const recordingDuration = ref(0);
let recordingTimer = null;

// --- UI 计算属性 ---
const buttonText = computed(() => {
  if (isLoading.value) return '正在转写...';
  return isRecording.value ? '停止录音' : '开始录音';
});

const statusText = computed(() => {
  if (isLoading.value) return '正在处理';
  if (isRecording.value) return '正在录音';
  return '空闲';
});

const statusClass = computed(() => {
  if (isLoading.value) return 'text-blue-400';
  if (isRecording.value) return 'text-red-400';
  return 'text-green-400';
});

// --- 生命周期钩子 ---
onUnmounted(() => {
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop();
  }
  if (recordingTimer) {
    clearInterval(recordingTimer);
  }
});

// --- 核心功能函数 (与上一版相同，但现在会驱动这个UI) ---

const toggleRecording = () => {
  if (!isRecording.value) {
    startRecording();
  } else {
    stopRecording();
  }
};

const startRecording = async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    ElMessage.error('您的浏览器不支持录音功能。');
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    audioChunks.value = [];
    transcriptionResult.value = '';
    
    mediaRecorder.value = new MediaRecorder(stream, { mimeType: 'audio/webm' });

    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data);
      }
    };

    mediaRecorder.value.onstop = () => {
      transcribeAudio();
      stream.getTracks().forEach(track => track.stop());
    };

    mediaRecorder.value.start();
    isRecording.value = true;

    recordingDuration.value = 0;
    recordingTimer = setInterval(() => {
      recordingDuration.value++;
    }, 1000);

  } catch (error) {
    console.error('无法开始录音:', error);
    ElMessage.error('无法启动录音功能，请检查麦克风权限。');
  }
};

const stopRecording = () => {
  if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    mediaRecorder.value.stop();
    isRecording.value = false;
    clearInterval(recordingTimer);
  }
};

const transcribeAudio = async () => {
  if (audioChunks.value.length === 0) {
    ElMessage.warning('录音内容过短，未进行转写。');
    return;
  }

  isLoading.value = true;
  transcriptionResult.value = '';

  const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' });
  const formData = new FormData();
  formData.append('file', audioBlob, `recording-${Date.now()}.webm`);

  try {
    const response = await fetch('/api/asr/transcribe/file', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '转写请求失败');
    }

    const data = await response.json();
    transcriptionResult.value = data.result || '未能识别出任何内容。';
    ElMessage.success('转写完成！');

  } catch (error) {
    console.error('转写失败:', error);
    ElMessage.error('转写失败: ' + error.message);
    transcriptionResult.value = `错误: ${error.message}`;
  } finally {
    isLoading.value = false;
  }
};

// --- 辅助UI函数 ---

const formatTime = (seconds) => {
  const m = String(Math.floor(seconds / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  return `${m}:${s}`;
};

const clearResult = () => {
  transcriptionResult.value = '';
};

const exportResult = () => {
  if (!transcriptionResult.value) {
    ElMessage.warning('没有可导出的结果');
    return;
  }
  const blob = new Blob([transcriptionResult.value], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `录音转写结果.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
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
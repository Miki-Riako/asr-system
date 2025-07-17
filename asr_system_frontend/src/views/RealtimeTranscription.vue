<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">分段录音转写</h1>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 max-w-5xl">
      <!-- 控制与状态显示区域 -->
      <el-card class="bg-gray-800 border-none shadow-lg mb-6">
        <template #header>
          <div class="flex items-center">
            <el-icon class="mr-2"><microphone /></el-icon>
            <span>录音控制台</span>
          </div>
        </template>
        <div class="flex flex-col md:flex-row items-center justify-center gap-8 p-6">
          <!-- 录音按钮 -->
          <el-button 
            :type="isRecording ? 'danger' : 'primary'"
            @click="toggleRecording"
            :disabled="isLoading"
            :loading="isLoading"
            size="large"
            class="w-48 h-16 text-lg"
          >
            <el-icon class="mr-2 text-xl">
              <component :is="isRecording ? 'VideoPause' : 'VideoPlay'" />
            </el-icon>
            {{ buttonText }}
          </el-button>
          
          <!-- 状态显示 -->
          <div class="text-center md:text-left">
            <div class="text-gray-400 text-sm">当前状态</div>
            <div class="text-lg font-semibold" :class="statusClass">{{ statusText }}</div>
            <div v-if="isRecording" class="text-lg font-mono mt-1">
              录音时长: {{ formatTime(recordingDuration) }}
            </div>
          </div>
        </div>
      </el-card>

      <!-- 转写结果历史记录 -->
      <el-card class="bg-gray-800 border-none shadow-lg">
        <template #header>
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <el-icon class="mr-2"><document /></el-icon>
              <span>转写历史</span>
            </div>
            <div class="flex gap-2">
              <el-button size="small" @click="exportHistory" :disabled="transcriptionHistory.length === 0">导出历史</el-button>
              <el-button size="small" type="danger" plain @click="clearHistory" :disabled="transcriptionHistory.length === 0">清空历史</el-button>
            </div>
          </div>
        </template>

        <!-- 正在转写中的提示 -->
        <div v-if="isLoading" class="p-4 mb-4 bg-blue-900/50 rounded-lg flex items-center gap-4">
          <el-icon class="is-loading text-2xl text-blue-400"><loading /></el-icon>
          <div>
            <div class="font-semibold">正在努力转写上一段录音...</div>
            <div class="text-sm text-gray-400">请稍候，转写完成后结果会出现在下方。</div>
          </div>
        </div>
        
        <!-- 历史记录列表 -->
        <div v-if="transcriptionHistory.length > 0" class="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
          <div 
            v-for="(item, index) in transcriptionHistory" 
            :key="index"
            class="bg-gray-700 p-4 rounded-lg"
          >
            <div class="text-xs text-gray-400 mb-2">
              #{{ transcriptionHistory.length - index }} - {{ item.timestamp }}
            </div>
            <p class="text-white leading-relaxed whitespace-pre-wrap">{{ item.text }}</p>
          </div>
        </div>
        
        <!-- 空状态提示 -->
        <div v-else-if="!isLoading" class="text-center py-12 text-gray-500">
          <el-icon class="text-5xl mb-2"><files /></el-icon>
          <p>暂无转写记录</p>
          <p class="text-sm mt-1">点击“开始录音”来创建第一条记录</p>
        </div>
      </el-card>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Microphone, Document, VideoPlay, VideoPause, Loading, Files } from '@element-plus/icons-vue';

// --- 响应式状态定义 ---
const isRecording = ref(false);       // 是否正在录音
const isLoading = ref(false);         // 是否正在向后端请求转写
const mediaRecorder = ref(null);      // MediaRecorder 实例
const audioChunks = ref([]);          // 存储录音数据块
const transcriptionHistory = ref([]); // 存储所有转写结果
const recordingDuration = ref(0);     // 当前录音的时长
let recordingTimer = null;            // 计时器实例

// --- UI 计算属性 ---
const buttonText = computed(() => {
  if (isLoading.value) return '处理中...';
  return isRecording.value ? '停止录音' : '开始录音';
});

const statusText = computed(() => {
  if (isLoading.value) return '正在转写';
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
  // 组件销毁时确保停止录音和计时器
  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop();
  }
  if (recordingTimer) {
    clearInterval(recordingTimer);
  }
});

// --- 核心功能函数 ---

// 1. "开始/停止录音"按钮的统一入口
const toggleRecording = () => {
  if (!isRecording.value) {
    startRecording();
  } else {
    stopRecording();
  }
};

// 2. 开始录音
const startRecording = async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    ElMessage.error('您的浏览器不支持录音功能。');
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    audioChunks.value = []; // 清空上一次的音频数据
    mediaRecorder.value = new MediaRecorder(stream, { mimeType: 'audio/webm' });

    // 监听数据块，并存入数组
    mediaRecorder.value.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunks.value.push(event.data);
      }
    };

    // 监听录音停止事件，这是触发转写的关键
    mediaRecorder.value.onstop = () => {
      transcribeAudio(); // 调用转写函数
      stream.getTracks().forEach(track => track.stop()); // 释放麦克风
    };

    mediaRecorder.value.start();
    isRecording.value = true;

    // 启动录音计时器
    recordingDuration.value = 0;
    recordingTimer = setInterval(() => {
      recordingDuration.value++;
    }, 1000);

  } catch (error) {
    console.error('无法开始录音:', error);
    ElMessage.error('无法启动录音功能，请检查麦克风权限。');
  }
};

// 3. 停止录音
const stopRecording = () => {
  if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    mediaRecorder.value.stop(); // 该操作会自动触发 onstop 事件
    isRecording.value = false;
    clearInterval(recordingTimer);
  }
};

// 4. 将录制的音频发送到后端进行转写
const transcribeAudio = async () => {
  if (audioChunks.value.length === 0) {
    ElMessage.warning('录音内容过短，未进行转写。');
    return;
  }

  isLoading.value = true;

  // 将所有音频数据块合并成一个 Blob 对象
  const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' });

  // 使用 FormData 模拟文件上传，与您的离线转写接口完全兼容
  const formData = new FormData();
  formData.append('file', audioBlob, `recording-${Date.now()}.webm`);

  try {
    // 调用您已有的、能正常工作的离线文件转写API
    const response = await fetch('/api/asr/transcribe/file', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '转写请求失败');
    }

    const data = await response.json();
    const resultText = data.result || '未能识别出任何内容。';
    
    // 将新结果添加到历史记录的开头
    transcriptionHistory.value.unshift({
      text: resultText,
      timestamp: new Date().toLocaleString('zh-CN'),
    });
    
    ElMessage.success('转写完成！');

  } catch (error) {
    console.error('转写失败:', error);
    ElMessage.error('转写失败: ' + error.message);
  } finally {
    isLoading.value = false; // 无论成功失败，都结束加载状态
  }
};

// --- 辅助功能 ---

// 格式化时间显示
const formatTime = (seconds) => {
  const m = String(Math.floor(seconds / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  return `${m}:${s}`;
};

// 清空历史记录
const clearHistory = () => {
  ElMessageBox.confirm('确定要清空所有转写历史记录吗？', '确认操作', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    transcriptionHistory.value = [];
    ElMessage.success('历史记录已清空');
  }).catch(() => {});
};

// 导出历史记录为文本文件
const exportHistory = () => {
  const content = transcriptionHistory.value
    .slice() // 创建副本以防修改原数组
    .reverse() // 让导出的文件按时间顺序排列
    .map((item, index) => `--- 第 ${index + 1} 条记录 (${item.timestamp}) ---\n${item.text}\n`)
    .join('\n');
    
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `录音转写历史.txt`;
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
  padding: 12px 20px;
  border-bottom: 1px solid #4b5563;
}
:deep(.el-table) {
  background-color: transparent;
}
</style>
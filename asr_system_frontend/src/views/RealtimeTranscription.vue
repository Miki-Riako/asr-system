<template>
  <div class="h-screen bg-gray-900 text-gray-200 flex flex-col">
    <header class="bg-gray-800 py-4 shadow-md flex-shrink-0">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">语音AI助手</h1>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 flex-grow flex min-h-0">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 w-full h-full">
        
        <!-- ======================================================= -->
        <!-- 左侧控制面板 -->
        <!-- ======================================================= -->
        <div class="lg:col-span-1">
          <el-card class="bg-gray-800 border-none shadow-lg">
            <template #header>
              <div class="flex items-center header-text">
                <el-icon class="mr-2"><microphone /></el-icon>
                <span>录音控制</span>
              </div>
            </template>
            <div class="space-y-6 p-4 flex flex-col items-center">
              <el-button 
                :type="isRecording ? 'danger' : 'primary'"
                :disabled="isLoading"
                @click="toggleRecording"
                size="large"
                class="w-full h-12"
              >
                <el-icon class="mr-2"><component :is="isRecording ? 'VideoPause' : 'Microphone'" /></el-icon>
                {{ isRecording ? '停止录音' : '开始录音' }}
              </el-button>
              
              <div class="bg-gray-700 p-4 rounded text-center w-full">
                <div class="text-sm text-gray-400">当前状态</div>
                <div class="text-lg font-semibold mt-1" :class="statusClass">
                  {{ statusText }}
                </div>
                <div v-if="isRecording" class="text-sm text-gray-400 mt-2">
                  录音时长: <span class="font-mono">{{ formatTime(recordingDuration) }}</span>
                </div>
              </div>

              <div v-if="isRecording" class="w-full flex flex-col items-center gap-2 pt-4">
                <div class="text-sm text-gray-400">实时音量</div>
                <el-progress type="dashboard" :percentage="audioLevel" :color="progressColors" />
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- ======================================================= -->
        <!-- 右侧交互区 (采用能实现滚动的标准布局) -->
        <!-- ======================================================= -->
        <div class="lg:col-span-2 flex flex-col h-full">
          <el-card class="bg-gray-800 border-none shadow-lg flex flex-col flex-grow">
            <template #header>
              <div class="flex items-center justify-between header-text">
                <span>AI 对话</span>
                <el-button size="small" type="danger" plain @click="clearChat" :disabled="chatHistory.length === 0">清空对话</el-button>
              </div>
            </template>
            
            <!-- 【核心】可滚动的聊天记录区域 -->
            <div ref="chatContainer" class="flex-grow p-4 space-y-4 overflow-y-auto min-h-0">
                <div v-if="chatHistory.length === 0 && !isLoading" class="flex items-center justify-center h-full text-center text-gray-500">
                  <div>
                    <el-icon class="text-5xl mb-4"><MagicStick /></el-icon>
                    <p>请通过录音或手动输入开始对话</p>
                  </div>
                </div>
                <div v-for="(item, index) in chatHistory" :key="index" :class="item.role === 'user' ? 'user-message' : 'assistant-message'">
                    <div class="message-bubble" :class="item.role">
                        <pre class="whitespace-pre-wrap font-sans">{{ item.content }}</pre>
                        <!-- 时间戳显示在右下角 -->
                        <span class="message-time">{{ item.time }}</span>
                    </div>
                </div>
            </div>

            <!-- 【核心】固定在底部的输入框和按钮 -->
            <div class="input-area p-4 border-t border-gray-700 mt-auto flex-shrink-0">
                <div class="flex items-center gap-2">
                    <el-input
                        v-model="promptText"
                        placeholder="识别后的文字将显示在这里，可编辑"
                        size="large"
                        @keyup.enter="sendPrompt"
                        :disabled="isLoading"
                    />
                    <el-button @click="sendPrompt" type="primary" size="large" :disabled="!promptText || isLoading" :loading="isLoading">
                        <el-icon><Promotion /></el-icon>
                        <span class="ml-2">运行</span>
                    </el-button>
                </div>
            </div>
          </el-card>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, nextTick } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Microphone, VideoPause, Promotion, MagicStick } from '@element-plus/icons-vue';
import axios from 'axios';

// --- 状态管理 (无变化) ---
const isRecording = ref(false);
const isLoading = ref(false);
const mediaRecorder = ref(null);
const audioChunks = ref([]);
const recordingDuration = ref(0);
let recordingTimer = null;
const audioLevel = ref(0);
let animationFrameId = null;

const promptText = ref('');
const chatHistory = ref([]);
const chatContainer = ref(null);

const progressColors = [
  { color: '#67c23a', percentage: 60 },
  { color: '#e6a23c', percentage: 80 },
  { color: '#f56c6c', percentage: 100 },
];

// --- UI 计算属性 (无变化) ---
const statusText = computed(() => {
  if (isRecording.value) return '正在录音...';
  if (isLoading.value) return 'AI思考中...';
  return '空闲';
});
const statusClass = computed(() => {
  if (isRecording.value) return 'text-red-400';
  if (isLoading.value) return 'text-blue-400';
  return 'text-green-400';
});

// --- 生命周期 (无变化) ---
onUnmounted(() => {
  stopAudioProcessing();
});

// --- 核心函数 ---

const toggleRecording = () => {
  if (isLoading.value) return;
  isRecording.value ? stopRecording() : startRecording();
};

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks.value = [];
    mediaRecorder.value = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    mediaRecorder.value.ondataavailable = event => audioChunks.value.push(event.data);
    mediaRecorder.value.onstop = () => {
      transcribeAudio();
      stopAudioProcessing(stream);
    };
    mediaRecorder.value.start();
    isRecording.value = true;
    startAudioProcessing(stream);
    recordingTimer = setInterval(() => recordingDuration.value++, 1000);
  } catch (error) {
    ElMessage.error('无法启动录音，请检查麦克风权限。');
  }
};

const stopRecording = () => {
  if (mediaRecorder.value) {
    mediaRecorder.value.stop();
  }
};

// 【功能1：音频转写 - 已是正确版本，无需修改】
const transcribeAudio = async () => {
  if (audioChunks.value.length === 0) return;
  isLoading.value = true;
  ElMessage.info('正在转写音频...');
  const audioBlob = new Blob(audioChunks.value, { type: 'audio/webm' });
  const formData = new FormData();
  formData.append('file', audioBlob, `recording.webm`);

  try {
    const response = await axios.post('/api/asr/transcribe/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    promptText.value = response.data.result || '';
    if (response.data.result) ElMessage.success('语音识别成功！');
    else ElMessage.warning('未能识别出任何内容。');
  } catch (error) {
    const detail = error.response?.data?.detail || '音频转写服务失败';
    ElMessage.error(detail);
  } finally {
    isLoading.value = false;
  }
};

// =======================================================
// 【功能2：发送Prompt给AI - 替换为真实API调用】
// =======================================================
const sendPrompt = async () => {
    if (!promptText.value.trim() || isLoading.value) return;

    isLoading.value = true;
    const currentPrompt = promptText.value;
    // 增加时间字段
    chatHistory.value.push({ role: 'user', content: currentPrompt, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) });
    promptText.value = '';

    await nextTick();
    scrollToBottom();

    const assistantMessageIndex = chatHistory.value.length;
    // 增加时间字段
    chatHistory.value.push({ role: 'assistant', content: '', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) });

    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ 
                prompt: currentPrompt,
                temperature: 0.7,
                max_tokens: 4000
            }),
        });

        if (!response.ok) {
            throw new Error(`DeepSeek服务错误: ${response.status} ${response.statusText}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (data.content) {
                            chatHistory.value[assistantMessageIndex].content += data.content;
                        } else if (data.error) {
                            chatHistory.value[assistantMessageIndex].content = `DeepSeek错误: ${data.error}`;
                            break;
                        } else if (data.done) {
                            // 添加模型信息到消息
                            if (data.model) {
                                console.log(`回复由 ${data.model} 生成`);
                            }
                            break;
                        }
                    } catch (e) {
                        // 忽略JSON解析错误
                    }
                }
            }
            
            scrollToBottom();
        }

    } catch (error) {
        chatHistory.value[assistantMessageIndex].content = `抱歉，与DeepSeek模型通信时出错: ${error.message}`;
        ElMessage.error(error.message);
    } finally {
        isLoading.value = false;
    }
};

// --- 音量可视化函数 (无变化) ---
const startAudioProcessing = (stream) => {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const analyserNode = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyserNode);
    analyserNode.smoothingTimeConstant = 0.8;
    analyserNode.fftSize = 256;
    
    const update = () => {
        const dataArray = new Uint8Array(analyserNode.frequencyBinCount);
        analyserNode.getByteFrequencyData(dataArray);
        const rms = Math.sqrt(dataArray.reduce((sum, val) => sum + val * val, 0) / dataArray.length);
        audioLevel.value = Math.min(100, Math.round((rms / 128) * 100));
        animationFrameId = requestAnimationFrame(update);
    };
    update();
};
const stopAudioProcessing = (stream = null) => {
    if (animationFrameId) cancelAnimationFrame(animationFrameId);
    if (stream) stream.getTracks().forEach(track => track.stop());
    isRecording.value = false;
    clearInterval(recordingTimer);
    recordingDuration.value = 0;
    audioLevel.value = 0;
};

// --- 辅助函数 (无变化) ---
const formatTime = (seconds) => {
  const m = String(Math.floor(seconds / 60)).padStart(2, '0');
  const s = String(seconds % 60).padStart(2, '0');
  return `${m}:${s}`;
};
const clearChat = () => {
    ElMessageBox.confirm('确定要清空所有对话记录吗？', '确认', { type: 'warning' })
        .then(() => {
            chatHistory.value = [];
            promptText.value = '';
            ElMessage.success('对话已清空');
        }).catch(() => {});
};
const scrollToBottom = () => {
    if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
};
</script>

<style scoped>
/* 卡片头部的文字颜色 */
:deep(.el-card__header) {
  color: #e5e7eb; 
  flex-shrink: 0; /* 确保 header 不会被压缩 */
}

/* 【关键】让 el-card 的主体部分成为 flex 容器，以便内部分区能占满空间 */
:deep(.el-card__body) {
  padding: 0;
  display: flex;
  flex-direction: column;
  flex-grow: 1; /* 让 body 填满 card 的剩余空间 */
  min-height: 0; /* 这是 flex 布局中的一个关键技巧，防止子元素溢出 */
}

/* 音量条百分比文字颜色 */
:deep(.el-progress__text) {
    color: #e5e7eb !important;
}

.header-text {
    color: #e5e7eb;
}

/* 聊天气泡样式 */
.user-message, .assistant-message {
  display: flex;
  margin-bottom: 1rem;
}
.user-message {
  justify-content: flex-end;
}
.assistant-message {
  justify-content: flex-start;
}
.message-bubble {
  max-width: 85%;
  padding: 0.75rem 1rem;
  border-radius: 1rem;
  line-height: 1.6;
  font-size: 1rem;
  position: relative; /* 新增 */
}
.message-bubble.user {
  background-color: #3b82f6;
  color: white;
  border-bottom-right-radius: 0.25rem;
}
.message-bubble.assistant {
  background-color: #4b5563;
  color: #e5e7eb;
  border-bottom-left-radius: 0.25rem;
}
.message-time {
  position: absolute;
  right: 12px;
  bottom: 6px;
  font-size: 0.75em;
  color: #bdbdbd;
  opacity: 0.7;
}
</style>
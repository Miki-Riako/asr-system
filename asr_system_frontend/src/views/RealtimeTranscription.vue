<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">实时语音转写</h1>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 max-w-6xl">
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 左侧：控制面板 -->
        <div class="lg:col-span-1">
          <el-card class="bg-gray-800 border-none shadow-lg">
            <template #header>
              <div class="flex items-center">
                <el-icon class="mr-2"><microphone /></el-icon>
                <span>录音控制</span>
              </div>
            </template>
            
            <div class="space-y-4">
              <!-- 连接状态 -->
              <div class="flex items-center justify-between p-3 bg-gray-700 rounded">
                <span>连接状态:</span>
                <el-tag :type="getStatusType(connectionStatus)" size="small">
                  {{ getStatusText(connectionStatus) }}
                </el-tag>
              </div>
              
              <!-- 录音控制按钮 -->
              <div class="flex flex-col gap-3">
                <el-button 
                  :type="isRecording ? 'danger' : 'primary'"
                  :disabled="connectionStatus !== 'connected'"
                  @click="toggleRecording"
                  size="large"
                  class="w-full"
                >
                  <el-icon class="mr-2">
                    <component :is="isRecording ? 'video-pause' : 'video-play'" />
                  </el-icon>
                  {{ isRecording ? '停止录音' : '开始录音' }}
                </el-button>
                
                <el-button 
                  v-if="connectionStatus === 'disconnected'"
                  type="success"
                  @click="connectWebSocket"
                  :loading="connecting"
                  size="large"
                  class="w-full"
                >
                  连接服务器
                </el-button>
                
                <el-button 
                  v-if="connectionStatus === 'connected'"
                  type="warning"
                  @click="disconnectWebSocket"
                  size="large"
                  class="w-full"
                >
                  断开连接
                </el-button>
              </div>
              
              <!-- 音频设置 -->
              <div class="space-y-3">
                <div class="flex items-center justify-between">
                  <span>启用热词增强:</span>
                  <el-switch v-model="useHotwords" />
                </div>
                
                <div class="flex items-center justify-between">
                  <span>音量:</span>
                  <div class="flex items-center gap-2">
                    <el-slider 
                      v-model="audioVolume" 
                      :min="0" 
                      :max="100" 
                      :step="5"
                      style="width: 120px"
                    />
                    <span class="text-sm">{{ audioVolume }}%</span>
                  </div>
                </div>
              </div>
              
              <!-- 音频可视化 -->
              <div class="bg-gray-700 p-3 rounded">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm">音频输入</span>
                  <span class="text-sm">{{ Math.round(audioLevel) }}%</span>
                </div>
                <div class="w-full bg-gray-600 rounded-full h-2">
                  <div 
                    class="bg-blue-500 h-2 rounded-full transition-all duration-100"
                    :style="{ width: audioLevel + '%' }"
                  ></div>
                </div>
              </div>
              
              <!-- 统计信息 -->
              <div class="text-sm text-gray-400 space-y-1">
                <div>录音时长: {{ formatTime(recordingDuration) }}</div>
                <div>转写片段: {{ transcriptionResults.length }}</div>
                <div>热词检测: {{ totalHotwordsDetected }}</div>
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 右侧：转写结果 -->
        <div class="lg:col-span-2">
          <el-card class="bg-gray-800 border-none shadow-lg">
            <template #header>
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <el-icon class="mr-2"><document /></el-icon>
                  <span>实时转写结果</span>
                </div>
                <div class="flex gap-2">
                  <el-button size="small" @click="clearResults">清空结果</el-button>
                  <el-button size="small" @click="exportResults">导出文本</el-button>
                </div>
              </div>
            </template>
            
            <div class="space-y-4">
              <!-- 实时转写区域 -->
              <div 
                ref="transcriptionContainer"
                class="bg-gray-700 p-4 rounded min-h-[400px] max-h-[500px] overflow-y-auto"
              >
                <div v-if="transcriptionResults.length === 0" class="text-center text-gray-400 py-8">
                  <el-icon class="text-4xl mb-2"><microphone /></el-icon>
                  <p>点击开始录音，实时转写结果将显示在这里</p>
                </div>
                
                <div v-else class="space-y-3">
                  <div 
                    v-for="(result, index) in transcriptionResults"
                    :key="index"
                    class="border-l-4 border-blue-500 pl-4 py-2"
                  >
                    <div class="flex items-center justify-between mb-1">
                      <span class="text-xs text-gray-400">{{ formatTime(result.timestamp) }}</span>
                      <div class="flex items-center gap-2">
                        <el-tag 
                          v-if="result.confidence_boost > 1"
                          type="success"
                          size="small"
                        >
                          热词增强 {{ result.confidence_boost.toFixed(1) }}x
                        </el-tag>
                        <span class="text-xs text-gray-400">
                          置信度: {{ (result.confidence * 100).toFixed(1) }}%
                        </span>
                      </div>
                    </div>
                    
                    <p class="text-white leading-relaxed">{{ result.text }}</p>
                    
                    <!-- 检测到的热词 -->
                    <div v-if="result.hotwords_detected.length > 0" class="mt-2">
                      <div class="flex items-center gap-2 flex-wrap">
                        <span class="text-xs text-gray-400">检测到热词:</span>
                        <el-tag 
                          v-for="hotword in result.hotwords_detected"
                          :key="hotword.word"
                          type="warning"
                          size="small"
                        >
                          {{ hotword.word }} ({{ hotword.weight }})
                        </el-tag>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 连接日志 -->
              <div class="bg-gray-700 p-3 rounded">
                <div class="flex items-center justify-between mb-2">
                  <span class="text-sm font-semibold">连接日志</span>
                  <el-button size="small" @click="clearLogs">清空日志</el-button>
                </div>
                <div class="text-xs text-gray-400 max-h-24 overflow-y-auto">
                  <div v-for="(log, index) in connectionLogs" :key="index" class="mb-1">
                    [{{ formatTime(log.timestamp) }}] {{ log.message }}
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Microphone, Document, VideoPlay, VideoPause } from '@element-plus/icons-vue';

const router = useRouter();

// 状态管理
const connectionStatus = ref('disconnected'); // disconnected, connecting, connected, error
const connecting = ref(false);
const isRecording = ref(false);
const useHotwords = ref(true);
const audioVolume = ref(80);
const audioLevel = ref(0);
const recordingDuration = ref(0);
const totalHotwordsDetected = ref(0);

// 转写结果
const transcriptionResults = ref([]);
const connectionLogs = ref([]);

// WebSocket相关
let websocket = null;
let mediaRecorder = null;
let audioContext = null;
let analyser = null;
let audioStream = null;
let recordingTimer = null;
let audioLevelTimer = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 3;
const RECONNECT_DELAY = 2000;

// 引用
const transcriptionContainer = ref(null);

// 页面加载时检查浏览器支持
onMounted(() => {
  checkBrowserSupport();
});

// 页面卸载时清理资源
onUnmounted(() => {
  cleanup();
});

// 检查浏览器支持
function checkBrowserSupport() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    ElMessage.error('您的浏览器不支持音频录制功能');
    return false;
  }
  
  if (!window.WebSocket) {
    ElMessage.error('您的浏览器不支持WebSocket');
    return false;
  }
  
  return true;
}

// 连接WebSocket
async function connectWebSocket() {
  if (!checkBrowserSupport()) return;
  
  try {
    connecting.value = true;
    connectionStatus.value = 'connecting';
    
    // 获取用户媒体权限
    audioStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        sampleRate: 16000
      }
    });
    
    // 创建音频上下文
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // 创建音频分析器
    analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(audioStream);
    source.connect(analyser);
    
    // 开始音频级别监控
    startAudioLevelMonitoring();
    
    // 建立WebSocket连接
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('未找到认证令牌，请重新登录');
    }
    
    // 构建WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//localhost:8080/ws/asr/transcribe/realtime?token=${token}`;
    
    if (websocket) {
      websocket.close();
      websocket = null;
    }
    
    websocket = new WebSocket(wsUrl);
    
    websocket.onopen = () => {
      connectionStatus.value = 'connected';
      connecting.value = false;
      reconnectAttempts = 0;
      addLog('WebSocket连接已建立');
      ElMessage.success('连接成功！');
    };
    
    websocket.onmessage = (event) => {
      handleWebSocketMessage(JSON.parse(event.data));
    };
    
    websocket.onclose = (event) => {
      connectionStatus.value = 'disconnected';
      connecting.value = false;
      addLog(`WebSocket连接已关闭 (代码: ${event.code})`);
      
      if (isRecording.value) {
        stopRecording();
      }
      
      // 尝试重连
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS && event.code !== 1000) {
        reconnectAttempts++;
        addLog(`尝试重新连接 (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`);
        setTimeout(connectWebSocket, RECONNECT_DELAY);
      }
    };
    
    websocket.onerror = (error) => {
      connectionStatus.value = 'error';
      connecting.value = false;
      addLog(`WebSocket错误: ${error.message || '未知错误'}`);
      ElMessage.error('连接失败，请检查网络或重试');
    };
    
  } catch (error) {
    connecting.value = false;
    connectionStatus.value = 'error';
    addLog(`连接失败: ${error.message}`);
    ElMessage.error(`连接失败: ${error.message}`);
    cleanup();
  }
}

// 断开WebSocket连接
function disconnectWebSocket() {
  if (isRecording.value) {
    stopRecording();
  }
  
  if (websocket) {
    websocket.close();
    websocket = null;
  }
  
  cleanup();
  addLog('手动断开连接');
}

// 处理WebSocket消息
function handleWebSocketMessage(message) {
  switch (message.type) {
    case 'connection_established':
      addLog(`连接已建立，用户ID: ${message.user_id}`);
      break;
      
    case 'ready':
      addLog('实时转写服务已准备就绪');
      break;
      
    case 'transcription_result':
      handleTranscriptionResult(message.data);
      break;
      
    case 'silence_detected':
      addLog('检测到静音');
      break;
      
    case 'error':
      addLog(`错误: ${message.message}`);
      ElMessage.error(message.message);
      break;
      
    case 'pong':
      addLog('收到服务器心跳响应');
      break;
      
    default:
      addLog(`收到未知消息类型: ${message.type}`);
  }
}

// 处理转写结果
function handleTranscriptionResult(data) {
  const result = {
    text: data.text,
    confidence: data.segments?.[0]?.confidence || 0.8,
    confidence_boost: data.confidence_boost || 1,
    hotwords_detected: data.hotwords_detected || [],
    timestamp: Date.now()
  };
  
  transcriptionResults.value.push(result);
  totalHotwordsDetected.value += result.hotwords_detected.length;
  
  // 自动滚动到最新结果
  nextTick(() => {
    if (transcriptionContainer.value) {
      transcriptionContainer.value.scrollTop = transcriptionContainer.value.scrollHeight;
    }
  });
  
  addLog(`转写结果: ${data.text.substring(0, 50)}${data.text.length > 50 ? '...' : ''}`);
}

// 开始/停止录音
function toggleRecording() {
  if (isRecording.value) {
    stopRecording();
  } else {
    startRecording();
  }
}

// 开始录音
function startRecording() {
  if (!audioStream) {
    ElMessage.error('音频流未就绪');
    return;
  }
  
  try {
    // 创建MediaRecorder
    mediaRecorder = new MediaRecorder(audioStream, {
      mimeType: 'audio/webm;codecs=opus',
      bitsPerSecond: 16000
    });
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0 && websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(event.data);
      }
    };
    
    // 每1秒发送一次数据
    mediaRecorder.start(1000);
    isRecording.value = true;
    
    // 启动录音计时器
    recordingDuration.value = 0;
    recordingTimer = setInterval(() => {
      recordingDuration.value += 1;
    }, 1000);
    
    addLog('开始录音');
    
  } catch (error) {
    ElMessage.error(`录音失败: ${error.message}`);
    addLog(`录音失败: ${error.message}`);
  }
}

// 停止录音
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
    addLog('停止录音');
  }
  
  if (recordingTimer) {
    clearInterval(recordingTimer);
    recordingTimer = null;
  }
  
  isRecording.value = false;
}

// 开始音频级别监控
function startAudioLevelMonitoring() {
  if (!analyser) return;
  
  const dataArray = new Uint8Array(analyser.frequencyBinCount);
  
  const updateLevel = () => {
    if (analyser) {
      analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
      audioLevel.value = (average / 255) * 100;
    }
  };
  
  audioLevelTimer = setInterval(updateLevel, 100);
}

// 清理资源
function cleanup() {
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop());
    audioStream = null;
  }
  
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  
  if (analyser) {
    analyser = null;
  }
  
  if (audioLevelTimer) {
    clearInterval(audioLevelTimer);
    audioLevelTimer = null;
  }
  
  if (recordingTimer) {
    clearInterval(recordingTimer);
    recordingTimer = null;
  }
  
  audioLevel.value = 0;
}

// 添加连接日志
function addLog(message) {
  connectionLogs.value.push({
    message,
    timestamp: Date.now()
  });
  
  // 限制日志数量
  if (connectionLogs.value.length > 100) {
    connectionLogs.value.shift();
  }
}

// 清空转写结果
function clearResults() {
  transcriptionResults.value = [];
  totalHotwordsDetected.value = 0;
}

// 清空日志
function clearLogs() {
  connectionLogs.value = [];
}

// 导出转写结果
function exportResults() {
  if (transcriptionResults.value.length === 0) {
    ElMessage.warning('没有可导出的转写结果');
    return;
  }
  
  const text = transcriptionResults.value
    .map(result => `[${formatTime(result.timestamp)}] ${result.text}`)
    .join('\n');
  
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `实时转写结果_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

// 获取状态类型
function getStatusType(status) {
  const statusMap = {
    'disconnected': 'info',
    'connecting': 'warning',
    'connected': 'success',
    'error': 'danger'
  };
  return statusMap[status] || 'info';
}

// 获取状态文本
function getStatusText(status) {
  const statusMap = {
    'disconnected': '未连接',
    'connecting': '连接中',
    'connected': '已连接',
    'error': '连接错误'
  };
  return statusMap[status] || status;
}

// 格式化时间
function formatTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('zh-CN');
}

// 添加WAV转换函数
function audioBufferToWav(buffer) {
  const numChannels = 1;
  const sampleRate = buffer.sampleRate;
  const format = 1; // PCM
  const bitDepth = 16;
  
  const bytesPerSample = bitDepth / 8;
  const blockAlign = numChannels * bytesPerSample;
  
  const wavBuffer = buffer.getChannelData(0);
  const wavDataBytes = wavBuffer.length * bytesPerSample;
  const wavHeaderBytes = 44;
  const totalBytes = wavHeaderBytes + wavDataBytes;
  
  const wavData = new ArrayBuffer(totalBytes);
  const view = new DataView(wavData);
  
  // WAV文件头
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + wavDataBytes, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, format, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * blockAlign, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitDepth, true);
  writeString(view, 36, 'data');
  view.setUint32(40, wavDataBytes, true);
  
  // 写入音频数据
  const offset = 44;
  for (let i = 0; i < wavBuffer.length; i++) {
    const sample = Math.max(-1, Math.min(1, wavBuffer[i]));
    view.setInt16(offset + i * bytesPerSample, sample * 0x7FFF, true);
  }
  
  return wavData;
}

function writeString(view, offset, string) {
  for (let i = 0; i < string.length; i++) {
    view.setUint8(offset + i, string.charCodeAt(i));
  }
}
// 在发送音频数据前添加重采样处理
const resampleAudio = (audioData, inputRate=48000, outputRate=16000) => {
  const ratio = inputRate / outputRate;
  const length = Math.round(audioData.length / ratio);
  const result = new Float32Array(length);
  for (let i = 0; i < length; i++) {
    result[i] = audioData[Math.round(i * ratio)];
  }
  return result;
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

:deep(.el-slider__runway) {
  background-color: #4b5563;
}

:deep(.el-slider__bar) {
  background-color: #3b82f6;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #3b82f6;
}

.transcription-container {
  scrollbar-width: thin;
  scrollbar-color: #4b5563 #374151;
}

.transcription-container::-webkit-scrollbar {
  width: 6px;
}

.transcription-container::-webkit-scrollbar-track {
  background: #374151;
}

.transcription-container::-webkit-scrollbar-thumb {
  background-color: #4b5563;
  border-radius: 3px;
}
</style>
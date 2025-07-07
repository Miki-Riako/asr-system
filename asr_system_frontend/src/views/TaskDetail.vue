<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">转写任务详情</h1>
        <div class="flex gap-2">
          <el-button type="primary" @click="refreshTask">刷新状态</el-button>
          <el-button type="default" @click="$router.push('/')">返回首页</el-button>
        </div>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 max-w-6xl">
      <div v-if="loading" class="text-center py-12">
        <el-icon class="is-loading text-4xl mb-4"><loading /></el-icon>
        <p>正在加载任务详情...</p>
      </div>
      
      <div v-else-if="error" class="text-center py-12">
        <el-icon class="text-4xl mb-4 text-red-400"><warning /></el-icon>
        <p class="text-red-400 mb-4">{{ error }}</p>
        <el-button type="primary" @click="refreshTask">重试</el-button>
      </div>
      
      <div v-else class="space-y-6">
        <!-- 任务基本信息 -->
        <el-card class="bg-gray-800 border-none shadow-lg">
          <template #header>
            <div class="flex items-center justify-between">
              <span>任务信息</span>
              <el-tag :type="getStatusType(task.status)" size="large">
                {{ getStatusText(task.status) }}
              </el-tag>
            </div>
          </template>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p class="text-gray-400 text-sm">任务ID</p>
              <p class="font-mono text-sm">{{ task.id }}</p>
            </div>
            <div>
              <p class="text-gray-400 text-sm">文件名</p>
              <p>{{ task.filename }}</p>
            </div>
            <div>
              <p class="text-gray-400 text-sm">创建时间</p>
              <p>{{ formatDate(task.created_at) }}</p>
            </div>
            <div v-if="task.completed_at">
              <p class="text-gray-400 text-sm">完成时间</p>
              <p>{{ formatDate(task.completed_at) }}</p>
            </div>
            <div v-if="task.error_message" class="col-span-full">
              <p class="text-gray-400 text-sm">错误信息</p>
              <p class="text-red-400">{{ task.error_message }}</p>
            </div>
          </div>
        </el-card>
        
        <!-- 处理中状态 -->
        <el-card v-if="task.status === 'processing'" class="bg-gray-800 border-none shadow-lg">
          <template #header>
            <span>处理进度</span>
          </template>
          <div class="text-center py-8">
            <el-icon class="is-loading text-4xl mb-4 text-blue-400"><loading /></el-icon>
            <p class="text-lg mb-2">正在转写音频文件...</p>
            <p class="text-gray-400">这可能需要几分钟时间，请稍候</p>
            <el-button type="primary" @click="startAutoRefresh" class="mt-4" :disabled="autoRefreshing">
              {{ autoRefreshing ? '自动刷新中...' : '开启自动刷新' }}
            </el-button>
          </div>
        </el-card>
        
        <!-- 转写结果 -->
        <div v-if="task.status === 'completed' && task.segments && task.segments.length > 0">
          <!-- 完整文本 -->
          <el-card class="bg-gray-800 border-none shadow-lg">
            <template #header>
              <div class="flex items-center justify-between">
                <span>完整转写文本</span>
                <div class="flex gap-2">
                  <el-button size="small" @click="copyFullText">复制全文</el-button>
                  <el-button size="small" @click="downloadText">下载文本</el-button>
                </div>
              </div>
            </template>
            
            <div class="bg-gray-700 p-4 rounded-lg">
              <p class="leading-relaxed">{{ fullText }}</p>
            </div>
          </el-card>
          
          <!-- 分段结果 -->
          <el-card class="bg-gray-800 border-none shadow-lg">
            <template #header>
              <div class="flex items-center justify-between">
                <span>分段转写结果</span>
                <div class="flex items-center gap-4">
                  <span class="text-sm text-gray-400">共 {{ task.segments.length }} 个片段</span>
                  <el-switch
                    v-model="showTimestamps"
                    active-text="显示时间戳"
                    inactive-text="隐藏时间戳"
                  />
                </div>
              </div>
            </template>
            
            <div class="space-y-3">
              <div
                v-for="(segment, index) in task.segments"
                :key="index"
                class="flex gap-4 p-3 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
              >
                <div v-if="showTimestamps" class="flex-shrink-0 w-32">
                  <div class="text-xs text-gray-400">
                    {{ formatTime(segment.start_time) }} - {{ formatTime(segment.end_time) }}
                  </div>
                  <div class="text-xs text-green-400">
                    置信度: {{ (segment.confidence * 100).toFixed(1) }}%
                  </div>
                </div>
                <div class="flex-1">
                  <p class="leading-relaxed">{{ segment.text }}</p>
                </div>
              </div>
            </div>
          </el-card>
        </div>
        
        <!-- 等待处理状态 -->
        <el-card v-if="task.status === 'pending'" class="bg-gray-800 border-none shadow-lg">
          <template #header>
            <span>排队等待</span>
          </template>
          <div class="text-center py-8">
            <el-icon class="text-4xl mb-4 text-yellow-400"><clock /></el-icon>
            <p class="text-lg mb-2">任务正在排队等待处理</p>
            <p class="text-gray-400">系统将按顺序处理您的任务</p>
            <el-button type="primary" @click="startAutoRefresh" class="mt-4" :disabled="autoRefreshing">
              {{ autoRefreshing ? '自动刷新中...' : '开启自动刷新' }}
            </el-button>
          </div>
        </el-card>
        
        <!-- 失败状态 -->
        <el-card v-if="task.status === 'failed'" class="bg-gray-800 border-none shadow-lg">
          <template #header>
            <span>处理失败</span>
          </template>
          <div class="text-center py-8">
            <el-icon class="text-4xl mb-4 text-red-400"><close /></el-icon>
            <p class="text-lg mb-2">转写任务处理失败</p>
            <p class="text-gray-400 mb-4">{{ task.error_message || '未知错误' }}</p>
            <div class="flex gap-2 justify-center">
              <el-button type="primary" @click="$router.push('/transcribe')">重新上传</el-button>
              <el-button type="default" @click="$router.push('/')">返回首页</el-button>
            </div>
          </div>
        </el-card>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Loading, Warning, Clock, Close } from '@element-plus/icons-vue';
import { transcriptionAPI } from '../services/api';

const router = useRouter();
const route = useRoute();
const taskId = route.params.id;

const task = ref(null);
const loading = ref(true);
const error = ref(null);
const showTimestamps = ref(true);
const autoRefreshing = ref(false);
let autoRefreshInterval = null;

const fullText = computed(() => {
  if (!task.value?.segments) return '';
  return task.value.segments.map(segment => segment.text).join(' ');
});

onMounted(() => {
  loadTask();
});

onUnmounted(() => {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval);
  }
});

async function loadTask() {
  try {
    loading.value = true;
    error.value = null;
    const result = await transcriptionAPI.getTaskResult(taskId);
    task.value = result;
  } catch (err) {
    console.error('加载任务详情失败:', err);
    if (err.response?.status === 404) {
      error.value = '任务不存在';
    } else if (err.response?.status === 403) {
      error.value = '无权访问此任务';
    } else {
      error.value = '加载失败，请重试';
    }
  } finally {
    loading.value = false;
  }
}

function refreshTask() {
  loadTask();
}

function startAutoRefresh() {
  if (autoRefreshInterval || autoRefreshing.value) return;
  
  autoRefreshing.value = true;
  ElMessage.info('已开启自动刷新，每10秒更新一次');
  
  autoRefreshInterval = setInterval(async () => {
    try {
      const result = await transcriptionAPI.getTaskResult(taskId);
      task.value = result;
      
      // 如果任务完成或失败，停止自动刷新
      if (result.status === 'completed' || result.status === 'failed') {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        autoRefreshing.value = false;
        ElMessage.success('任务状态已更新，停止自动刷新');
      }
    } catch (err) {
      console.error('自动刷新失败:', err);
    }
  }, 10000);
}

function getStatusType(status) {
  const statusMap = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  };
  return statusMap[status] || 'info';
}

function getStatusText(status) {
  const statusMap = {
    'pending': '等待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  };
  return statusMap[status] || status;
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleString('zh-CN');
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

async function copyFullText() {
  try {
    await navigator.clipboard.writeText(fullText.value);
    ElMessage.success('文本已复制到剪贴板');
  } catch (err) {
    ElMessage.error('复制失败');
  }
}

function downloadText() {
  const blob = new Blob([fullText.value], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `转写结果_${task.value.filename}_${Date.now()}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  ElMessage.success('文本文件已下载');
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

:deep(.el-switch__label) {
  color: #d1d5db;
}

:deep(.el-switch__label.is-active) {
  color: #3b82f6;
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style> 
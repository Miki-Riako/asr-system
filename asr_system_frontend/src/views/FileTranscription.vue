<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">离线文件转写</h1>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 max-w-4xl">
      <el-card class="bg-gray-800 border-none shadow-lg">
        <template #header>
          <div class="flex items-center">
            <i class="el-icon-upload mr-2"></i>
            <span>上传音频文件</span>
          </div>
        </template>
        
        <div class="space-y-6">
          <!-- 文件上传区域 -->
          <div>
            <el-upload
              ref="uploadRef"
              class="upload-demo"
              drag
              :auto-upload="false"
              :on-change="handleFileChange"
              :before-remove="handleFileRemove"
              accept=".mp3,.wav,.m4a,.flac"
              :limit="1"
              :on-exceed="handleExceed"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将音频文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip text-gray-400">
                  支持 MP3、WAV、M4A、FLAC 格式，文件大小不超过 100MB
                </div>
              </template>
            </el-upload>
          </div>
          
          <!-- 文件信息 -->
          <div v-if="selectedFile" class="bg-gray-700 p-4 rounded-lg">
            <h4 class="text-lg font-semibold mb-2">文件信息</h4>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-400">文件名：</span>
                <span>{{ selectedFile.name }}</span>
              </div>
              <div>
                <span class="text-gray-400">文件大小：</span>
                <span>{{ formatFileSize(selectedFile.size) }}</span>
              </div>
              <div>
                <span class="text-gray-400">文件类型：</span>
                <span>{{ selectedFile.type || '未知' }}</span>
              </div>
              <div>
                <span class="text-gray-400">预计用时：</span>
                <span>{{ estimatedTime }} 分钟</span>
              </div>
            </div>
          </div>
          
          <!-- 热词选项 -->
          <div class="bg-gray-700 p-4 rounded-lg">
            <h4 class="text-lg font-semibold mb-3">热词设置</h4>
            <div class="flex items-center gap-4">
              <el-switch
                v-model="useHotwords"
                active-text="启用热词增强"
                inactive-text="使用默认模式"
              />
              <el-button 
                type="text" 
                @click="$router.push('/hotwords')"
                class="text-blue-400 hover:text-blue-300"
              >
                管理我的热词
              </el-button>
            </div>
            <div v-if="useHotwords" class="mt-3">
              <p class="text-sm text-gray-400">
                将使用您自定义的热词来提高专业术语的识别准确率
              </p>
            </div>
          </div>
          
          <!-- 提交按钮 -->
          <div class="flex justify-center">
            <el-button
              type="primary"
              size="large"
              :disabled="!selectedFile || uploading"
              :loading="uploading"
              @click="submitTranscription"
              class="px-8 py-3"
            >
              {{ uploading ? '正在提交...' : '开始转写' }}
            </el-button>
          </div>
        </div>
      </el-card>
      
      <!-- 上传进度 -->
      <el-card v-if="uploadProgress.show" class="bg-gray-800 border-none shadow-lg mt-6">
        <template #header>
          <span>上传进度</span>
        </template>
        <div class="space-y-4">
          <el-progress
            :percentage="uploadProgress.percentage"
            :status="uploadProgress.status"
            :stroke-width="8"
          />
          <div class="text-center">
            <p class="text-lg">{{ uploadProgress.message }}</p>
            <p v-if="uploadProgress.taskId" class="text-sm text-gray-400 mt-2">
              任务ID: {{ uploadProgress.taskId }}
            </p>
          </div>
        </div>
      </el-card>
    </main>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';
import { transcriptionAPI } from '../services/api';

const router = useRouter();
const uploadRef = ref();
const selectedFile = ref(null);
const useHotwords = ref(false);
const uploading = ref(false);

const uploadProgress = ref({
  show: false,
  percentage: 0,
  status: '',
  message: '',
  taskId: null
});

const estimatedTime = computed(() => {
  if (!selectedFile.value) return 0;
  // 简单估算：假设1MB大约需要0.5分钟处理
  const sizeMB = selectedFile.value.size / (1024 * 1024);
  return Math.max(1, Math.ceil(sizeMB * 0.5));
});

function handleFileChange(file, fileList) {
  selectedFile.value = file.raw;
}

function handleFileRemove() {
  selectedFile.value = null;
}

function handleExceed() {
  ElMessage.warning('只能上传一个音频文件');
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function submitTranscription() {
  if (!selectedFile.value) {
    ElMessage.error('请先选择要转写的音频文件');
    return;
  }
  
  try {
    uploading.value = true;
    uploadProgress.value = {
      show: true,
      percentage: 10,
      status: '',
      message: '正在上传文件...',
      taskId: null
    };
    
    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value.percentage < 90) {
        uploadProgress.value.percentage += 10;
      }
    }, 200);
    
    // 提交转写任务
    const result = await transcriptionAPI.submitTask(
      selectedFile.value,
      useHotwords.value ? 'user_hotwords' : null
    );
    
    clearInterval(progressInterval);
    
    uploadProgress.value = {
      show: true,
      percentage: 100,
      status: 'success',
      message: '文件上传成功，转写任务已创建',
      taskId: result.id
    };
    
    ElMessage.success('转写任务已提交，正在后台处理');
    
    // 3秒后询问用户是否查看任务
    setTimeout(async () => {
      try {
        await ElMessageBox.confirm(
          '转写任务已开始处理，是否前往查看？',
          '提示',
          {
            confirmButtonText: '查看任务',
            cancelButtonText: '返回首页',
            type: 'info'
          }
        );
        router.push(`/task/${result.id}`);
      } catch {
        router.push('/');
      }
    }, 3000);
    
  } catch (error) {
    console.error('提交转写任务失败:', error);
    uploadProgress.value = {
      show: true,
      percentage: 0,
      status: 'exception',
      message: '上传失败: ' + (error.response?.data?.detail || error.message),
      taskId: null
    };
    ElMessage.error('提交失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    uploading.value = false;
  }
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

:deep(.el-upload) {
  border: 2px dashed #4b5563;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: border-color 0.2s;
}

:deep(.el-upload:hover) {
  border-color: #3b82f6;
}

:deep(.el-upload-dragger) {
  background-color: #4b5563;
  border: none;
}

:deep(.el-upload-dragger:hover) {
  background-color: #6b7280;
}

:deep(.el-switch__label) {
  color: #d1d5db;
}

:deep(.el-switch__label.is-active) {
  color: #3b82f6;
}
</style> 
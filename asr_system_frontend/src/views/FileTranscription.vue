<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4">
        <div class="flex items-center justify-between">
          <h1 class="text-xl font-bold text-blue-400">音频转写</h1>
          <el-button type="primary" plain @click="goBack">返回</el-button>
        </div>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 max-w-4xl">
      <el-card class="bg-gray-800 border-none shadow-lg">
        <template #header>
          <div class="flex items-center">
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
              accept=".mp3,.wav,.m4a,.flac"
              :limit="1"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将音频文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip text-gray-400">
                  支持 MP3、WAV、M4A、FLAC 格式
                </div>
              </template>
            </el-upload>
          </div>
          
          <!-- 提交按钮 -->
          <div class="flex justify-center">
            <el-button
              type="primary"
              :loading="uploading"
              @click="submitTranscription"
            >
              开始转写
            </el-button>
          </div>
        </div>
      </el-card>
      
      <!-- 转写结果 -->
      <el-card v-if="result" class="bg-gray-800 border-none shadow-lg mt-6">
        <template #header>
          <span>转写结果</span>
        </template>
        <div class="terminal-output">
          <pre class="whitespace-pre-wrap text-green-400 font-mono text-sm">{{ result }}</pre>
        </div>
      </el-card>

      <!-- 终端输出 -->
      <el-card v-if="terminalOutput" class="bg-gray-800 border-none shadow-lg mt-6">
        <template #header>
          <span>终端输出</span>
        </template>
        <div class="terminal-output">
          <pre class="whitespace-pre-wrap text-green-400 font-mono text-sm">{{ terminalOutput }}</pre>
        </div>
      </el-card>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { UploadFilled } from '@element-plus/icons-vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const uploadRef = ref();
const selectedFile = ref(null);
const uploading = ref(false);
const result = ref('');
const terminalOutput = ref('');

function goBack() {
  router.back();
}

function handleFileChange(file) {
  selectedFile.value = file.raw;
}

async function submitTranscription() {
  if (!selectedFile.value) {
    ElMessage.error('请先选择要转写的音频文件');
    return;
  }
  
  try {
    uploading.value = true;
    
    const formData = new FormData();
    formData.append('file', selectedFile.value);
    
    const response = await fetch('/api/asr/transcribe/file', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('转写失败');
    }
    
    const data = await response.json();
    result.value = data.result;
    terminalOutput.value = data.terminal_output;
    ElMessage.success('转写完成');
    
  } catch (error) {
    console.error('转写失败:', error);
    ElMessage.error('转写失败: ' + error.message);
  } finally {
    uploading.value = false;
  }
}
</script>

<style scoped>
:deep(.el-card) {
  background-color: #374151;
  border: none;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

:deep(.el-card__header) {
  background-color: rgba(17, 24, 39, 0.4);
  padding: 12px 16px;
  border-bottom: 1px solid rgba(75, 85, 99, 0.4);
}

:deep(.el-upload) {
  border: 2px dashed #4b5563;
  border-radius: 8px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
  background-color: rgba(17, 24, 39, 0.2);
}

:deep(.el-upload:hover) {
  border-color: #3b82f6;
  transform: translateY(-1px);
}

:deep(.el-upload-dragger) {
  background-color: transparent;
  border: none;
  padding: 40px 20px;
}

:deep(.el-upload-dragger:hover) {
  background-color: rgba(107, 114, 128, 0.1);
}

:deep(.el-upload__text) {
  color: #9ca3af;
  margin-top: 16px;
}

:deep(.el-upload__text em) {
  color: #3b82f6;
  font-style: normal;
  font-weight: 500;
}

:deep(.el-button) {
  transition: all 0.3s ease;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.1);
}

.terminal-output {
  background-color: rgba(17, 24, 39, 0.6);
  border-radius: 6px;
  padding: 16px;
  margin-top: 8px;
}

.terminal-output pre {
  margin: 0;
  line-height: 1.5;
}
</style> 
<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">支持热词预测的语音识别系统</h1>
        <div class="flex items-center gap-4">
          <span>{{ username }}</span>
          <el-button type="danger" size="small" @click="logout">退出登录</el-button>
        </div>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4">
      <h2 class="text-2xl font-bold mb-6">欢迎使用语音识别系统</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <el-card class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all">
          <template #header>
            <div class="flex items-center">
              <i class="el-icon-microphone mr-2"></i>
              <span>离线文件转写</span>
            </div>
          </template>
          <div class="text-gray-400">
            上传音频文件，系统会自动进行转写并返回文本结果。
          </div>
          <el-button type="primary" class="mt-4 w-full" @click="$router.push('/transcribe')">开始转写</el-button>
        </el-card>
        
        <el-card class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all">
          <template #header>
            <div class="flex items-center">
              <i class="el-icon-video-play mr-2"></i>
              <span>实时语音转写</span>
            </div>
          </template>
          <div class="text-gray-400">
            使用麦克风进行实时录音，系统会即时转写您的语音内容。
          </div>
          <el-button type="success" class="mt-4 w-full" disabled>即将推出</el-button>
        </el-card>
        
        <el-card class="bg-gray-800 border-none shadow-lg hover:shadow-xl transition-all">
          <template #header>
            <div class="flex items-center">
              <i class="el-icon-s-order mr-2"></i>
              <span>热词管理</span>
            </div>
          </template>
          <div class="text-gray-400">
            添加和管理您的专业领域词汇，提高语音识别准确率。
          </div>
          <el-button type="warning" class="mt-4 w-full" @click="$router.push('/hotwords')">管理热词</el-button>
        </el-card>
      </div>
      
      <h3 class="text-xl font-bold mb-4">最近的转写任务</h3>
      <el-table 
        :data="recentTasks" 
        style="width: 100%" 
        class="mb-4" 
        v-loading="loadingTasks"
        :empty-text="tasksEmptyText"
      >
        <el-table-column prop="id" label="任务ID" width="220"></el-table-column>
        <el-table-column prop="filename" label="文件名称"></el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              :disabled="scope.row.status !== 'completed'" 
              @click="viewTask(scope.row)"
            >
              查看结果
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { authAPI, transcriptionAPI } from '../services/api';
import { ElMessage } from 'element-plus';

const router = useRouter();
const username = ref('用户');
const recentTasks = ref([]);
const loadingTasks = ref(false);
const tasksEmptyText = ref('暂无转写任务');

onMounted(async () => {
  try {
    // 获取当前用户信息
    const userData = await authAPI.getCurrentUser();
    username.value = userData.username;
    
    // 获取最近的转写任务
    loadingTasks.value = true;
    const tasks = await transcriptionAPI.getUserTasks();
    recentTasks.value = tasks;
  } catch (err) {
    console.error('加载数据失败', err);
    if (err.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录');
      logout();
    } else {
      tasksEmptyText.value = '加载任务失败，请刷新重试';
    }
  } finally {
    loadingTasks.value = false;
  }
});

function logout() {
  localStorage.removeItem('token');
  router.push('/login');
}

function viewTask(task) {
  router.push(`/task/${task.id}`);
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

:deep(.el-table) {
  background-color: transparent !important;
}

:deep(.el-table th.el-table__cell) {
  background-color: #1f2937 !important;
}

:deep(.el-table tr) {
  background-color: #374151 !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: #4b5563 !important;
}

:deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #6b7280 !important;
}
</style> 
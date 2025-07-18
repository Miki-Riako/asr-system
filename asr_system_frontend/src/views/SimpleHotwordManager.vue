<!-- File: asr_system_frontend/src/views/SimpleHotwordManager.vue -->
<template>
  <div class="min-h-screen bg-gray-900 text-gray-200 p-4 sm:p-8">
    <div class="container mx-auto max-w-6xl">
      <!-- 头部 -->
      <header class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6">
        <h1 class="text-2xl font-bold text-blue-400">简易热词管理 (hotwords.txt)</h1>
        <el-button type="primary" plain @click="$router.push('/')" class="mt-2 sm:mt-0">返回首页</el-button>
      </header>

      <!-- 操作区 -->
      <el-card class="bg-gray-800 border-none shadow-lg mb-6">
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <!-- 左侧操作按钮 -->
          <div class="flex flex-wrap gap-4 items-center">
            <el-button type="primary" @click="dialogVisible = true">
              <el-icon class="mr-1"><Plus /></el-icon>添加热词
            </el-button>
            <el-button type="success" @click="triggerFileUpload">
              <el-icon class="mr-1"><Upload /></el-icon>批量导入
            </el-button>
            <el-button type="danger" @click="batchDelete" :disabled="selectedHotwords.length === 0">
              <el-icon class="mr-1"><Delete /></el-icon>批量删除 ({{ selectedHotwords.length }})
            </el-button>
            <input type="file" ref="fileInput" @change="handleFileUpload" accept=".txt" style="display: none;" />
          </div>
          <!-- 右侧统计和搜索 -->
          <div class="flex items-center gap-4 text-gray-400">
            <span>共 {{ hotwords.length }} 个热词</span>
          </div>
        </div>
      </el-card>

      <!-- 热词列表 -->
      <el-card class="bg-gray-800 border-none shadow-lg">
        <el-table
          v-loading="loading"
          :data="hotwords"
          style="width: 100%"
          height="60vh"
          @selection-change="handleSelectionChange"
          empty-text="暂无热词，请添加或导入"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="word" label="热词" min-width="300" />
          <el-table-column prop="weight" label="权重" width="120" />
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button type="danger" size="small" @click="deleteHotword(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 添加热词对话框 -->
    <el-dialog v-model="dialogVisible" title="添加热词" width="500px" @close="resetForm">
      <el-form :model="form" label-width="80px">
        <el-form-item label="热词">
          <el-input v-model="form.word" placeholder="请输入热词" />
        </el-form-item>
        <el-form-item label="权重">
          <el-slider v-model="form.weight" :min="1" :max="20" show-input />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="addHotword">添加</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Upload, Delete } from '@element-plus/icons-vue';

const hotwords = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const form = ref({ word: '', weight: 10 });
const selectedHotwords = ref([]);
const fileInput = ref(null);

// 从后端加载热词
const loadHotwords = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/simple-hotwords');
    hotwords.value = response.data;
  } catch (error) {
    ElMessage.error('加载热词列表失败');
  } finally {
    loading.value = false;
  }
};

// 保存热词列表到后端
const saveHotwords = async () => {
  loading.value = true;
  try {
    await axios.post('/simple-hotwords', hotwords.value);
    ElMessage.success('操作成功');
    await loadHotwords(); // 重新加载以确保同步
  } catch (error) {
    ElMessage.error('操作失败');
    await loadHotwords(); // 失败时也重新加载以恢复
  } finally {
    loading.value = false;
  }
};

// 添加单个热词
const addHotword = () => {
  const wordToAdd = form.value.word.trim();
  if (!wordToAdd) {
    ElMessage.warning('热词不能为空');
    return;
  }
  if (hotwords.value.some(h => h.word === wordToAdd)) {
    ElMessage.warning('该热词已存在');
    return;
  }
  hotwords.value.push({ word: wordToAdd, weight: form.value.weight });
  dialogVisible.value = false;
  saveHotwords();
};

// 删除单个热词
const deleteHotword = (row) => {
  ElMessageBox.confirm(`确定要删除热词 "${row.word}" 吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    hotwords.value = hotwords.value.filter(h => h.word !== row.word);
    saveHotwords();
  }).catch(() => {});
};

// 批量删除
const batchDelete = () => {
  if (selectedHotwords.value.length === 0) return;
  ElMessageBox.confirm(`确定要删除选中的 ${selectedHotwords.value.length} 个热词吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    const wordsToDelete = new Set(selectedHotwords.value.map(h => h.word));
    hotwords.value = hotwords.value.filter(h => !wordsToDelete.has(h.word));
    saveHotwords();
  }).catch(() => {});
};

// 处理文件上传
const triggerFileUpload = () => {
  fileInput.value.click();
};

const handleFileUpload = (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    const content = e.target.result;
    const lines = content.split(/\r?\n/);
    const existingWords = new Set(hotwords.value.map(h => h.word));
    let addedCount = 0;
    let updatedCount = 0;

    lines.forEach(line => {
      const parts = line.trim().split(/\s+/);
      if (parts.length >= 2) {
        const word = parts[0];
        const weight = parseInt(parts.slice(-1)[0], 10);
        if (word && !isNaN(weight)) {
          if (existingWords.has(word)) {
            // 更新已存在的词
            const index = hotwords.value.findIndex(h => h.word === word);
            if (hotwords.value[index].weight !== weight) {
              hotwords.value[index].weight = weight;
              updatedCount++;
            }
          } else {
            // 添加新词
            hotwords.value.push({ word, weight });
            existingWords.add(word); // 防止文件内重复
            addedCount++;
          }
        }
      }
    });

    if (addedCount > 0 || updatedCount > 0) {
      ElMessage.success(`导入完成：新增 ${addedCount} 个，更新 ${updatedCount} 个。`);
      saveHotwords();
    } else {
      ElMessage.info('没有新的热词被导入。');
    }
  };
  reader.readAsText(file);
  event.target.value = ''; // 重置input，以便可以再次上传同一个文件
};

// 表格选择
const handleSelectionChange = (val) => {
  selectedHotwords.value = val;
};

// 重置表单
const resetForm = () => {
  form.value = { word: '', weight: 10 };
};

onMounted(loadHotwords);
</script>

<style scoped>
/* 使用与您项目一致的暗黑主题样式 */
:deep(.el-card) {
  background-color: #2d3748;
  border: none;
}
:deep(.el-card__header) {
  color: #e2e8f0;
}
:deep(.el-table), :deep(.el-table__expanded-cell) {
  background-color: transparent !important;
}
:deep(.el-table th.el-table__cell),
:deep(.el-table tr) {
  background-color: #2d3748 !important;
  color: #e2e8f0;
}
:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background-color: #4a5568 !important;
}
:deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #4a5568 !important;
}
:deep(.el-dialog) {
  background-color: #2d3748;
}
</style>
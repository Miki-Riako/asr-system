<template>
  <div class="min-h-screen bg-gray-900 text-gray-200">
    <header class="bg-gray-800 py-4 shadow-md">
      <div class="container mx-auto px-4 flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-400">热词管理</h1>
        <el-button type="primary" @click="$router.push('/')">返回首页</el-button>
      </div>
    </header>
    
    <main class="container mx-auto py-8 px-4 max-w-6xl">
      <!-- 操作工具栏 -->
      <el-card class="bg-gray-800 border-none shadow-lg mb-6">
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center">
            <el-button type="primary" @click="showAddDialog = true">
              <el-icon><plus /></el-icon>
              添加热词
            </el-button>
            <el-button type="success" @click="showImportDialog = true">
              <el-icon><upload /></el-icon>
              批量导入
            </el-button>
            <el-button type="danger" :disabled="selectedRows.length === 0" @click="batchDelete">
              <el-icon><delete /></el-icon>
              批量删除 ({{ selectedRows.length }})
            </el-button>
          </div>
          <div class="flex gap-4 items-center">
            <span class="text-sm text-gray-400">共 {{ total }} 个热词</span>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索热词..."
              prefix-icon="Search"
              clearable
              @input="handleSearch"
              class="w-64"
            />
          </div>
        </div>
      </el-card>
      
      <!-- 热词列表 -->
      <el-card class="bg-gray-800 border-none shadow-lg">
        <el-table
          v-loading="loading"
          :data="filteredHotwords"
          style="width: 100%"
          @selection-change="handleSelectionChange"
          :empty-text="hotwords.length === 0 ? '暂无热词，点击添加按钮创建' : '没有匹配的热词'"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="word" label="热词" min-width="200">
            <template #default="scope">
              <span class="font-medium">{{ scope.row.word }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="weight" label="权重" width="120">
            <template #default="scope">
              <el-tag :type="getWeightType(scope.row.weight)" size="small">
                {{ scope.row.weight }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160">
            <template #default="scope">
              <div class="flex gap-2">
                <el-button type="primary" size="small" @click="editHotword(scope.row)">
                  编辑
                </el-button>
                <el-button type="danger" size="small" @click="deleteHotword(scope.row)">
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
      
      <!-- 添加/编辑热词对话框 -->
      <el-dialog
        v-model="showAddDialog"
        :title="editingHotword ? '编辑热词' : '添加热词'"
        width="500px"
        :close-on-click-modal="false"
      >
        <el-form
          ref="hotwordFormRef"
          :model="hotwordForm"
          :rules="hotwordRules"
          label-width="80px"
        >
          <el-form-item label="热词" prop="word">
            <el-input
              v-model="hotwordForm.word"
              placeholder="请输入热词"
              maxlength="255"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="权重" prop="weight">
            <el-slider
              v-model="hotwordForm.weight"
              :min="1"
              :max="10"
              :marks="weightMarks"
              show-tooltip
            />
            <div class="text-sm text-gray-400 mt-2">
              权重越高，识别优先级越高（建议：常用词1-5，专业术语6-10）
            </div>
          </el-form-item>
        </el-form>
        
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="showAddDialog = false">取消</el-button>
            <el-button type="primary" @click="saveHotword" :loading="saving">
              {{ editingHotword ? '更新' : '添加' }}
            </el-button>
          </div>
        </template>
      </el-dialog>
      
      <!-- 批量导入对话框 -->
      <el-dialog
        v-model="showImportDialog"
        title="批量导入热词"
        width="600px"
        :close-on-click-modal="false"
      >
        <div class="space-y-4">
          <div class="bg-blue-900 p-4 rounded-lg">
            <h4 class="font-semibold mb-2">导入格式说明：</h4>
            <ul class="text-sm space-y-1">
              <li>• 支持 CSV 和 TXT 格式文件</li>
              <li>• CSV 格式：每行一个热词，格式为 "热词,权重"（权重可选，默认为5）</li>
              <li>• TXT 格式：每行一个热词</li>
              <li>• 示例：机器学习,8</li>
              <li>• 最多可导入100个热词（包含现有热词）</li>
            </ul>
          </div>
          
          <el-upload
            ref="importUploadRef"
            :auto-upload="false"
            :on-change="handleImportFileChange"
            :before-remove="handleImportFileRemove"
            accept=".csv,.txt"
            :limit="1"
            drag
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                只能上传 CSV/TXT 文件，且不超过 1MB
              </div>
            </template>
          </el-upload>
          
          <div v-if="importPreview.length > 0" class="bg-gray-700 p-4 rounded-lg">
            <h4 class="font-semibold mb-2">预览（前10条）：</h4>
            <div class="space-y-1 text-sm">
              <div v-for="(item, index) in importPreview.slice(0, 10)" :key="index" class="flex justify-between">
                <span>{{ item.word }}</span>
                <span class="text-gray-400">权重: {{ item.weight }}</span>
              </div>
              <div v-if="importPreview.length > 10" class="text-gray-400">
                ...还有 {{ importPreview.length - 10 }} 条
              </div>
            </div>
          </div>
        </div>
        
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="showImportDialog = false">取消</el-button>
            <el-button 
              type="primary" 
              @click="submitImport" 
              :disabled="importPreview.length === 0"
              :loading="importing"
            >
              导入 {{ importPreview.length }} 个热词
            </el-button>
          </div>
        </template>
      </el-dialog>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Upload, Delete, UploadFilled } from '@element-plus/icons-vue';
import { hotwordAPI } from '../services/api';

const router = useRouter();

// 数据状态
const hotwords = ref([]);
const loading = ref(false);
const saving = ref(false);
const importing = ref(false);
const total = ref(0);
const selectedRows = ref([]);
const searchKeyword = ref('');

// 对话框状态
const showAddDialog = ref(false);
const showImportDialog = ref(false);
const editingHotword = ref(null);

// 表单数据
const hotwordForm = reactive({
  word: '',
  weight: 5
});

const importPreview = ref([]);
const importFile = ref(null);

// 表单验证规则
const hotwordRules = {
  word: [
    { required: true, message: '请输入热词', trigger: 'blur' },
    { min: 1, max: 255, message: '热词长度应在1-255字符之间', trigger: 'blur' }
  ],
  weight: [
    { required: true, message: '请选择权重', trigger: 'change' },
    { type: 'number', min: 1, max: 10, message: '权重必须在1-10之间', trigger: 'change' }
  ]
};

// 权重滑块标记
const weightMarks = {
  1: '低',
  5: '中',
  10: '高'
};

// 计算属性
const filteredHotwords = computed(() => {
  if (!searchKeyword.value) return hotwords.value;
  const keyword = searchKeyword.value.toLowerCase();
  return hotwords.value.filter(item => 
    item.word.toLowerCase().includes(keyword)
  );
});

onMounted(() => {
  loadHotwords();
});

// 加载热词列表
async function loadHotwords() {
  try {
    loading.value = true;
    const result = await hotwordAPI.getUserHotwords(0, 100);
    hotwords.value = result;
    total.value = result.length;
  } catch (error) {
    console.error('加载热词失败:', error);
    ElMessage.error('加载热词失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    loading.value = false;
  }
}

// 表格选择变化
function handleSelectionChange(selection) {
  selectedRows.value = selection;
}

// 搜索处理
function handleSearch() {
  // 搜索是响应式的，由computed自动处理
}

// 编辑热词
function editHotword(hotword) {
  editingHotword.value = hotword;
  hotwordForm.word = hotword.word;
  hotwordForm.weight = hotword.weight;
  showAddDialog.value = true;
}

// 保存热词
async function saveHotword() {
  const hotwordFormRef = ref();
  if (!hotwordFormRef.value) return;
  
  try {
    await hotwordFormRef.value.validate();
    saving.value = true;
    
    if (editingHotword.value) {
      // 更新热词
      await hotwordAPI.updateHotword(editingHotword.value.id, {
        word: hotwordForm.word,
        weight: hotwordForm.weight
      });
      ElMessage.success('热词更新成功');
    } else {
      // 添加热词
      await hotwordAPI.createHotword(hotwordForm.word, hotwordForm.weight);
      ElMessage.success('热词添加成功');
    }
    
    showAddDialog.value = false;
    resetForm();
    loadHotwords();
  } catch (error) {
    console.error('保存热词失败:', error);
    ElMessage.error('保存失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    saving.value = false;
  }
}

// 删除热词
async function deleteHotword(hotword) {
  try {
    await ElMessageBox.confirm(
      `确定要删除热词 "${hotword.word}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await hotwordAPI.deleteHotword(hotword.id);
    ElMessage.success('热词删除成功');
    loadHotwords();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除热词失败:', error);
      ElMessage.error('删除失败: ' + (error.response?.data?.detail || error.message));
    }
  }
}

// 批量删除
async function batchDelete() {
  if (selectedRows.value.length === 0) return;
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个热词吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    // 并行删除所有选中的热词
    await Promise.all(
      selectedRows.value.map(hotword => hotwordAPI.deleteHotword(hotword.id))
    );
    
    ElMessage.success(`成功删除 ${selectedRows.value.length} 个热词`);
    selectedRows.value = [];
    loadHotwords();
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error);
      ElMessage.error('批量删除失败: ' + (error.response?.data?.detail || error.message));
    }
  }
}

// 处理导入文件变化
function handleImportFileChange(file) {
  importFile.value = file.raw;
  parseImportFile(file.raw);
}

function handleImportFileRemove() {
  importFile.value = null;
  importPreview.value = [];
}

// 解析导入文件
async function parseImportFile(file) {
  try {
    const text = await file.text();
    const lines = text.split('\n').filter(line => line.trim());
    const preview = [];
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      
      let word, weight = 5;
      
      // 尝试解析CSV格式
      if (trimmed.includes(',')) {
        const parts = trimmed.split(',');
        word = parts[0].trim();
        if (parts[1]) {
          const w = parseInt(parts[1].trim());
          if (w >= 1 && w <= 10) {
            weight = w;
          }
        }
      } else {
        word = trimmed;
      }
      
      if (word) {
        preview.push({ word, weight });
      }
    }
    
    importPreview.value = preview;
  } catch (error) {
    console.error('解析文件失败:', error);
    ElMessage.error('文件解析失败');
    importPreview.value = [];
  }
}

// 提交导入
async function submitImport() {
  if (!importFile.value) {
    ElMessage.error('请选择要导入的文件');
    return;
  }
  
  try {
    importing.value = true;
    const result = await hotwordAPI.importHotwords(importFile.value);
    
    ElMessage.success(
      `导入完成：成功添加 ${result.added_count} 个热词，跳过 ${result.skipped_count} 个重复热词`
    );
    
    showImportDialog.value = false;
    importFile.value = null;
    importPreview.value = [];
    loadHotwords();
  } catch (error) {
    console.error('导入失败:', error);
    ElMessage.error('导入失败: ' + (error.response?.data?.detail || error.message));
  } finally {
    importing.value = false;
  }
}

// 重置表单
function resetForm() {
  editingHotword.value = null;
  hotwordForm.word = '';
  hotwordForm.weight = 5;
}

// 工具函数
function getWeightType(weight) {
  if (weight <= 3) return 'info';
  if (weight <= 6) return 'warning';
  return 'success';
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

:deep(.el-dialog) {
  background-color: #374151;
}

:deep(.el-dialog__header) {
  background-color: #1f2937;
  margin: 0;
  padding: 16px 20px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}

:deep(.el-upload) {
  border: 2px dashed #4b5563;
  border-radius: 6px;
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

:deep(.el-slider__runway) {
  background-color: #4b5563;
}

:deep(.el-slider__button) {
  border-color: #3b82f6;
}

:deep(.el-form-item__label) {
  color: #d1d5db;
}
</style> 
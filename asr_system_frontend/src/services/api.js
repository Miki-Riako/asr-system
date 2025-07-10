import axios from 'axios';

// 配置axios基础URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
axios.defaults.baseURL = API_BASE_URL;

// 请求拦截器：添加认证token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：处理401错误
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response && error.response.status === 401) {
      // Token过期或无效，清除本地存储并跳转到登录页
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (username, password) => {
    const response = await axios.post('/auth/login', { username, password });
    return response.data;
  },
  
  register: async (username, password) => {
    const response = await axios.post('/auth/register', { username, password });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await axios.get('/auth/me');
    return response.data;
  }
};

// Transcription API
export const transcriptionAPI = {
  submitTask: async (file, hotwordListId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (hotwordListId) {
      formData.append('hotword_list_id', hotwordListId);
    }
    
    const response = await axios.post('/asr/transcribe/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  },
  
  getTaskResult: async (taskId) => {
    const response = await axios.get(`/asr/tasks/${taskId}`);
    return response.data;
  },
  
  getUserTasks: async (skip = 0, limit = 10) => {
    const response = await axios.get(`/asr/tasks?skip=${skip}&limit=${limit}`);
    return response.data;
  }
};

// Hotwords API
export const hotwordAPI = {
  createHotword: async (word, weight) => {
    const response = await axios.post('/hotwords', { word, weight });
    return response.data;
  },
  
  getUserHotwords: async (skip = 0, limit = 100) => {
    const response = await axios.get(`/hotwords?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  updateHotword: async (hotwordId, data) => {
    const response = await axios.put(`/hotwords/${hotwordId}`, data);
    return response.data;
  },
  
  deleteHotword: async (hotwordId) => {
    const response = await axios.delete(`/hotwords/${hotwordId}`);
    return response.data;
  },
  
  importHotwords: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post('/hotwords/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    
    return response.data;
  }
}; 
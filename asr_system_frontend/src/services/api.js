import axios from 'axios';

// 配置axios基础URL - 使用相对路径，依赖vite的代理配置
axios.defaults.withCredentials = true;  // 允许跨域请求携带凭证

// WebSocket URL配置 - 使用相对路径
const WS_BASE_URL = '';  // 空字符串表示使用相对路径

// 请求拦截器：添加认证token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // 确保Content-Type正确设置
    if (config.data instanceof FormData) {
      config.headers['Content-Type'] = 'multipart/form-data';
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
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await axios.post('/auth/token', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  
  register: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    const response = await axios.post('/auth/register', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
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

// Realtime API (WebSocket 相关工具函数)
export const realtimeAPI = {
  getWebSocketUrl: () => {
    const token = localStorage.getItem('token');
    return `${WS_BASE_URL}/ws/asr/transcribe/realtime?token=${token}`;
  },
  
  // 心跳检测
  sendHeartbeat: (websocket) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({
        type: 'ping',
        timestamp: Date.now()
      }));
    }
  },
  
  // 发送命令
  sendCommand: (websocket, command) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify(command));
    }
  }
}; 
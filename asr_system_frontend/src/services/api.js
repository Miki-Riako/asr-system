import axios from 'axios';

// 关键：确保所有API请求都指向后端服务器
axios.defaults.baseURL = 'http://localhost:8080';

// 请求拦截器：自动添加token
axios.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// 响应拦截器：处理401未授权错误
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  /**
   * 【极简版登录】
   * 发送包含用户名和密码的 JSON 对象。
   */
  login: async (username, password) => {
    const response = await axios.post('/auth/token', {
      username: username,
      password: password
    });
    return response.data;
  },
  
  /**
   * 【极简版注册】
   * 发送包含用户名和密码的 JSON 对象。
   */
  register: async (username, password) => {
    const response = await axios.post('/auth/register', {
      username: username,
      password: password
    });
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await axios.get('/auth/me');
    return response.data;
  }
};

// --- 其他API部分保持不变 ---
export const transcriptionAPI = {
  submitTask: async (file, hotwordListId = null) => {
    const formData = new FormData();
    formData.append('file', file);
    if (hotwordListId) {
      formData.append('hotword_list_id', hotwordListId);
    }
    const response = await axios.post('/asr/transcribe/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
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
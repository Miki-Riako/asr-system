import axios from 'axios';

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
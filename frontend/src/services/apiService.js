import axios from 'axios';

class ApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
    this.api = axios.create({
      baseURL: this.baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // 请求拦截器
    this.api.interceptors.request.use(
      (config) => {
        if (this.authToken) {
          config.headers.Authorization = `Bearer ${this.authToken}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 响应拦截器
    this.api.interceptors.response.use(
      (response) => response.data,
      (error) => {
        console.error('API Error:', error.response?.data || error.message);
        throw error;
      }
    );
  }

  setAuthToken(token) {
    this.authToken = token;
  }

  // 用户认证相关
  async loginUser() {
    return await this.api.post('/api/users/auth/login');
  }

  async getProfile() {
    return await this.api.get('/api/users/profile');
  }

  async updateProfile(profileData) {
    return await this.api.put('/api/users/profile', profileData);
  }

  // 偏好管理
  async addPreference(preferenceData) {
    return await this.api.post('/api/users/preferences', preferenceData);
  }

  async removePreference(type, value) {
    return await this.api.delete(`/api/users/preferences/${type}/${value}`);
  }

  // 情绪管理
  async updateMood(moodData) {
    return await this.api.post('/api/users/mood', moodData);
  }

  // 聊天会话管理
  async createChatSession(sessionData) {
    return await this.api.post('/api/users/sessions', sessionData);
  }

  async getUserSessions(limit = 10) {
    return await this.api.get(`/api/users/sessions?limit=${limit}`);
  }

  async getActiveSession() {
    return await this.api.get('/api/users/sessions/active');
  }

  async endChatSession(sessionId) {
    return await this.api.post(`/api/users/sessions/${sessionId}/end`);
  }

  // 消息管理
  async addChatMessage(messageData) {
    return await this.api.post('/api/users/messages', messageData);
  }

  // 推荐管理
  async addRecommendation(recommendationData) {
    return await this.api.post('/api/users/recommendations', recommendationData);
  }

  async getUserRecommendations(limit = 20) {
    return await this.api.get(`/api/users/recommendations?limit=${limit}`);
  }

  async updateRecommendationFeedback(recommendationId, feedback) {
    return await this.api.put(`/api/users/recommendations/${recommendationId}/feedback`, {
      feedback
    });
  }

  // 统计信息
  async getUserStats() {
    return await this.api.get('/api/users/stats');
  }

  // AI 聊天接口
  async chatWithAI(userId, message) {
    return await this.api.post('/api/chat/', {
      user_id: userId,
      message: message
    });
  }

  // 获取艺术品推荐
  async getArtworkRecommendations(requestData) {
    return await this.api.post('/api/recommend/', requestData);
  }

  // 健康检查
  async healthCheck() {
    return await this.api.get('/');
  }
}

export const apiService = new ApiService();

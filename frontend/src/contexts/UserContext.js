import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { apiService } from '../services/apiService';
import toast from 'react-hot-toast';

const UserContext = createContext();

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

export const UserProvider = ({ children }) => {
  const { getToken, isLoaded, userId } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [preferences, setPreferences] = useState([]);
  const [currentMood, setCurrentMood] = useState(null);
  const [chatSessions, setChatSessions] = useState([]);
  const [activeSession, setActiveSession] = useState(null);

  // 初始化用户数据
  useEffect(() => {
    if (isLoaded && userId) {
      initializeUser();
    }
  }, [isLoaded, userId]);

  const initializeUser = async () => {
    try {
      setLoading(true);
      const token = await getToken();
      apiService.setAuthToken(token);

      // 登录/注册用户
      const userData = await apiService.loginUser();
      setUser(userData);
      setPreferences(userData.preferences || []);
      setCurrentMood(userData.current_mood);

      // 获取活跃会话
      const activeSessionData = await apiService.getActiveSession();
      setActiveSession(activeSessionData);

      // 获取会话列表
      const sessions = await apiService.getUserSessions();
      setChatSessions(sessions);

      toast.success(`欢迎回来, ${userData.first_name || userData.email}!`);
    } catch (error) {
      console.error('用户初始化失败:', error);
      toast.error('用户初始化失败，请刷新页面重试');
    } finally {
      setLoading(false);
    }
  };

  // 更新用户资料
  const updateProfile = async (profileData) => {
    try {
      const updatedUser = await apiService.updateProfile(profileData);
      setUser(updatedUser);
      toast.success('资料更新成功!');
      return updatedUser;
    } catch (error) {
      console.error('资料更新失败:', error);
      toast.error('资料更新失败');
      throw error;
    }
  };

  // 添加偏好
  const addPreference = async (preferenceData) => {
    try {
      await apiService.addPreference(preferenceData);
      
      // 更新本地状态
      const existingIndex = preferences.findIndex(
        p => p.type === preferenceData.type && p.value === preferenceData.value
      );
      
      if (existingIndex >= 0) {
        const newPreferences = [...preferences];
        newPreferences[existingIndex] = { ...newPreferences[existingIndex], weight: preferenceData.weight };
        setPreferences(newPreferences);
      } else {
        setPreferences([...preferences, preferenceData]);
      }
      
      toast.success('偏好添加成功!');
    } catch (error) {
      console.error('偏好添加失败:', error);
      toast.error('偏好添加失败');
      throw error;
    }
  };

  // 删除偏好
  const removePreference = async (type, value) => {
    try {
      await apiService.removePreference(type, value);
      setPreferences(preferences.filter(p => !(p.type === type && p.value === value)));
      toast.success('偏好删除成功!');
    } catch (error) {
      console.error('偏好删除失败:', error);
      toast.error('偏好删除失败');
      throw error;
    }
  };

  // 更新情绪
  const updateMood = async (moodData) => {
    try {
      await apiService.updateMood(moodData);
      setCurrentMood(moodData);
      toast.success('情绪更新成功!');
    } catch (error) {
      console.error('情绪更新失败:', error);
      toast.error('情绪更新失败');
      throw error;
    }
  };

  // 创建聊天会话
  const createChatSession = async (sessionName) => {
    try {
      const newSession = await apiService.createChatSession({ session_name: sessionName });
      setChatSessions([newSession, ...chatSessions]);
      setActiveSession(newSession);
      toast.success('新会话创建成功!');
      return newSession;
    } catch (error) {
      console.error('会话创建失败:', error);
      toast.error('会话创建失败');
      throw error;
    }
  };

  // 发送消息
  const sendMessage = async (sessionId, content, messageType = 'user') => {
    try {
      const messageData = {
        session_id: sessionId,
        message_type: messageType,
        content: content
      };
      
      const message = await apiService.addChatMessage(messageData);
      return message;
    } catch (error) {
      console.error('消息发送失败:', error);
      toast.error('消息发送失败');
      throw error;
    }
  };

  // 结束会话
  const endChatSession = async (sessionId) => {
    try {
      await apiService.endChatSession(sessionId);
      setChatSessions(chatSessions.map(s => 
        s.id === sessionId ? { ...s, is_active: false } : s
      ));
      if (activeSession && activeSession.id === sessionId) {
        setActiveSession(null);
      }
      toast.success('会话已结束');
    } catch (error) {
      console.error('结束会话失败:', error);
      toast.error('结束会话失败');
      throw error;
    }
  };

  // 获取用户统计
  const getUserStats = async () => {
    try {
      return await apiService.getUserStats();
    } catch (error) {
      console.error('获取统计失败:', error);
      throw error;
    }
  };

  const value = {
    user,
    loading,
    preferences,
    currentMood,
    chatSessions,
    activeSession,
    
    // Actions
    updateProfile,
    addPreference,
    removePreference,
    updateMood,
    createChatSession,
    sendMessage,
    endChatSession,
    getUserStats,
    setActiveSession,
    
    // Refresh data
    refreshUser: initializeUser
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};

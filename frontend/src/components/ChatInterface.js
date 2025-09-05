import React, { useState, useRef, useEffect } from 'react';
import styled from 'styled-components';
import { 
  Send, 
  Plus, 
  MessageCircle, 
  Bot, 
  User,
  Sparkles,
  Heart,
  Palette
} from 'lucide-react';
import { useUser } from '../contexts/UserContext';
import { apiService } from '../services/apiService';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

const ChatContainer = styled.div`
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
`;

const ChatHeader = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px 16px 0 0;
  padding: 1.5rem;
  display: flex;
  justify-content: between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
`;

const ChatTitle = styled.h1`
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
`;

const NewChatButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s ease;

  &:hover {
    background: #5a67d8;
  }
`;

const ChatBody = styled.div`
  background: rgba(255, 255, 255, 0.95);
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
`;

const MessagesContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const Message = styled.div`
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  ${props => props.$isUser ? 'flex-direction: row-reverse;' : ''}
`;

const MessageAvatar = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${props => props.$isUser ? '#667eea' : '#10b981'};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
`;

const MessageBubble = styled.div`
  max-width: 70%;
  padding: 1rem 1.5rem;
  border-radius: 18px;
  background: ${props => props.$isUser ? '#667eea' : '#f8f9fa'};
  color: ${props => props.$isUser ? 'white' : '#333'};
  line-height: 1.5;
  word-wrap: break-word;
  
  ${props => props.$isUser ? `
    border-bottom-right-radius: 4px;
  ` : `
    border-bottom-left-radius: 4px;
  `}
`;

const MessageTime = styled.div`
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.5rem;
  text-align: ${props => props.$isUser ? 'right' : 'left'};
`;

const RecommendationCard = styled.div`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 1rem;
  margin-top: 0.5rem;
  color: white;
`;

const RecommendationTitle = styled.div`
  font-weight: 600;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const RecommendationText = styled.div`
  opacity: 0.9;
  line-height: 1.4;
`;

const InputContainer = styled.div`
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 0 0 16px 16px;
`;

const InputForm = styled.form`
  display: flex;
  gap: 1rem;
  align-items: flex-end;
`;

const InputWrapper = styled.div`
  flex: 1;
  position: relative;
`;

const MessageInput = styled.textarea`
  width: 100%;
  min-height: 50px;
  max-height: 120px;
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  font-size: 1rem;
  font-family: inherit;
  resize: none;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: #667eea;
  }

  &::placeholder {
    color: #999;
  }
`;

const SendButton = styled.button`
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: #667eea;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;

  &:hover {
    background: #5a67d8;
    transform: scale(1.05);
  }

  &:disabled {
    background: #cbd5e0;
    cursor: not-allowed;
    transform: none;
  }
`;

const EmptyState = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #666;
  gap: 1rem;
`;

const EmptyStateIcon = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const TypingIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #666;
  font-style: italic;
  padding: 0.5rem 0;
`;

const ChatInterface = () => {
  const { user, activeSession, createChatSession, sendMessage } = useUser();
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleNewChat = async () => {
    try {
      const sessionName = `对话 ${new Date().toLocaleString()}`;
      await createChatSession(sessionName);
      setMessages([]);
      toast.success('新对话已创建');
    } catch (error) {
      console.error('创建新对话失败:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading) return;
    
    if (!activeSession) {
      await handleNewChat();
      return;
    }

    const userMessage = inputValue.trim();
    setInputValue('');
    setIsLoading(true);
    setIsTyping(true);

    // 添加用户消息到界面
    const newUserMessage = {
      id: Date.now(),
      content: userMessage,
      type: 'user',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newUserMessage]);

    try {
      // 发送消息到后端
      await sendMessage(activeSession.id, userMessage, 'user');
      
      // 调用AI聊天接口
      const aiResponse = await apiService.chatWithAI(user.id, userMessage);
      
      // 添加AI响应到界面
      const aiMessage = {
        id: Date.now() + 1,
        content: aiResponse.ai_response,
        type: 'assistant',
        timestamp: new Date(),
        extracted_elements: aiResponse.extracted_elements,
        recommendation_triggered: aiResponse.recommendation_triggered
      };
      
      setMessages(prev => [...prev, aiMessage]);
      
      // 如果触发了推荐，获取艺术品推荐
      if (aiResponse.recommendation_triggered) {
        try {
          const recommendations = await apiService.getArtworkRecommendations({
            user_id: user.id,
            extracted_elements: aiResponse.extracted_elements,
            user_profile: aiResponse.user_profile
          });
          
          // 添加推荐消息
          const recommendationMessage = {
            id: Date.now() + 2,
            content: '为您推荐以下艺术作品:',
            type: 'recommendation',
            timestamp: new Date(),
            recommendations: recommendations
          };
          
          setMessages(prev => [...prev, recommendationMessage]);
        } catch (error) {
          console.error('获取推荐失败:', error);
        }
      }
      
      // 保存AI响应消息
      await sendMessage(activeSession.id, aiResponse.ai_response, 'assistant');
      
    } catch (error) {
      console.error('发送消息失败:', error);
      toast.error('发送消息失败，请重试');
      
      // 添加错误消息
      const errorMessage = {
        id: Date.now() + 1,
        content: '抱歉，我现在无法回复您的消息。请稍后再试。',
        type: 'assistant',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    
    return (
      <Message key={message.id} $isUser={isUser}>
        <MessageAvatar $isUser={isUser}>
          {isUser ? <User size={20} /> : <Bot size={20} />}
        </MessageAvatar>
        <div style={{ flex: 1 }}>
          <MessageBubble $isUser={isUser}>
            {message.content}
            
            {message.type === 'recommendation' && message.recommendations && (
              <RecommendationCard>
                <RecommendationTitle>
                  <Palette size={16} />
                  艺术品推荐
                </RecommendationTitle>
                <RecommendationText>
                  {message.recommendations.slice(0, 3).map((artwork, index) => (
                    <div key={index} style={{ marginBottom: '0.5rem' }}>
                      <strong>{artwork.title}</strong> - {artwork.artist}
                      <br />
                      <small>{artwork.description?.substring(0, 100)}...</small>
                    </div>
                  ))}
                </RecommendationText>
              </RecommendationCard>
            )}
            
            {message.recommendation_triggered && (
              <div style={{ 
                marginTop: '0.5rem', 
                padding: '0.5rem', 
                background: 'rgba(255,255,255,0.1)', 
                borderRadius: '8px',
                fontSize: '0.9rem'
              }}>
                <Heart size={14} style={{ marginRight: '0.3rem' }} />
                已为您触发个性化推荐
              </div>
            )}
          </MessageBubble>
          <MessageTime $isUser={isUser}>
            {formatTime(message.timestamp)}
          </MessageTime>
        </div>
      </Message>
    );
  };

  if (!user) {
    return <LoadingSpinner />;
  }

  return (
    <ChatContainer>
      <ChatHeader>
        <ChatTitle>
          <MessageCircle size={24} />
          AI 艺术助手
          {activeSession && (
            <span style={{ fontSize: '1rem', color: '#666', fontWeight: 'normal' }}>
              - {activeSession.session_name}
            </span>
          )}
        </ChatTitle>
        <NewChatButton onClick={handleNewChat}>
          <Plus size={16} />
          新对话
        </NewChatButton>
      </ChatHeader>

      <ChatBody>
        <MessagesContainer>
          {messages.length === 0 ? (
            <EmptyState>
              <EmptyStateIcon>
                <Sparkles size={40} />
              </EmptyStateIcon>
              <h3>开始您的艺术探索之旅</h3>
              <p>告诉我您的心情或艺术偏好，我将为您推荐最适合的艺术作品</p>
            </EmptyState>
          ) : (
            messages.map(renderMessage)
          )}
          
          {isTyping && (
            <TypingIndicator>
              <Bot size={16} />
              AI正在思考中...
            </TypingIndicator>
          )}
          
          <div ref={messagesEndRef} />
        </MessagesContainer>

        <InputContainer>
          <InputForm onSubmit={handleSendMessage}>
            <InputWrapper>
              <MessageInput
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  activeSession 
                    ? "分享您的心情或艺术偏好..." 
                    : "开始新对话，告诉我您的心情..."
                }
                disabled={isLoading}
              />
            </InputWrapper>
            <SendButton 
              type="submit" 
              disabled={!inputValue.trim() || isLoading}
            >
              <Send size={20} />
            </SendButton>
          </InputForm>
        </InputContainer>
      </ChatBody>
    </ChatContainer>
  );
};

export default ChatInterface;

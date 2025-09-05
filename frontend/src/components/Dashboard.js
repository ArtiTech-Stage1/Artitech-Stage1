import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { 
  MessageCircle, 
  Heart, 
  User, 
  TrendingUp, 
  Calendar,
  Palette,
  Sparkles,
  BarChart3
} from 'lucide-react';
import { useUser } from '../contexts/UserContext';
import LoadingSpinner from './LoadingSpinner';

const DashboardContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const WelcomeSection = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  text-align: center;
`;

const WelcomeTitle = styled.h1`
  font-size: 2.5rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 0.5rem;
`;

const WelcomeSubtitle = styled.p`
  font-size: 1.1rem;
  color: #666;
  margin-bottom: 1.5rem;
`;

const QuickActions = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
`;

const ActionCard = styled(Link)`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 1.5rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  }
`;

const ActionIcon = styled.div`
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: ${props => props.$color || '#667eea'};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const ActionTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0;
`;

const ActionDescription = styled.p`
  font-size: 0.9rem;
  color: #666;
  margin: 0;
  line-height: 1.4;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
`;

const StatCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 1.5rem;
`;

const StatHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: between;
  margin-bottom: 1rem;
`;

const StatTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: #333;
  margin: 0;
  flex: 1;
`;

const StatIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: ${props => props.$color || '#667eea'};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 0.5rem;
`;

const StatDescription = styled.p`
  font-size: 0.9rem;
  color: #666;
  margin: 0;
`;

const RecentActivity = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 1.5rem;
`;

const SectionTitle = styled.h2`
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ActivityList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const ActivityItem = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
`;

const ActivityIcon = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: ${props => props.$color || '#667eea'};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const ActivityContent = styled.div`
  flex: 1;
`;

const ActivityTitle = styled.div`
  font-weight: 600;
  color: #333;
  margin-bottom: 0.2rem;
`;

const ActivityTime = styled.div`
  font-size: 0.8rem;
  color: #666;
`;

const Dashboard = () => {
  const { user, loading, chatSessions, currentMood } = useUser();
  const [stats, setStats] = useState(null);

  useEffect(() => {
    // 这里可以获取用户统计数据
    // getUserStats().then(setStats);
  }, []);

  if (loading) {
    return <LoadingSpinner />;
  }

  const quickActions = [
    {
      to: '/chat',
      icon: <MessageCircle size={24} />,
      title: '开始对话',
      description: '与AI助手聊天，获得个性化艺术推荐',
      color: '#667eea'
    },
    {
      to: '/profile',
      icon: <User size={24} />,
      title: '个人资料',
      description: '管理您的偏好设置和个人信息',
      color: '#10b981'
    },
    {
      to: '/recommendations',
      icon: <Heart size={24} />,
      title: '推荐历史',
      description: '查看您的艺术品推荐记录',
      color: '#f59e0b'
    }
  ];

  const mockStats = [
    {
      title: '总对话数',
      value: chatSessions?.length || 0,
      description: '与AI的对话次数',
      icon: <MessageCircle size={20} />,
      color: '#667eea'
    },
    {
      title: '推荐作品',
      value: '12',
      description: '获得的艺术品推荐',
      icon: <Heart size={20} />,
      color: '#f59e0b'
    },
    {
      title: '偏好设置',
      value: user?.preferences?.length || 0,
      description: '已设置的艺术偏好',
      icon: <Palette size={20} />,
      color: '#10b981'
    },
    {
      title: '活跃天数',
      value: '7',
      description: '最近活跃天数',
      icon: <Calendar size={20} />,
      color: '#8b5cf6'
    }
  ];

  const recentActivities = [
    {
      title: '创建了新的聊天会话',
      time: '2小时前',
      icon: <MessageCircle size={16} />,
      color: '#667eea'
    },
    {
      title: '更新了艺术偏好设置',
      time: '1天前',
      icon: <Palette size={16} />,
      color: '#10b981'
    },
    {
      title: '获得了5个新推荐',
      time: '2天前',
      icon: <Heart size={16} />,
      color: '#f59e0b'
    }
  ];

  return (
    <DashboardContainer>
      <WelcomeSection>
        <WelcomeTitle>
          欢迎回来, {user?.first_name || '艺术爱好者'}! 
          <Sparkles size={32} style={{ marginLeft: '0.5rem', color: '#667eea' }} />
        </WelcomeTitle>
        <WelcomeSubtitle>
          {currentMood ? 
            `今天您的心情是 ${currentMood.mood}，让我们为您推荐一些合适的艺术作品吧！` :
            '准备好探索新的艺术世界了吗？让我们开始您的艺术之旅！'
          }
        </WelcomeSubtitle>
      </WelcomeSection>

      <QuickActions>
        {quickActions.map((action, index) => (
          <ActionCard key={index} to={action.to}>
            <ActionIcon $color={action.color}>
              {action.icon}
            </ActionIcon>
            <ActionTitle>{action.title}</ActionTitle>
            <ActionDescription>{action.description}</ActionDescription>
          </ActionCard>
        ))}
      </QuickActions>

      <StatsGrid>
        {mockStats.map((stat, index) => (
          <StatCard key={index}>
            <StatHeader>
              <StatTitle>{stat.title}</StatTitle>
              <StatIcon $color={stat.color}>
                {stat.icon}
              </StatIcon>
            </StatHeader>
            <StatValue>{stat.value}</StatValue>
            <StatDescription>{stat.description}</StatDescription>
          </StatCard>
        ))}
      </StatsGrid>

      <RecentActivity>
        <SectionTitle>
          <TrendingUp size={20} />
          最近活动
        </SectionTitle>
        <ActivityList>
          {recentActivities.map((activity, index) => (
            <ActivityItem key={index}>
              <ActivityIcon $color={activity.color}>
                {activity.icon}
              </ActivityIcon>
              <ActivityContent>
                <ActivityTitle>{activity.title}</ActivityTitle>
                <ActivityTime>{activity.time}</ActivityTime>
              </ActivityContent>
            </ActivityItem>
          ))}
        </ActivityList>
      </RecentActivity>
    </DashboardContainer>
  );
};

export default Dashboard;

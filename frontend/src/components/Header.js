import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { UserButton, useUser as useClerkUser } from '@clerk/clerk-react';
import styled from 'styled-components';
import { Home, User, MessageCircle, Heart, Palette } from 'lucide-react';
import { useUser } from '../contexts/UserContext';

const HeaderContainer = styled.header`
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding: 0 2rem;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 100;
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: bold;
  color: #667eea;
  text-decoration: none;
`;

const Nav = styled.nav`
  display: flex;
  gap: 2rem;
  align-items: center;
`;

const NavLink = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  text-decoration: none;
  color: ${props => props.$active ? '#667eea' : '#666'};
  background: ${props => props.$active ? 'rgba(102, 126, 234, 0.1)' : 'transparent'};
  transition: all 0.2s ease;
  font-weight: ${props => props.$active ? '600' : '400'};

  &:hover {
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
  }
`;

const UserSection = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
`;

const UserInfo = styled.div`
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 0.9rem;
`;

const UserName = styled.span`
  font-weight: 600;
  color: #333;
`;

const UserEmail = styled.span`
  color: #666;
  font-size: 0.8rem;
`;

const MoodIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.8rem;
  background: ${props => getMoodColor(props.$mood)};
  border-radius: 20px;
  font-size: 0.8rem;
  color: white;
  font-weight: 500;
`;

const getMoodColor = (mood) => {
  const moodColors = {
    happy: '#4ade80',
    sad: '#64748b',
    excited: '#f59e0b',
    calm: '#06b6d4',
    anxious: '#ef4444',
    angry: '#dc2626',
    content: '#10b981',
    lonely: '#6b7280',
    default: '#8b5cf6'
  };
  return moodColors[mood] || moodColors.default;
};

const getMoodEmoji = (mood) => {
  const moodEmojis = {
    happy: '😊',
    sad: '😢',
    excited: '🤩',
    calm: '😌',
    anxious: '😰',
    angry: '😠',
    content: '😊',
    lonely: '😔',
    default: '🎨'
  };
  return moodEmojis[mood] || moodEmojis.default;
};

const Header = () => {
  const location = useLocation();
  const { user: clerkUser } = useClerkUser();
  const { user, currentMood } = useUser();

  const navItems = [
    { path: '/', label: '首页', icon: Home },
    { path: '/profile', label: '个人资料', icon: User },
    { path: '/chat', label: 'AI 对话', icon: MessageCircle },
    { path: '/recommendations', label: '推荐历史', icon: Heart },
  ];

  return (
    <HeaderContainer>
      <Logo as={Link} to="/">
        <Palette size={28} />
        ArtTech
      </Logo>

      <Nav>
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            $active={location.pathname === path}
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </Nav>

      <UserSection>
        {currentMood && (
          <MoodIndicator $mood={currentMood.mood}>
            {getMoodEmoji(currentMood.mood)}
            {currentMood.mood}
          </MoodIndicator>
        )}
        
        <UserInfo>
          <UserName>
            {user?.first_name || clerkUser?.firstName || '用户'}
          </UserName>
          <UserEmail>
            {user?.email || clerkUser?.primaryEmailAddress?.emailAddress}
          </UserEmail>
        </UserInfo>
        
        <UserButton 
          appearance={{
            elements: {
              avatarBox: {
                width: '40px',
                height: '40px'
              }
            }
          }}
        />
      </UserSection>
    </HeaderContainer>
  );
};

export default Header;

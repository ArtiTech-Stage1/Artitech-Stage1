import React from 'react';
import { SignIn } from '@clerk/clerk-react';
import styled from 'styled-components';
import { Palette, Sparkles, Heart, MessageCircle } from 'lucide-react';

const LandingContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
`;

const ContentWrapper = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  max-width: 1200px;
  width: 100%;
  align-items: center;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 2rem;
    text-align: center;
  }
`;

const HeroSection = styled.div`
  color: white;
`;

const Title = styled.h1`
  font-size: 3.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
  line-height: 1.2;

  @media (max-width: 768px) {
    font-size: 2.5rem;
  }
`;

const Subtitle = styled.p`
  font-size: 1.2rem;
  margin-bottom: 2rem;
  opacity: 0.9;
  line-height: 1.6;
`;

const FeatureList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
`;

const Feature = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  backdrop-filter: blur(10px);
`;

const FeatureIcon = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const FeatureText = styled.div`
  flex: 1;
`;

const FeatureTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.3rem;
`;

const FeatureDescription = styled.p`
  font-size: 0.9rem;
  opacity: 0.8;
  line-height: 1.4;
`;

const AuthSection = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
`;

const SignInWrapper = styled.div`
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  
  .cl-rootBox {
    width: 100%;
  }
  
  .cl-card {
    box-shadow: none;
    border: none;
  }
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 2rem;
  color: white;
`;

const LandingPage = () => {
  const features = [
    {
      icon: <Sparkles size={24} />,
      title: '智能情感分析',
      description: '基于先进的AI技术，深度理解您的情感状态和艺术偏好'
    },
    {
      icon: <MessageCircle size={24} />,
      title: '个性化对话',
      description: '与AI助手进行自然对话，获得量身定制的艺术推荐'
    },
    {
      icon: <Heart size={24} />,
      title: '精准推荐',
      description: '结合您的情绪、偏好和历史记录，推荐最适合的艺术作品'
    },
    {
      icon: <Palette size={24} />,
      title: '艺术探索',
      description: '发现新的艺术风格，拓展您的艺术视野和品味'
    }
  ];

  return (
    <LandingContainer>
      <ContentWrapper>
        <HeroSection>
          <Logo>
            <Palette size={32} />
            ArtTech
          </Logo>
          
          <Title>
            发现属于你的
            <br />
            艺术世界
          </Title>
          
          <Subtitle>
            通过AI驱动的个性化推荐系统，基于您的情感状态和艺术偏好，
            为您推荐最适合的艺术作品，开启独特的艺术探索之旅。
          </Subtitle>
          
          <FeatureList>
            {features.map((feature, index) => (
              <Feature key={index}>
                <FeatureIcon>
                  {feature.icon}
                </FeatureIcon>
                <FeatureText>
                  <FeatureTitle>{feature.title}</FeatureTitle>
                  <FeatureDescription>{feature.description}</FeatureDescription>
                </FeatureText>
              </Feature>
            ))}
          </FeatureList>
        </HeroSection>

        <AuthSection>
          <SignInWrapper>
            <SignIn 
              appearance={{
                elements: {
                  formButtonPrimary: {
                    backgroundColor: '#667eea',
                    '&:hover': {
                      backgroundColor: '#5a67d8'
                    }
                  },
                  card: {
                    boxShadow: 'none'
                  }
                }
              }}
              redirectUrl="/"
            />
          </SignInWrapper>
        </AuthSection>
      </ContentWrapper>
    </LandingContainer>
  );
};

export default LandingPage;

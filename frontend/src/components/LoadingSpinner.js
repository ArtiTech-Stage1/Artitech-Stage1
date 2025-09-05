import React from 'react';
import styled, { keyframes } from 'styled-components';
import { Palette } from 'lucide-react';

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const pulse = keyframes`
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
`;

const LoadingContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 2rem;
`;

const Spinner = styled.div`
  width: 60px;
  height: 60px;
  border: 4px solid rgba(102, 126, 234, 0.1);
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
  margin-bottom: 1rem;
`;

const LoadingIcon = styled.div`
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 1rem;
  animation: ${pulse} 2s ease-in-out infinite;
`;

const LoadingText = styled.p`
  color: #666;
  font-size: 1rem;
  text-align: center;
  margin: 0;
`;

const LoadingSpinner = ({ text = "加载中...", variant = "spinner" }) => {
  return (
    <LoadingContainer>
      {variant === "spinner" ? (
        <Spinner />
      ) : (
        <LoadingIcon>
          <Palette size={24} />
        </LoadingIcon>
      )}
      <LoadingText>{text}</LoadingText>
    </LoadingContainer>
  );
};

export default LoadingSpinner;

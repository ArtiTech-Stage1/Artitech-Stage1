import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { 
  Heart, 
  ThumbsUp, 
  ThumbsDown, 
  Calendar,
  Palette,
  User,
  Star,
  Filter,
  Search
} from 'lucide-react';
import { useUser } from '../contexts/UserContext';
import { apiService } from '../services/apiService';
import LoadingSpinner from './LoadingSpinner';
import toast from 'react-hot-toast';

const RecommendationsContainer = styled.div`
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
`;

const Header = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 2rem;
  margin-bottom: 2rem;
  text-align: center;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
`;

const Subtitle = styled.p`
  font-size: 1.1rem;
  color: #666;
  margin-bottom: 1.5rem;
`;

const FilterSection = styled.div`
  display: flex;
  gap: 1rem;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
`;

const SearchInput = styled.input`
  padding: 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  min-width: 200px;
  transition: border-color 0.2s ease;

  &:focus {
    outline: none;
    border-color: #667eea;
  }
`;

const FilterButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: 2px solid ${props => props.$active ? '#667eea' : '#e2e8f0'};
  background: ${props => props.$active ? '#667eea' : 'white'};
  color: ${props => props.$active ? 'white' : '#666'};
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;

  &:hover {
    border-color: #667eea;
    color: ${props => props.$active ? 'white' : '#667eea'};
  }
`;

const RecommendationsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
`;

const RecommendationCard = styled.div`
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  padding: 1.5rem;
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  }
`;

const CardHeader = styled.div`
  display: flex;
  justify-content: between;
  align-items: flex-start;
  margin-bottom: 1rem;
`;

const CardTitle = styled.h3`
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin: 0;
  flex: 1;
`;

const CardDate = styled.div`
  font-size: 0.9rem;
  color: #666;
  display: flex;
  align-items: center;
  gap: 0.3rem;
`;

const ArtworksList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1rem;
`;

const ArtworkItem = styled.div`
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
`;

const ArtworkTitle = styled.div`
  font-weight: 600;
  color: #333;
  margin-bottom: 0.3rem;
`;

const ArtworkArtist = styled.div`
  color: #667eea;
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
`;

const ArtworkDescription = styled.div`
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
`;

const ArtworkMeta = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
`;

const MetaTag = styled.span`
  background: ${props => getTagColor(props.$type)};
  color: white;
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
`;

const ContextInfo = styled.div`
  background: #f0f4ff;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
`;

const ContextTitle = styled.div`
  font-weight: 600;
  color: #333;
  margin-bottom: 0.5rem;
`;

const ContextDetails = styled.div`
  font-size: 0.9rem;
  color: #666;
  line-height: 1.4;
`;

const FeedbackSection = styled.div`
  display: flex;
  justify-content: between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #e2e8f0;
`;

const FeedbackButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const FeedbackButton = styled.button`
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.5rem 1rem;
  border: 1px solid ${props => getFeedbackColor(props.$type, props.$active)};
  background: ${props => props.$active ? getFeedbackColor(props.$type, true) : 'white'};
  color: ${props => props.$active ? 'white' : getFeedbackColor(props.$type, false)};
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;

  &:hover {
    background: ${props => getFeedbackColor(props.$type, true)};
    color: white;
  }
`;

const FeedbackStatus = styled.div`
  font-size: 0.9rem;
  color: #666;
  display: flex;
  align-items: center;
  gap: 0.3rem;
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 4rem 2rem;
  color: #666;
`;

const EmptyIcon = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 1rem;
`;

const getTagColor = (type) => {
  const colors = {
    style: '#667eea',
    theme: '#10b981',
    color: '#f59e0b',
    mood: '#ef4444',
    default: '#8b5cf6'
  };
  return colors[type] || colors.default;
};

const getFeedbackColor = (type, active) => {
  if (type === 'liked') {
    return active ? '#10b981' : '#10b981';
  } else if (type === 'disliked') {
    return active ? '#ef4444' : '#ef4444';
  }
  return '#666';
};

const Recommendations = () => {
  const { user } = useUser();
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadRecommendations();
  }, []);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      const data = await apiService.getUserRecommendations(50);
      setRecommendations(data);
    } catch (error) {
      console.error('加载推荐历史失败:', error);
      toast.error('加载推荐历史失败');
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (recommendationId, feedback) => {
    try {
      await apiService.updateRecommendationFeedback(recommendationId, feedback);
      
      // 更新本地状态
      setRecommendations(prev => 
        prev.map(rec => 
          rec.id === recommendationId 
            ? { ...rec, user_feedback: feedback }
            : rec
        )
      );
      
      toast.success('反馈已保存');
    } catch (error) {
      console.error('保存反馈失败:', error);
      toast.error('保存反馈失败');
    }
  };

  const filteredRecommendations = recommendations.filter(rec => {
    // 搜索过滤
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      const matchesSearch = rec.artwork_ids.some(artworkId => 
        artworkId.toLowerCase().includes(searchLower)
      ) || JSON.stringify(rec.recommendation_context).toLowerCase().includes(searchLower);
      
      if (!matchesSearch) return false;
    }
    
    // 反馈过滤
    if (filter === 'liked') return rec.user_feedback === 'liked';
    if (filter === 'disliked') return rec.user_feedback === 'disliked';
    if (filter === 'no_feedback') return !rec.user_feedback;
    
    return true;
  });

  if (loading) {
    return <LoadingSpinner />;
  }

  return (
    <RecommendationsContainer>
      <Header>
        <Title>
          <Heart size={32} />
          推荐历史
        </Title>
        <Subtitle>
          查看您的个性化艺术品推荐记录，并提供反馈帮助我们改进
        </Subtitle>
        
        <FilterSection>
          <SearchInput
            type="text"
            placeholder="搜索推荐记录..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          
          <FilterButton 
            $active={filter === 'all'} 
            onClick={() => setFilter('all')}
          >
            <Filter size={16} />
            全部
          </FilterButton>
          
          <FilterButton 
            $active={filter === 'liked'} 
            onClick={() => setFilter('liked')}
          >
            <ThumbsUp size={16} />
            喜欢的
          </FilterButton>
          
          <FilterButton 
            $active={filter === 'disliked'} 
            onClick={() => setFilter('disliked')}
          >
            <ThumbsDown size={16} />
            不喜欢的
          </FilterButton>
          
          <FilterButton 
            $active={filter === 'no_feedback'} 
            onClick={() => setFilter('no_feedback')}
          >
            <Star size={16} />
            待评价
          </FilterButton>
        </FilterSection>
      </Header>

      {filteredRecommendations.length === 0 ? (
        <EmptyState>
          <EmptyIcon>
            <Heart size={40} />
          </EmptyIcon>
          <h3>暂无推荐记录</h3>
          <p>开始与AI对话，获得个性化的艺术品推荐吧！</p>
        </EmptyState>
      ) : (
        <RecommendationsGrid>
          {filteredRecommendations.map((recommendation) => (
            <RecommendationCard key={recommendation.id}>
              <CardHeader>
                <CardTitle>艺术品推荐</CardTitle>
                <CardDate>
                  <Calendar size={14} />
                  {new Date(recommendation.created_at).toLocaleDateString('zh-CN')}
                </CardDate>
              </CardHeader>

              <ContextInfo>
                <ContextTitle>推荐上下文</ContextTitle>
                <ContextDetails>
                  {recommendation.recommendation_context.mood && (
                    <div>心情: {recommendation.recommendation_context.mood}</div>
                  )}
                  {recommendation.recommendation_context.colors?.length > 0 && (
                    <div>偏好颜色: {recommendation.recommendation_context.colors.join(', ')}</div>
                  )}
                  {recommendation.recommendation_context.themes?.length > 0 && (
                    <div>偏好主题: {recommendation.recommendation_context.themes.join(', ')}</div>
                  )}
                </ContextDetails>
              </ContextInfo>

              <ArtworksList>
                {recommendation.artwork_ids.slice(0, 3).map((artworkId, index) => (
                  <ArtworkItem key={index}>
                    <ArtworkTitle>推荐作品 #{index + 1}</ArtworkTitle>
                    <ArtworkArtist>
                      <User size={14} />
                      ID: {artworkId}
                    </ArtworkArtist>
                    <ArtworkDescription>
                      基于您的偏好和当时的心情状态推荐的艺术作品
                    </ArtworkDescription>
                    <ArtworkMeta>
                      {recommendation.recommendation_context.mood && (
                        <MetaTag $type="mood">{recommendation.recommendation_context.mood}</MetaTag>
                      )}
                      {recommendation.recommendation_context.colors?.slice(0, 2).map(color => (
                        <MetaTag key={color} $type="color">{color}</MetaTag>
                      ))}
                      {recommendation.recommendation_context.themes?.slice(0, 2).map(theme => (
                        <MetaTag key={theme} $type="theme">{theme}</MetaTag>
                      ))}
                    </ArtworkMeta>
                  </ArtworkItem>
                ))}
              </ArtworksList>

              <FeedbackSection>
                <FeedbackButtons>
                  <FeedbackButton
                    $type="liked"
                    $active={recommendation.user_feedback === 'liked'}
                    onClick={() => handleFeedback(recommendation.id, 'liked')}
                  >
                    <ThumbsUp size={14} />
                    喜欢
                  </FeedbackButton>
                  <FeedbackButton
                    $type="disliked"
                    $active={recommendation.user_feedback === 'disliked'}
                    onClick={() => handleFeedback(recommendation.id, 'disliked')}
                  >
                    <ThumbsDown size={14} />
                    不喜欢
                  </FeedbackButton>
                </FeedbackButtons>
                
                <FeedbackStatus>
                  {recommendation.user_feedback ? (
                    <>
                      <Star size={14} />
                      已评价: {recommendation.user_feedback === 'liked' ? '喜欢' : '不喜欢'}
                    </>
                  ) : (
                    '待评价'
                  )}
                </FeedbackStatus>
              </FeedbackSection>
            </RecommendationCard>
          ))}
        </RecommendationsGrid>
      )}
    </RecommendationsContainer>
  );
};

export default Recommendations;

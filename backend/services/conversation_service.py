from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging
from collections import deque
import numpy as np
from models.conversation_models import (
    ConversationState, ConversationTurn, ConversationQualityMetrics, ConversationMemory
)
from models.user_models import UserProfile, MoodEntry
from models.artwork_models import ArtElementsResponse

logger = logging.getLogger(__name__)

class ConversationStateMachine:
    """对话状态机"""
    
    def __init__(self):
        self.states = {
            'GREETING': 'initial_greeting',
            'EMOTION_EXPLORATION': 'explore_emotions',
            'PREFERENCE_GATHERING': 'gather_preferences',
            'CLARIFICATION': 'clarify_requirements',
            'RECOMMENDATION': 'provide_recommendations',
            'FEEDBACK': 'collect_feedback',
            'FOLLOW_UP': 'follow_up_conversation'
        }
        
        self.transition_rules = {
            'GREETING': ['EMOTION_EXPLORATION', 'PREFERENCE_GATHERING'],
            'EMOTION_EXPLORATION': ['PREFERENCE_GATHERING', 'RECOMMENDATION', 'CLARIFICATION'],
            'PREFERENCE_GATHERING': ['RECOMMENDATION', 'CLARIFICATION'],
            'CLARIFICATION': ['RECOMMENDATION', 'EMOTION_EXPLORATION'],
            'RECOMMENDATION': ['FEEDBACK', 'FOLLOW_UP'],
            'FEEDBACK': ['FOLLOW_UP', 'RECOMMENDATION'],
            'FOLLOW_UP': ['RECOMMENDATION', 'EMOTION_EXPLORATION']
        }

    def transition(self, current_state: str, user_input: str, 
                  analysis_result: ArtElementsResponse) -> str:
        """状态转换逻辑"""
        if analysis_result.is_recommendation_query and analysis_result.emotion_intensity in ['medium', 'high']:
            return 'RECOMMENDATION'
        elif analysis_result.needs_guidance:
            if not analysis_result.mood:
                return 'EMOTION_EXPLORATION'
            else:
                return 'PREFERENCE_GATHERING'
        elif current_state == 'RECOMMENDATION':
            return 'FEEDBACK'
        else:
            return 'CLARIFICATION'

class ConversationMemoryNetwork:
    """对话记忆网络"""
    
    def __init__(self, max_short_term: int = 10):
        self.short_term_memory = deque(maxlen=max_short_term)
        self.long_term_memory = {}
        self.episodic_memory = []
        self.semantic_memory = {}

    def update_memory(self, turn_data: ConversationTurn):
        """更新多层记忆结构"""
        # 短期记忆
        self.short_term_memory.append(turn_data)

        # 长期记忆更新
        if self._contains_preference(turn_data.extracted_elements):
            self._update_long_term_preferences(turn_data.extracted_elements)

        # 重要片段识别
        if turn_data.importance_score > 0.8:
            self.episodic_memory.append(turn_data)

        # 语义关联更新
        self._update_semantic_associations(turn_data)

    def _contains_preference(self, extracted_elements: Dict[str, Any]) -> bool:
        """检查是否包含用户偏好"""
        return any([
            extracted_elements.get('colors'),
            extracted_elements.get('themes'),
            extracted_elements.get('styles'),
            extracted_elements.get('mood')
        ])

    def _update_long_term_preferences(self, extracted_elements: Dict[str, Any]):
        """更新长期偏好"""
        for key in ['colors', 'themes', 'styles']:
            if extracted_elements.get(key):
                if key not in self.long_term_memory:
                    self.long_term_memory[key] = {}
                
                for value in extracted_elements[key]:
                    if value in self.long_term_memory[key]:
                        self.long_term_memory[key][value] += 1
                    else:
                        self.long_term_memory[key][value] = 1

    def _update_semantic_associations(self, turn_data: ConversationTurn):
        """更新语义关联"""
        # 基于用户输入和系统响应的关键词提取
        keywords = self._extract_keywords(turn_data.user_input + " " + turn_data.system_response)
        
        for keyword in keywords:
            if keyword not in self.semantic_memory:
                self.semantic_memory[keyword] = []
            
            # 关联相关的对话轮次
            related_turns = [turn for turn in self.short_term_memory 
                           if keyword in turn.user_input or keyword in turn.system_response]
            
            self.semantic_memory[keyword] = related_turns

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简化实现）"""
        # 这里可以使用更复杂的NLP技术
        words = text.lower().split()
        # 过滤常见词汇
        stop_words = {'的', '了', '在', '是', '我', '你', '他', '她', '它', '们', '有', '和', '与', '或'}
        keywords = [word for word in words if word not in stop_words and len(word) > 1]
        return keywords[:5]  # 返回前5个关键词

    def retrieve_relevant_context(self, current_query: str) -> Dict[str, Any]:
        """检索相关上下文"""
        # 从短期记忆中获取直接上下文
        immediate_context = list(self.short_term_memory)[-3:]

        # 从长期记忆中获取相关偏好
        relevant_preferences = self._match_preferences(current_query)

        # 从情节记忆中获取相似经历
        similar_episodes = self._find_similar_episodes(current_query)

        return {
            'immediate': immediate_context,
            'preferences': relevant_preferences,
            'episodes': similar_episodes
        }

    def _match_preferences(self, query: str) -> Dict[str, Any]:
        """匹配相关偏好"""
        matched_preferences = {}
        query_keywords = self._extract_keywords(query)
        
        for category, preferences in self.long_term_memory.items():
            for preference, count in preferences.items():
                if any(keyword in preference for keyword in query_keywords):
                    if category not in matched_preferences:
                        matched_preferences[category] = {}
                    matched_preferences[category][preference] = count
        
        return matched_preferences

    def _find_similar_episodes(self, query: str) -> List[ConversationTurn]:
        """查找相似经历"""
        query_keywords = self._extract_keywords(query)
        similar_episodes = []
        
        for episode in self.episodic_memory:
            episode_text = episode.user_input + " " + episode.system_response
            episode_keywords = self._extract_keywords(episode_text)
            
            # 计算关键词重叠度
            overlap = len(set(query_keywords) & set(episode_keywords))
            if overlap > 0:
                episode.similarity_score = overlap / len(query_keywords)
                similar_episodes.append(episode)
        
        # 按相似度排序
        similar_episodes.sort(key=lambda x: getattr(x, 'similarity_score', 0), reverse=True)
        return similar_episodes[:3]  # 返回前3个最相似的

class EmotionalStateTracker:
    """情感状态追踪器"""
    
    def __init__(self):
        self.emotion_history = []
        self.emotion_transitions = {}
        self.baseline_emotions = {}

    def track_emotion_evolution(self, conversation_history: List[ConversationTurn]) -> Dict[str, Any]:
        """追踪情感演变"""
        emotions = []
        
        for turn in conversation_history:
            if turn.extracted_elements.get('mood'):
                emotions.append({
                    'emotion': turn.extracted_elements['mood'],
                    'intensity': turn.extracted_elements.get('emotion_intensity', 'medium'),
                    'timestamp': turn.timestamp,
                    'trigger': turn.user_input[:50]  # 简化的触发因素
                })

        if not emotions:
            return {
                'current_state': None,
                'evolution_pattern': 'no_emotion_detected',
                'predicted_trend': 'stable',
                'stability_score': 0.0
            }

        # 分析情感变化模式
        transitions = self._analyze_emotion_transitions(emotions)
        
        # 预测情感趋势
        predicted_next = self._predict_emotion_trend(emotions)
        
        # 计算情感稳定性
        stability_score = self._calculate_emotion_stability(emotions)

        return {
            'current_state': emotions[-1] if emotions else None,
            'evolution_pattern': transitions,
            'predicted_trend': predicted_next,
            'stability_score': stability_score
        }

    def _analyze_emotion_transitions(self, emotions: List[Dict[str, Any]]) -> str:
        """分析情感转换模式"""
        if len(emotions) < 2:
            return 'insufficient_data'
        
        transitions = []
        for i in range(1, len(emotions)):
            prev_emotion = emotions[i-1]['emotion']
            curr_emotion = emotions[i]['emotion']
            transitions.append(f"{prev_emotion}->{curr_emotion}")
        
        # 分析转换模式
        if len(set(transitions)) == 1:
            return 'stable_emotion'
        elif len(set(transitions)) > len(transitions) * 0.7:
            return 'volatile_emotion'
        else:
            return 'gradual_change'

    def _predict_emotion_trend(self, emotions: List[Dict[str, Any]]) -> str:
        """预测情感趋势"""
        if len(emotions) < 3:
            return 'insufficient_data'
        
        # 简化的趋势预测
        recent_emotions = emotions[-3:]
        positive_emotions = ['happy', 'excited', 'content', 'peaceful']
        negative_emotions = ['sad', 'anxious', 'angry', 'stressed']
        
        positive_count = sum(1 for e in recent_emotions if e['emotion'] in positive_emotions)
        negative_count = sum(1 for e in recent_emotions if e['emotion'] in negative_emotions)
        
        if positive_count > negative_count:
            return 'improving'
        elif negative_count > positive_count:
            return 'deteriorating'
        else:
            return 'stable'

    def _calculate_emotion_stability(self, emotions: List[Dict[str, Any]]) -> float:
        """计算情感稳定性分数"""
        if len(emotions) < 2:
            return 0.0
        
        # 计算情感变化的频率
        emotion_changes = 0
        for i in range(1, len(emotions)):
            if emotions[i]['emotion'] != emotions[i-1]['emotion']:
                emotion_changes += 1
        
        # 稳定性分数：变化越少，分数越高
        stability_score = 1.0 - (emotion_changes / (len(emotions) - 1))
        return max(0.0, min(1.0, stability_score))

class ConversationService:
    """对话服务主类"""
    
    def __init__(self):
        self.state_machine = ConversationStateMachine()
        self.memory_network = ConversationMemoryNetwork()
        self.emotion_tracker = EmotionalStateTracker()
        self.conversation_states = {}  # 用户ID -> 对话状态

    async def process_conversation_turn(self, user_id: str, user_input: str, 
                                     analysis_result: ArtElementsResponse) -> Dict[str, Any]:
        """处理单轮对话"""
        start_time = datetime.now()
        
        # 获取或创建用户对话状态
        if user_id not in self.conversation_states:
            self.conversation_states[user_id] = ConversationState()
        
        current_state = self.conversation_states[user_id]
        
        # 创建对话轮次
        turn = ConversationTurn(
            turn_id=f"{user_id}_{datetime.now().timestamp()}",
            user_input=user_input,
            system_response=analysis_result.direct_response,
            extracted_elements=analysis_result.dict(),
            importance_score=self._calculate_importance_score(analysis_result)
        )
        
        # 更新记忆网络
        self.memory_network.update_memory(turn)
        
        # 更新对话状态
        self._update_conversation_state(current_state, analysis_result)
        
        # 状态转换
        new_state = self.state_machine.transition(
            current_state.current_phase, user_input, analysis_result
        )
        current_state.current_phase = new_state
        
        # 计算响应时间
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        turn.response_time_ms = int(response_time)
        
        # 生成引导策略
        guidance = await self._generate_guidance_strategy(current_state, analysis_result)
        
        return {
            'response': analysis_result.direct_response,
            'next_state': new_state,
            'guidance': guidance,
            'conversation_metrics': self._calculate_conversation_metrics(user_id),
            'response_time_ms': response_time
        }

    def _calculate_importance_score(self, analysis_result: ArtElementsResponse) -> float:
        """计算对话轮次的重要性分数"""
        score = 0.0
        
        # 情感强度权重
        intensity_weights = {'low': 0.3, 'medium': 0.6, 'high': 0.9}
        score += intensity_weights.get(analysis_result.emotion_intensity, 0.5)
        
        # 推荐查询权重
        if analysis_result.is_recommendation_query:
            score += 0.3
        
        # 信息丰富度权重
        info_score = len(analysis_result.colors) + len(analysis_result.themes) + len(analysis_result.styles)
        score += min(0.2, info_score * 0.05)
        
        return min(1.0, score)

    def _update_conversation_state(self, state: ConversationState, 
                                 analysis_result: ArtElementsResponse):
        """更新对话状态"""
        # 更新信息完整度
        info_score = 0.0
        if analysis_result.colors:
            info_score += 0.2
        if analysis_result.themes:
            info_score += 0.2
        if analysis_result.styles:
            info_score += 0.2
        if analysis_result.mood:
            info_score += 0.4
        
        state.information_completeness = min(1.0, state.information_completeness + info_score * 0.3)
        
        # 更新情感清晰度
        if analysis_result.mood:
            state.emotional_clarity = min(1.0, state.emotional_clarity + 0.3)
        
        # 更新对话深度
        state.conversation_depth += 1
        
        # 更新用户参与度
        if len(analysis_result.user_input) > 20:  # 简化的参与度计算
            state.user_engagement_level = min(1.0, state.user_engagement_level + 0.1)
        
        state.last_updated = datetime.now()

    async def _generate_guidance_strategy(self, current_state: ConversationState, 
                                       analysis_result: ArtElementsResponse) -> Dict[str, Any]:
        """生成引导策略"""
        if analysis_result.is_recommendation_query:
            return {
                'strategy': 'proceed_to_recommendation',
                'message': '准备生成推荐...',
                'next_questions': []
            }
        
        if current_state.information_completeness < 0.3:
            return {
                'strategy': 'deep_exploration',
                'message': '需要更多信息来了解你的需求',
                'next_questions': [
                    '你今天的心情怎么样？',
                    '你希望通过艺术获得什么样的体验？',
                    '你对哪些颜色或主题特别感兴趣？'
                ]
            }
        elif current_state.emotional_clarity < 0.5:
            return {
                'strategy': 'emotion_clarification',
                'message': '让我更好地理解你的情感状态',
                'next_questions': [
                    '能具体描述一下你的感受吗？',
                    '是什么让你有这种心情？',
                    '你希望艺术能帮助你什么？'
                ]
            }
        else:
            return {
                'strategy': 'preference_refinement',
                'message': '让我了解你的具体偏好',
                'next_questions': [
                    '你更喜欢哪种艺术风格？',
                    '你对哪些艺术家或作品有印象？',
                    '你希望看到什么主题的作品？'
                ]
            }

    def _calculate_conversation_metrics(self, user_id: str) -> ConversationQualityMetrics:
        """计算对话质量指标"""
        if user_id not in self.conversation_states:
            return ConversationQualityMetrics(
                engagement_score=0.0,
                recommendation_accuracy=0.0,
                avg_response_time=0.0,
                user_satisfaction=3.0,
                conversation_completion_rate=0.0,
                error_rate=0.0
            )
        
        state = self.conversation_states[user_id]
        
        # 计算参与度分数
        engagement_score = (
            state.user_engagement_level * 0.4 +
            state.information_completeness * 0.3 +
            state.emotional_clarity * 0.3
        )
        
        # 计算对话完成率
        completion_rate = min(1.0, state.conversation_depth / 5.0)
        
        return ConversationQualityMetrics(
            engagement_score=engagement_score,
            recommendation_accuracy=0.8,  # 默认值，实际应该基于用户反馈
            avg_response_time=1.5,  # 默认值，实际应该基于历史数据
            user_satisfaction=4.0,  # 默认值，实际应该基于用户反馈
            conversation_completion_rate=completion_rate,
            error_rate=0.05  # 默认值，实际应该基于错误统计
        )

    def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """获取对话摘要"""
        if user_id not in self.conversation_states:
            return {}
        
        state = self.conversation_states[user_id]
        context = self.memory_network.retrieve_relevant_context("")
        
        return {
            'current_state': state.dict(),
            'conversation_context': context,
            'emotional_evolution': self.emotion_tracker.track_emotion_evolution(
                list(self.memory_network.short_term_memory)
            ),
            'metrics': self._calculate_conversation_metrics(user_id)
        }


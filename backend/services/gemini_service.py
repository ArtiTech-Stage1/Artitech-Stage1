import httpx
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import os
import json
from google import genai
from pydantic import BaseModel
from google.genai import types
from models.artwork_models import ArtElementsResponse
import asyncio
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        # Gemini API 配置
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = "gemini-2.5-flash"

        # 初始化 Gemini 客户端
        self.client = genai.Client()

        # 系统提示词模板
        self.system_prompt_template = self._get_system_prompt_template()
        
        # Few-shot学习示例
        self.few_shot_examples = self._get_few_shot_examples()

    def _get_system_prompt_template(self) -> str:
        """获取系统提示词模板"""
        return """
你是一个专业的艺术品推荐助理，具备以下能力：

核心职责：
1. 深度情感分析：识别用户的情感状态、强度和潜在需求
2. 智能对话引导：通过恰当的问题引导用户表达更多信息
3. 个性化推荐：基于情感、偏好和上下文提供精准推荐

分析框架：
- 情感维度：开心、悲伤、平静、兴奋、焦虑、愤怒、满足、孤独、压力、平和等
- 艺术元素：颜色、主题、风格、时期、技法、构图、笔触、光影
- 用户意图：推荐需求、情感表达、学习探索、闲聊交流

响应策略：
- 当用户情感明确且强烈时：直接进入推荐模式
- 当用户表达模糊时：使用开放性问题引导
- 当用户显示专业兴趣时：提供深度艺术知识
- 当检测到负面情绪时：优先提供情感支持

输出要求：
严格按照JSON schema返回结构化数据，确保所有字段完整且类型正确。
"""

    def _get_few_shot_examples(self) -> List[Dict[str, Any]]:
        """获取Few-shot学习示例"""
        return [
            {
                "user_input": "我最近压力很大，想看些能让我放松的画",
                "expected_output": {
                    "mood": "stressed",
                    "emotion_intensity": "high",
                    "colors": ["soft", "cool", "natural"],
                    "themes": ["nature", "peaceful", "serene"],
                    "styles": ["impressionism", "landscape"],
                    "direct_response": "我理解你现在的压力。让我为你推荐一些宁静舒缓的作品，比如莫奈的《睡莲》系列或者塞尚的普罗旺斯风景画，这些作品的柔和色调和自然主题能帮助你放松心情。",
                    "is_recommendation_query": True,
                    "needs_guidance": False,
                    "is_malicious": False,
                    "confidence_score": 0.95,
                    "extracted_context": {
                        "stress_level": "high",
                        "relaxation_need": True,
                        "art_preference": "calming"
                    }
                }
            },
            {
                "user_input": "我喜欢那种有点忧郁但又很美的画，像莫奈的睡莲那样，但是要更有故事感",
                "expected_output": {
                    "mood": "melancholic_beautiful",
                    "emotion_intensity": "medium",
                    "colors": ["blue", "green", "soft_tones"],
                    "themes": ["nature", "water", "narrative"],
                    "styles": ["impressionism", "storytelling"],
                    "direct_response": "我理解你想要的复杂情感体验。基于你对莫奈睡莲的喜爱和对故事感的追求，我推荐Waterhouse的《The Lady of Shalott》和Millais的《Ophelia》，这些作品既有印象派的色彩美感，又蕴含着深刻的叙事内容。",
                    "is_recommendation_query": True,
                    "needs_guidance": False,
                    "is_malicious": False,
                    "confidence_score": 0.92,
                    "extracted_context": {
                        "emotional_complexity": "melancholic + beautiful",
                        "narrative_requirement": "story_driven",
                        "style_evolution": "impressionism + narrative"
                    }
                }
            }
        ]

    async def analyze_user_input(self, user_input: str, system_prompt: str = None, 
                                conversation_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """分析用户输入，提取艺术相关元素和情感信息"""

        # 构建增强的系统提示词
        enhanced_prompt = self._build_enhanced_prompt(system_prompt, conversation_context)
        
        # 添加Few-shot示例
        full_prompt = self._add_few_shot_examples(enhanced_prompt, user_input)
        
        return await self._call_with_structured_output(user_input, full_prompt)

    def _build_enhanced_prompt(self, system_prompt: str = None, 
                              conversation_context: Dict[str, Any] = None) -> str:
        """构建增强的系统提示词"""
        base_prompt = system_prompt or self.system_prompt_template
        
        if conversation_context:
            context_info = f"""
当前对话上下文：
- 对话轮数: {conversation_context.get('turn_count', 1)}
- 用户参与度: {conversation_context.get('engagement_level', 'unknown')}
- 已收集信息: {conversation_context.get('collected_info', [])}
- 当前阶段: {conversation_context.get('current_phase', 'exploration')}

请根据上下文调整分析策略。
"""
            base_prompt += context_info
        
        return base_prompt

    def _add_few_shot_examples(self, system_prompt: str, user_input: str) -> str:
        """添加Few-shot学习示例"""
        examples_text = "\n\n学习示例：\n"
        for i, example in enumerate(self.few_shot_examples):
            examples_text += f"""
示例{i+1}:
用户输入: "{example['user_input']}"
期望输出: {json.dumps(example['expected_output'], ensure_ascii=False, indent=2)}
"""
        
        examples_text += f"\n\n现在分析用户输入: \"{user_input}\""
        
        return system_prompt + examples_text

    async def _call_with_structured_output(self, user_input: str, system_prompt: str) -> Dict[str, Any]:
        """使用 Gemini API 进行结构化输出调用"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=ArtElementsResponse,
                ),
                contents=user_input,
            )

            # 解析响应
            result_data = json.loads(response.text)
            
            # 验证响应数据
            validated_data = self._validate_response_data(result_data)
            
            logger.info(f"成功分析用户输入: {user_input[:50]}...")

            return {
                "status": "success",
                "type": "structured_response",
                "data": validated_data
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return {
                "status": "error",
                "message": f"Failed to parse JSON response: {e}"
            }
        except Exception as e:
            logger.error(f"Gemini API调用失败: {e}")
            return {
                "status": "error",
                "message": f"Gemini API call failed: {e}"
            }

    def _validate_response_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证响应数据的完整性"""
        required_fields = [
            'mood', 'emotion_intensity', 'colors', 'themes', 'styles',
            'direct_response', 'is_recommendation_query', 'needs_guidance', 'is_malicious'
        ]
        
        # 确保所有必需字段都存在
        for field in required_fields:
            if field not in data:
                data[field] = self._get_default_value(field)
        
        # 添加置信度分数（如果没有的话）
        if 'confidence_score' not in data:
            data['confidence_score'] = 0.8
        
        # 添加提取的上下文（如果没有的话）
        if 'extracted_context' not in data:
            data['extracted_context'] = {}
        
        return data

    def _get_default_value(self, field: str) -> Any:
        """获取字段的默认值"""
        defaults = {
            'mood': None,
            'emotion_intensity': 'medium',
            'colors': [],
            'themes': [],
            'styles': [],
            'direct_response': '我需要更多信息来帮助你。',
            'is_recommendation_query': False,
            'needs_guidance': True,
            'is_malicious': False
        }
        return defaults.get(field, None)

    async def _call_simple(self, user_input: str, system_prompt: str) -> Dict[str, Any]:
        """简单的 Gemini API 调用，返回文本响应"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt
                ),
                contents=user_input,
            )

            return {
                "status": "success",
                "type": "text_response",
                "data": {"direct_response": response.text}
            }

        except Exception as e:
            logger.error(f"简单API调用失败: {e}")
            return {
                "status": "error",
                "message": f"Gemini API call failed: {e}"
            }

    async def generate_conversation_guidance(self, user_input: str, 
                                          current_state: Dict[str, Any]) -> Dict[str, Any]:
        """生成对话引导策略"""
        guidance_prompt = f"""
基于当前对话状态，为用户提供合适的引导：

当前状态：
- 信息完整度: {current_state.get('information_completeness', 0.3)}
- 情感清晰度: {current_state.get('emotional_clarity', 0.4)}
- 对话深度: {current_state.get('conversation_depth', 1)}

用户输入: "{user_input}"

请生成引导策略，包括：
1. 下一步应该问什么问题
2. 如何引导用户表达更多信息
3. 是否应该进入推荐模式
"""
        
        return await self._call_simple(user_input, guidance_prompt)

    async def analyze_emotional_evolution(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析情感演变模式"""
        history_text = "\n".join([
            f"轮次{i+1}: {turn.get('user_input', '')} -> 情感: {turn.get('mood', 'unknown')}"
            for i, turn in enumerate(conversation_history[-5:])  # 最近5轮
        ])
        
        evolution_prompt = f"""
分析以下对话历史中的情感演变模式：

{history_text}

请分析：
1. 情感变化趋势
2. 情感稳定性
3. 情感触发因素
4. 下一步情感预测
"""
        
        return await self._call_simple(history_text, evolution_prompt)

        
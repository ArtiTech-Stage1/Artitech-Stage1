from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from services.gemini_service import GeminiService

# 设置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 全局变量，将在main.py中设置
gemini_service: Optional[GeminiService] = None

class ChatInput(BaseModel):
    user_id: str
    message: str

# 响应的 BaseModel 类
class ExtractedElements(BaseModel):
    mood: Optional[str] = None
    emotion_intensity: Optional[str] = None
    colors: List[str] = Field(default_factory=list)
    themes: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)
    is_recommendation_query: bool = False
    needs_guidance: bool = True
    is_malicious: bool = False

class UserProfileResponse(BaseModel):
    user_id: str
    preferences: Dict[str, Any] = Field(default_factory=dict)
    mood: Optional[str] = None
    last_updated: Optional[str] = None

class ChatResponse(BaseModel):
    user_id: str
    ai_response: str
    extracted_elements: ExtractedElements
    recommendation_triggered: bool

def analyze_emotion_simple(message: str) -> Dict[str, Any]:
    """简单的情感分析函数，替代DeepSeek服务"""
    message_lower = message.lower()
    
    # 情感关键词映射
    emotion_keywords = {
        "happy": ["开心", "高兴", "快乐", "愉快", "兴奋", "happy", "joy", "excited", "cheerful"],
        "sad": ["难过", "悲伤", "沮丧", "失落", "伤心", "sad", "depressed", "upset", "down"],
        "calm": ["平静", "安静", "放松", "宁静", "calm", "peaceful", "relaxed", "serene"],
        "angry": ["愤怒", "生气", "烦躁", "angry", "mad", "furious", "annoyed"],
        "anxious": ["焦虑", "紧张", "担心", "nervous", "anxious", "worried", "stressed"],
        "tired": ["累", "疲惫", "困", "tired", "exhausted", "sleepy"],
        "confused": ["困惑", "迷茫", "不知道", "confused", "lost", "uncertain"]
    }
    
    # 颜色关键词
    color_keywords = {
        "蓝色": "blue", "红色": "red", "绿色": "green", "黄色": "yellow", 
        "紫色": "purple", "橙色": "orange", "黑色": "black", "白色": "white",
        "blue": "blue", "red": "red", "green": "green", "yellow": "yellow",
        "purple": "purple", "orange": "orange", "black": "black", "white": "white"
    }
    
    # 主题关键词
    theme_keywords = {
        "自然": "nature", "城市": "urban", "人物": "portrait", "抽象": "abstract",
        "风景": "landscape", "静物": "still_life", "nature": "nature", "urban": "urban",
        "portrait": "portrait", "abstract": "abstract", "landscape": "landscape"
    }
    
    detected_emotion = None
    emotion_intensity = "low"
    detected_colors = []
    detected_themes = []
    
    # 检测情感
    for emotion, keywords in emotion_keywords.items():
        if any(keyword in message_lower for keyword in keywords):
            detected_emotion = emotion
            # 判断强度
            if any(strong_word in message_lower for strong_word in ["非常", "特别", "很", "extremely", "very", "really"]):
                emotion_intensity = "high"
            else:
                emotion_intensity = "medium"
            break
    
    # 检测颜色
    for color_cn, color_en in color_keywords.items():
        if color_cn in message_lower:
            detected_colors.append(color_en)
    
    # 检测主题
    for theme_cn, theme_en in theme_keywords.items():
        if theme_cn in message_lower:
            detected_themes.append(theme_en)
    
    # 判断是否需要推荐
    has_clear_emotion = detected_emotion is not None and emotion_intensity in ["medium", "high"]
    has_preferences = len(detected_colors) > 0 or len(detected_themes) > 0
    is_recommendation_query = has_clear_emotion or has_preferences
    
    # 生成回复
    if is_recommendation_query:
        if detected_emotion:
            direct_response = f"我理解你现在感到{detected_emotion}，让我为你推荐一些合适的艺术品来配合你的心情。"
        else:
            direct_response = "根据你的偏好，我来为你推荐一些艺术品。"
    else:
        # 需要引导的回复
        guidance_questions = [
            "能告诉我更多关于你今天的感受吗？",
            "你现在的心情如何？开心还是有些沮丧？",
            "有什么特别的事情影响了你的心情吗？",
            "你希望看到什么样的艺术作品？比如颜色或主题？"
        ]
        import random
        direct_response = random.choice(guidance_questions)
    
    return {
        "mood": detected_emotion,
        "emotion_intensity": emotion_intensity,
        "colors": detected_colors,
        "themes": detected_themes,
        "styles": [],
        "direct_response": direct_response,
        "is_recommendation_query": is_recommendation_query,
        "needs_guidance": not is_recommendation_query,
        "is_malicious": False
    }


@router.post("/chat/", response_model=ChatResponse)
async def chat_with_analysis(chat_input: ChatInput) -> ChatResponse:
    """聊天接口，分析用户输入并返回响应"""
    logger.info(f"收到用户 {chat_input.user_id} 的消息: {chat_input.message}")

    if gemini_service is None:
        logger.error("Gemini服务未初始化")
        raise HTTPException(status_code=500, detail="服务器配置错误")
    
    user_id = chat_input.user_id
    user_message = chat_input.message
    
    # 基本安全检查
    if len(user_message.strip()) < 1:
        return ChatResponse(
            user_id=user_id,
            ai_response="请输入一些内容。",
            extracted_elements=ExtractedElements(
                is_recommendation_query=False,
                needs_guidance=True
            ),
            recommendation_triggered=False,
            user_profile=UserProfileResponse(
                user_id=user_id,
                preferences={},
                mood=None,
                last_updated=None
            )
        )
    
    # 注意：这里简化了用户管理，实际应用中应该使用新的用户管理系统
    # 用户管理现在通过 /api/users 路由处理
    
    # 分析用户输入
    # try:
    #     analysis_result = analyze_emotion_simple(user_message)
    #     logger.info(f"情感分析结果: {analysis_result}")
        
    #     extracted_elements = analysis_result
    #     ai_response = analysis_result["direct_response"]
    #     recommendation_triggered = analysis_result["is_recommendation_query"]
        
    #     # 更新用户画像
    #     profile_updates = {}
    #     current_preferences = user.profile.preferences.copy()
        
    #     # 更新情绪（只有明确表达时）
    #     if analysis_result.get("mood") and analysis_result.get("emotion_intensity") in ["medium", "high"]:
    #         profile_updates["mood"] = analysis_result["mood"]
    #         logger.info(f"更新用户 {user_id} 情绪: {analysis_result['mood']}")
        
    #     # 更新偏好
    #     if analysis_result.get("colors"):
    #         current_colors = current_preferences.get("colors", [])
    #         current_preferences["colors"] = list(set(current_colors + analysis_result["colors"]))
            
    #     if analysis_result.get("themes"):
    #         current_themes = current_preferences.get("themes", [])
    #         current_preferences["themes"] = list(set(current_themes + analysis_result["themes"]))
        
    #     if current_preferences != user.profile.preferences:
    #         profile_updates["preferences"] = current_preferences
    #         logger.info(f"更新用户 {user_id} 偏好: {current_preferences}")
        
    #     # 应用更新
    #     if profile_updates:
    #         user_manager.update_user_profile(user_id, profile_updates)
        
    #     # 记录聊天历史
    try:
        gemini_analysis_raw = await gemini_service.analyze_user_input(user_message)
        logger.info(f"Gemini analysis raw result: {gemini_analysis_raw}")

        if gemini_analysis_raw["status"] == "error":
            logger.error(f"Gemini API error: {gemini_analysis_raw['message']}")
            raise HTTPException(status_code=500, detail="Failed to get analysis from AI service.")

        extracted_elements: ExtractedElements
        ai_response: str
        recommendation_triggered: bool = False

        if gemini_analysis_raw["type"] == "structured_response":
            analysis_data = gemini_analysis_raw["data"]

            # Populate extracted_elements from function call
            extracted_elements = ExtractedElements(
                mood=analysis_data.get("mood"),
                emotion_intensity=analysis_data.get("emotion_intensity", "low"),
                colors=analysis_data.get("colors", []),
                themes=analysis_data.get("themes", []),
                styles=analysis_data.get("styles", []),
                is_recommendation_query=analysis_data.get("is_recommendation_query", False),
                needs_guidance=analysis_data.get("needs_guidance", False),
                is_malicious=analysis_data.get("is_malicious", False)
            )
            ai_response = analysis_data.get("direct_response", "I'm still learning, please tell me more.")
            recommendation_triggered = extracted_elements.is_recommendation_query

            # 注意：用户偏好更新现在通过新的用户管理系统处理
            # 这里只处理AI对话逻辑

            if recommendation_triggered:
                # 简化的推荐触发逻辑
                if extracted_elements.mood:
                    ai_response = f"我理解你现在的情绪是{extracted_elements.mood}。让我为你推荐一些合适的艺术作品！"
                else:
                    ai_response = "根据你的偏好，我来为你推荐一些艺术作品。"

                logger.info(f"为用户 {user_id} 触发推荐")

        elif gemini_analysis_raw["type"] == "text_response":
            ai_response = gemini_analysis_raw["data"].get("direct_response", "I'm still learning, please tell me more.")
            extracted_elements = ExtractedElements(
                is_recommendation_query=False,
                needs_guidance=True,
                is_malicious=False
            )
            recommendation_triggered = False # Direct text responses from Gemini for guidance imply no immediate recommendation


        # 注意：聊天历史现在通过新的用户管理系统处理
        # 这里只返回当前对话的响应

        # 构建简化的用户资料响应
        user_profile_response = UserProfileResponse(
            user_id=user_id,
            preferences={},  # 实际偏好需要通过用户管理API获取
            mood=None,
            last_updated=None
        )

        response = ChatResponse(
            user_id=user_id,
            ai_response=ai_response,
            extracted_elements=extracted_elements,
            recommendation_triggered=recommendation_triggered,
            user_profile=user_profile_response
        )

        logger.info(f"返回响应给用户 {user_id}: recommendation_triggered={recommendation_triggered}")
        return response
        
    except Exception as e:
        logger.error(f"处理用户 {user_id} 消息时出错: {str(e)}")

        # 简化的错误响应
        user_profile_response = UserProfileResponse(
            user_id=user_id,
            preferences={},
            mood=None,
            last_updated=None
        )

        return ChatResponse(
            user_id=user_id,
            ai_response="抱歉，我现在无法理解你的消息，请稍后再试。",
            extracted_elements=ExtractedElements(
                is_recommendation_query=False,
                needs_guidance=True
            ),
            recommendation_triggered=False,
            user_profile=user_profile_response
        )

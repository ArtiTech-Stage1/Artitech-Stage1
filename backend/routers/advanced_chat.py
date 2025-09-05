from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局服务引用（由main.py设置）
conversation_service = None
gemini_service = None

class ChatRequest(BaseModel):
    """聊天请求模型"""
    user_id: str
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str
    session_id: str
    conversation_state: Dict[str, Any]
    guidance: Dict[str, Any]
    metrics: Dict[str, Any]
    timestamp: datetime

class ConversationSummaryRequest(BaseModel):
    """对话摘要请求模型"""
    user_id: str
    session_id: Optional[str] = None

class ConversationSummaryResponse(BaseModel):
    """对话摘要响应模型"""
    user_id: str
    current_state: Dict[str, Any]
    conversation_context: Dict[str, Any]
    emotional_evolution: Dict[str, Any]
    metrics: Dict[str, Any]
    timestamp: datetime

@router.post("/chat", response_model=ChatResponse)
async def advanced_chat(request: ChatRequest):
    """高级聊天端点"""
    try:
        if not conversation_service or not gemini_service:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        logger.info(f"处理用户{request.user_id}的聊天请求: {request.message[:50]}...")
        
        # 1. 使用Gemini服务分析用户输入
        analysis_result = await gemini_service.analyze_user_input(
            request.message,
            conversation_context=request.context
        )
        
        if analysis_result['status'] != 'success':
            raise HTTPException(
                status_code=500, 
                detail=f"情感分析失败: {analysis_result.get('message', '未知错误')}"
            )
        
        # 2. 使用对话服务处理对话轮次
        conversation_result = await conversation_service.process_conversation_turn(
            request.user_id,
            request.message,
            analysis_result['data']
        )
        
        # 3. 构建响应
        response = ChatResponse(
            response=conversation_result['response'],
            session_id=request.session_id or f"session_{request.user_id}_{datetime.now().timestamp()}",
            conversation_state=conversation_result.get('conversation_metrics', {}),
            guidance=conversation_result.get('guidance', {}),
            metrics=conversation_result.get('conversation_metrics', {}),
            timestamp=datetime.now()
        )
        
        logger.info(f"用户{request.user_id}的聊天请求处理完成")
        return response
        
    except Exception as e:
        logger.error(f"高级聊天处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/summary/{user_id}", response_model=ConversationSummaryResponse)
async def get_conversation_summary(user_id: str, session_id: Optional[str] = None):
    """获取对话摘要"""
    try:
        if not conversation_service:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        logger.info(f"获取用户{user_id}的对话摘要")
        
        # 获取对话摘要
        summary = conversation_service.get_conversation_summary(user_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="未找到对话记录")
        
        response = ConversationSummaryResponse(
            user_id=user_id,
            current_state=summary.get('current_state', {}),
            conversation_context=summary.get('conversation_context', {}),
            emotional_evolution=summary.get('emotional_evolution', {}),
            metrics=summary.get('metrics', {}),
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"获取对话摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversation/guidance")
async def get_conversation_guidance(request: ChatRequest):
    """获取对话引导策略"""
    try:
        if not gemini_service:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        logger.info(f"为用户{request.user_id}生成对话引导策略")
        
        # 获取当前对话状态
        current_state = {
            'information_completeness': 0.3,
            'emotional_clarity': 0.4,
            'conversation_depth': 1
        }
        
        # 生成引导策略
        guidance = await gemini_service.generate_conversation_guidance(
            request.message, 
            current_state
        )
        
        return {
            "user_id": request.user_id,
            "guidance": guidance,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"生成对话引导策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversation/emotion/analyze")
async def analyze_emotion_evolution(request: ChatRequest):
    """分析情感演变"""
    try:
        if not gemini_service:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        logger.info(f"分析用户{request.user_id}的情感演变")
        
        # 这里应该从数据库获取真实的对话历史
        # 为了演示，我们使用模拟数据
        conversation_history = [
            {
                'user_input': '我今天很开心',
                'mood': 'happy',
                'emotion_intensity': 'high'
            },
            {
                'user_input': '但是有点累',
                'mood': 'tired',
                'emotion_intensity': 'medium'
            }
        ]
        
        # 分析情感演变
        evolution = await gemini_service.analyze_emotional_evolution(conversation_history)
        
        return {
            "user_id": request.user_id,
            "emotional_evolution": evolution,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"分析情感演变失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/state/{user_id}")
async def get_conversation_state(user_id: str):
    """获取用户对话状态"""
    try:
        if not conversation_service:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        logger.info(f"获取用户{user_id}的对话状态")
        
        # 获取对话状态
        summary = conversation_service.get_conversation_summary(user_id)
        
        if not summary:
            return {
                "user_id": user_id,
                "state": "no_conversation",
                "message": "用户尚未开始对话"
            }
        
        return {
            "user_id": user_id,
            "state": summary.get('current_state', {}),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"获取对话状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversation/reset/{user_id}")
async def reset_conversation(user_id: str):
    """重置用户对话状态"""
    try:
        if not conversation_service:
            raise HTTPException(status_code=500, detail="服务未初始化")
        
        logger.info(f"重置用户{user_id}的对话状态")
        
        # 重置对话状态（这里应该实现真正的重置逻辑）
        # 为了演示，我们返回成功消息
        
        return {
            "user_id": user_id,
            "message": "对话状态已重置",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"重置对话状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


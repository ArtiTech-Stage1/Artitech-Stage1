import httpx
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import os
import json
from google import genai
from pydantic import BaseModel
from google.genai import types
load_dotenv()

# 定义响应的 BaseModel 结构
class ArtElementsResponse(BaseModel):
    mood: Optional[str] = None
    emotion_intensity: str  # "low", "medium", "high"
    colors: List[str] = []
    themes: List[str] = []
    styles: List[str] = []
    direct_response: str
    is_recommendation_query: bool
    needs_guidance: bool
    is_malicious: bool

class GeminiService:
    def __init__(self):
        # Gemini API 配置
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = "gemini-2.5-flash"

        # 初始化 Gemini 客户端
        self.client = genai.Client()


    async def analyze_user_input(self, user_input: str, system_prompt: str = None) -> Dict[str, Any]:
        """分析用户输入，提取艺术相关元素和情感信息"""

        # 默认系统提示词
        if system_prompt is None:
            system_prompt = """
            你是一个专业的艺术品推荐助理。你的任务是：
                1. 情感分析：仔细分析用户输入中的情感表达，判断是否有明确的情感流露
                2. 引导对话：如果用户没有明确表达情感，通过温和的问题引导用户分享更多感受
                3. 提取偏好：从用户的表达中提取艺术相关的偏好（颜色、主题、风格等）
                4. 推荐判断：只有当用户明确表达了情感或艺术偏好时，才触发推荐

                请根据用户输入的情感丰富程度来决定回应策略：
                - 如果用户表达了明确的情感（开心、悲伤、焦虑、平静等），提取情感并准备推荐
                - 如果用户只是简单回应或没有明确情感，引导用户分享更多
                - 如果用户表达了艺术偏好，也可以触发推荐

                请以JSON格式返回分析结果，包含以下字段：
                - mood: 用户的主要情绪（如果没有明确情感表达则为null）
                - emotion_intensity: 情感表达的强度（low/medium/high）
                - colors: 用户提到的颜色偏好数组
                - themes: 用户提到的主题数组
                - styles: 用户提到的艺术风格数组
                - direct_response: 对用户的回复
                - is_recommendation_query: 是否应该触发艺术品推荐
                - needs_guidance: 是否需要进一步引导用户表达情感
                - is_malicious: 判断用户输入是否包含恶意或不当内容
            """

        return await self._call_with_structured_output(user_input, system_prompt)

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

            return {
                "status": "success",
                "type": "structured_response",
                "data": result_data
            }

        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Failed to parse JSON response: {e}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Gemini API call failed: {e}"
            }

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
            return {
                "status": "error",
                "message": f"Gemini API call failed: {e}"
            }

        
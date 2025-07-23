import httpx
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import os

load_dotenv()

class DeepseekService:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.api_url = os.getenv("DEEPSEEK_API_URL")
        self.model = os.getenv("DEEPSEEK_MODEL")

    async def analyze_user_input(self, user_input: str, system_prompt: str, function_tool: str) -> Dict[str, Any]:
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
        """
        function_tool = [
                {
                    "name": "extract_art_elements",
                    "description": "从用户输入中提取艺术品推荐相关的元素和用户情绪，并判断是否需要进一步引导。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mood": {"type": "string", "description": "用户的主要情绪，例如：开心、悲伤、平静、兴奋、焦虑、愤怒、满足、孤独等。如果没有明确情感表达则为null。"},
                            "emotion_intensity": {"type": "string", "enum": ["low", "medium", "high"], "description": "情感表达的强度：low=模糊或轻微，medium=一般，high=强烈明确"},
                            "colors": {"type": "array", "items": {"type": "string"}, "description": "用户提到的颜色偏好。"},
                            "themes": {"type": "array", "items": {"type": "string"}, "description": "用户提到的主题，例如：自然、城市、人物、抽象、风景、静物等。"},
                            "styles": {"type": "array", "items": {"type": "string"}, "description": "用户提到的艺术风格，例如：印象派、立体主义、现代艺术、古典主义等。"},
                            "direct_response": {"type": "string", "description": "对用户的回复，如果需要引导则提出温和的问题。"},
                            "is_recommendation_query": {"type": "boolean", "description": "是否应该触发艺术品推荐。只有当用户有明确情感表达(emotion_intensity为medium或high)或明确艺术偏好时才为true。"},
                            "needs_guidance": {"type": "boolean", "description": "是否需要进一步引导用户表达情感。当用户回应过于简单或模糊时为true。"},
                            "is_malicious": {"type": "boolean", "description": "判断用户输入是否包含恶意或不当内容。"}
                        },
                        "required": ["emotion_intensity", "direct_response", "is_recommendation_query", "needs_guidance", "is_malicious"]
                    }
                }
            ]
        await self._call(user_input, system_prompt, function_tool)

    async def _call(self, user_input: str, system_prompt: str, function_tool: List[Dict]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "functions": function_tool,
            "function_call": "auto" # 自动决定是否调用函数
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f"{self.api_url}/chat/completions", headers=headers, json=payload, timeout=30)
                response.raise_for_status()  # 检查HTTP错误
                response_data = response.json()

                # 处理 Deepseek 的响应，根据它是否调用了函数来提取信息
                if "choices" in response_data and response_data["choices"]:
                    choice = response_data["choices"][0]
                    if "function_call" in choice["message"] and choice["message"]["function_call"]["name"] == "extract_art_elements":
                        # 解析函数调用的参数
                        import json
                        function_args = json.loads(choice["message"]["function_call"]["arguments"])
                        return {
                            "status": "success",
                            "type": "function_call",
                            "data": function_args
                        }
                    elif "content" in choice["message"]:
                        # 直接的文本回复
                        return {
                            "status": "success",
                            "type": "text_response",
                            "data": {"direct_response": choice["message"]["content"]}
                        }
                return {"status": "error", "message": "Deepseek did not return expected data format."}

            except httpx.HTTPStatusError as e:
                return {"status": "error", "message": f"HTTP error occurred: {e.response.status_code} - {e.response.text}"}
            except httpx.RequestError as e:
                return {"status": "error", "message": f"An error occurred while requesting Deepseek API: {e}"}
            except Exception as e:
                return {"status": "error", "message": f"An unexpected error occurred: {e}"}
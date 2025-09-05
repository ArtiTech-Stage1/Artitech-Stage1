# #!/usr/bin/env python3
# """
# 测试 Gemini Service 迁移的脚本
# """

# import asyncio
# import sys
# import os
# from dotenv import load_dotenv

# # 添加当前目录到 Python 路径
# # sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# load_dotenv()
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# from services.gemini_service import GeminiService

# async def test_gemini_service():
#     """测试 Gemini Service 的基本功能"""
#     print("🚀 开始测试 Gemini Service...")
    
#     # 初始化服务
#     try:
#         gemini_service = GeminiService()
#         print("✅ Gemini Service 初始化成功")
#     except Exception as e:
#         print(f"❌ Gemini Service 初始化失败: {e}")
#         return False
    
#     # 测试用例
#     test_cases = [
#         "我今天感觉很开心，想看一些明亮的艺术作品",
#         "我有点难过，需要一些安慰",
#         "我喜欢蓝色和自然主题的画作",
#         "你好"
#     ]
    
#     for i, test_input in enumerate(test_cases, 1):
#         print(f"\n📝 测试用例 {i}: {test_input}")
        
#         try:
#             result = await gemini_service.analyze_user_input(test_input)
            
#             if result["status"] == "success":
#                 print(f"✅ 分析成功")
#                 print(f"   类型: {result['type']}")
                
#                 if result["type"] == "structured_response":
#                     data = result["data"]
#                     print(f"   情绪: {data.get('mood', 'None')}")
#                     print(f"   情感强度: {data.get('emotion_intensity', 'None')}")
#                     print(f"   推荐查询: {data.get('is_recommendation_query', False)}")
#                     print(f"   需要引导: {data.get('needs_guidance', False)}")
#                     print(f"   AI回复: {data.get('direct_response', 'None')[:100]}...")
#                 elif result["type"] == "text_response":
#                     print(f"   AI回复: {result['data'].get('direct_response', 'None')[:100]}...")
                    
#             else:
#                 print(f"❌ 分析失败: {result.get('message', 'Unknown error')}")
                
#         except Exception as e:
#             print(f"❌ 测试失败: {e}")
    
#     print("\n🎉 测试完成!")
#     return True

# if __name__ == "__main__":
#     # 检查环境变量
#     if not os.getenv("GEMINI_API_KEY"):
#         print("❌ 错误: 未找到 GEMINI_API_KEY 环境变量")
#         print("请确保在 .env 文件中设置了 GEMINI_API_KEY")
#         sys.exit(1)
    
#     # 运行测试
#     asyncio.run(test_gemini_service())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.gemini_service import GeminiService
from services.conversation_service import ConversationService
from services.advanced_rag_service import AdvancedRAGService
from services.recommendation_engine import HybridRecommendationEngine
from database.config import init_database, close_database
from user_management import user_router
from user_management.auth import AuthMiddleware
import logging
import sys
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="艺术品推荐后端",
    description="基于 Gemini 的智能艺术品推荐服务 - 完整实现版",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化所有服务
gemini_service = GeminiService()
conversation_service = ConversationService()
rag_service = AdvancedRAGService()
recommendation_engine = HybridRecommendationEngine()

logger.info("所有核心服务初始化完成")

@app.on_event("startup")
async def startup_event():
    logger.info("初始化数据库连接...")
    await init_database()
    logger.info("应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("关闭数据库连接...")
    await close_database()
    logger.info("应用关闭")

@app.get("/")
async def root():
    logger.info("根路径被访问")
    return {
        "message": "欢迎来到艺术品推荐API！", 
        "version": "2.0.0",
        "features": [
            "高级情感分析",
            "智能对话引导", 
            "多级RAG检索",
            "混合推荐算法",
            "对话状态管理",
            "情感演变追踪"
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "services": {
            "gemini_service": "active",
            "conversation_service": "active", 
            "rag_service": "active",
            "recommendation_engine": "active"
        },
        "timestamp": datetime.now().isoformat()
    }

# 导入并注册路由（避免循环导入）
from routers.chat import router as chat_router
from routers.recommend import router as recommend_router
from artwork_retrieval.routes import router as artwork_router
from routers.advanced_chat import router as advanced_chat_router
from routers.advanced_recommend import router as advanced_recommend_router

app.include_router(chat_router, prefix="/api", tags=["Chat & Extraction"])
app.include_router(recommend_router, prefix="/api", tags=["Artworks Recommendation"])
app.include_router(artwork_router, tags=["Artwork Retrieval"])
app.include_router(user_router, tags=["User Management"])
app.include_router(advanced_chat_router, prefix="/api/v2", tags=["Advanced Chat System"])
app.include_router(advanced_recommend_router, prefix="/api/v2", tags=["Advanced Recommendation System"])

# 将服务传递给路由
from routers import chat, recommend
chat.gemini_service = gemini_service
recommend.gemini_service = gemini_service

# 将高级服务传递给高级路由
from routers import advanced_chat, advanced_recommend
advanced_chat.conversation_service = conversation_service
advanced_chat.gemini_service = gemini_service
advanced_recommend.recommendation_engine = recommendation_engine
advanced_recommend.rag_service = rag_service

if __name__ == "__main__":
    import uvicorn
    logger.info("启动服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
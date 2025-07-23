from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from services.gemini_service import GeminiService
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
    description="基于 Gemini 的智能艺术品推荐服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
gemini_service = GeminiService()
logger.info("Gemini服务初始化完成")

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
    return {"message": "欢迎来到艺术品推荐API！", "timestamp": datetime.now().isoformat()}

# 导入并注册路由（避免循环导入）
from routers.chat import router as chat_router
from routers.recommend import router as recommend_router

app.include_router(chat_router, prefix="/api", tags=["Chat & Extraction"])
app.include_router(recommend_router, prefix="/api", tags=["Artworks Recommendation"])
app.include_router(user_router, tags=["User Management"])
app.include_router(user_router, tags=["User Management"])

# 将gemini_service传递给路由
from routers import chat
chat.gemini_service = gemini_service


if __name__ == "__main__":
    import uvicorn
    logger.info("启动服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
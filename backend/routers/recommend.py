from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

# 设置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 扩展的艺术品数据库
ARTWORKS_DATABASE = [
    {
        "id": "A001", 
        "title": "星夜", 
        "artist": "梵高", 
        "style": "后印象派", 
        "colors": ["blue", "yellow"], 
        "theme": "nature",
        "mood_match": ["calm", "sad", "anxious"],
        "description": "梵高的经典作品，蓝色和黄色的旋转星空"
    },
    {
        "id": "A002", 
        "title": "记忆的永恒", 
        "artist": "达利", 
        "style": "超现实主义", 
        "colors": ["brown", "orange"], 
        "theme": "abstract",
        "mood_match": ["confused", "anxious"],
        "description": "达利的超现实主义杰作，融化的时钟"
    },
    {
        "id": "A003", 
        "title": "神奈川冲浪里", 
        "artist": "葛饰北斋", 
        "style": "浮世绘", 
        "colors": ["blue", "white"], 
        "theme": "nature",
        "mood_match": ["calm", "happy"],
        "description": "日本浮世绘经典，动感的海浪"
    },
    {
        "id": "A004", 
        "title": "呐喊", 
        "artist": "蒙克", 
        "style": "表现主义", 
        "colors": ["red", "orange"], 
        "theme": "portrait",
        "mood_match": ["angry", "anxious", "sad"],
        "description": "表现主义的代表作，情感的强烈表达"
    },
    {
        "id": "A005", 
        "title": "蒙娜丽莎", 
        "artist": "达芬奇", 
        "style": "文艺复兴", 
        "colors": ["brown", "green"], 
        "theme": "portrait",
        "mood_match": ["calm", "happy"],
        "description": "文艺复兴时期的肖像画杰作"
    },
    {
        "id": "A006", 
        "title": "向日葵", 
        "artist": "梵高", 
        "style": "后印象派", 
        "colors": ["yellow", "orange"], 
        "theme": "nature",
        "mood_match": ["happy", "calm"],
        "description": "梵高的温暖向日葵系列"
    },
    {
        "id": "A007", 
        "title": "睡莲", 
        "artist": "莫奈", 
        "style": "印象派", 
        "colors": ["blue", "green", "purple"], 
        "theme": "nature",
        "mood_match": ["calm", "tired"],
        "description": "莫奈的宁静睡莲池塘"
    },
    {
        "id": "A008", 
        "title": "自由引导人民", 
        "artist": "德拉克洛瓦", 
        "style": "浪漫主义", 
        "colors": ["red", "blue", "white"], 
        "theme": "portrait",
        "mood_match": ["angry", "happy"],
        "description": "法国浪漫主义的激情之作"
    }
]

class RecommendationInput(BaseModel):
    user_id: str
    extracted_elements: Dict[str, Any]
    user_profile: Dict[str, Any]

class Artwork(BaseModel):
    id: str
    title: str
    artist: str
    style: str
    colors: List[str]
    theme: str
    description: str

def calculate_artwork_score(artwork: Dict, mood: str, colors: List[str], themes: List[str], styles: List[str]) -> float:
    """计算艺术品匹配分数"""
    score = 0.0
    
    # 情绪匹配（权重最高）
    if mood and mood in artwork.get("mood_match", []):
        score += 3.0
        logger.debug(f"艺术品 {artwork['title']} 情绪匹配 {mood}: +3.0")
    
    # 颜色匹配
    artwork_colors = artwork.get("colors", [])
    color_matches = len(set(colors) & set(artwork_colors))
    if color_matches > 0:
        score += color_matches * 1.5
        logger.debug(f"艺术品 {artwork['title']} 颜色匹配 {color_matches}: +{color_matches * 1.5}")
    
    # 主题匹配
    if artwork.get("theme") in themes:
        score += 2.0
        logger.debug(f"艺术品 {artwork['title']} 主题匹配: +2.0")
    
    # 风格匹配
    if artwork.get("style") in styles:
        score += 1.5
        logger.debug(f"艺术品 {artwork['title']} 风格匹配: +1.5")
    
    return score

@router.post("/recommend/", response_model=List[Artwork])
async def get_artworks_recommendation(recommend_input: RecommendationInput):
    """获取艺术品推荐"""
    logger.info(f"为用户 {recommend_input.user_id} 生成推荐")
    
    user_id = recommend_input.user_id
    extracted_elements = recommend_input.extracted_elements
    user_profile = recommend_input.user_profile
    
    # 提取偏好信息
    current_mood = extracted_elements.get("mood") or user_profile.get("mood")
    current_colors = extracted_elements.get("colors", [])
    current_themes = extracted_elements.get("themes", [])
    current_styles = extracted_elements.get("styles", [])
    
    # 从用户画像中获取历史偏好
    preferences = user_profile.get("preferences", {})
    historical_colors = preferences.get("colors", [])
    historical_themes = preferences.get("themes", [])
    historical_styles = preferences.get("styles", [])
    
    # 合并当前和历史偏好
    all_colors = list(set(current_colors + historical_colors))
    all_themes = list(set(current_themes + historical_themes))
    all_styles = list(set(current_styles + historical_styles))
    
    logger.info(f"推荐参数 - 情绪: {current_mood}, 颜色: {all_colors}, 主题: {all_themes}, 风格: {all_styles}")
    
    # 计算每个艺术品的匹配分数
    scored_artworks = []
    for artwork in ARTWORKS_DATABASE:

        ## TODO: optimize the retrieval
        score = calculate_artwork_score(artwork, current_mood, all_colors, all_themes, all_styles)
        if score > 0:  # 只包含有匹配的艺术品
            scored_artworks.append((artwork, score))
            logger.debug(f"艺术品 {artwork['title']} 总分: {score}")
    
    # 按分数排序
    scored_artworks.sort(key=lambda x: x[1], reverse=True)
    
    # 如果没有匹配的艺术品，提供默认推荐
    if not scored_artworks:
        logger.info("没有找到匹配的艺术品，使用默认推荐")
        if current_mood:
            # 基于情绪的默认推荐
            mood_defaults = {
                "happy": ["A006", "A003", "A005"],  # 向日葵、神奈川冲浪里、蒙娜丽莎
                "sad": ["A001", "A004"],  # 星夜、呐喊
                "calm": ["A007", "A001", "A005"],  # 睡莲、星夜、蒙娜丽莎
                "angry": ["A004", "A008"],  # 呐喊、自由引导人民
                "anxious": ["A001", "A007"],  # 星夜、睡莲
                "tired": ["A007", "A001"],  # 睡莲、星夜
                "confused": ["A002"]  # 记忆的永恒
            }
            default_ids = mood_defaults.get(current_mood, ["A001", "A003", "A005"])
            recommended_artworks = [artwork for artwork in ARTWORKS_DATABASE if artwork["id"] in default_ids]
        else:
            # 通用默认推荐
            recommended_artworks = ARTWORKS_DATABASE[:3]
    else:
        # 取前5个最匹配的
        recommended_artworks = [artwork for artwork, score in scored_artworks[:5]]
    
    logger.info(f"为用户 {user_id} 推荐了 {len(recommended_artworks)} 件艺术品")
    
    # 转换为响应格式
    result = []
    for artwork in recommended_artworks:
        result.append(Artwork(
            id=artwork["id"],
            title=artwork["title"],
            artist=artwork["artist"],
            style=artwork["style"],
            colors=artwork["colors"],
            theme=artwork["theme"],
            description=artwork["description"]
        ))
    
    return result

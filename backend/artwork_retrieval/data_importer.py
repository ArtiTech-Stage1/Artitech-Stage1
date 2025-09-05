"""
艺术品数据导入模块
"""

import csv
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
from uuid import uuid4

from database.config import get_db_manager
from .models import Artwork, ArtworkBatch, BatchProcessingStatus
from .tag_extractor import TagExtractor
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ArtworkDataImporter:
    """艺术品数据导入器"""
    
    def __init__(self):
        self.db_manager = None
        self.tag_extractor = TagExtractor()
        self.embedding_service = EmbeddingService()
        self.batch_size = 100
        
    async def initialize(self):
        """初始化数据库连接"""
        self.db_manager = get_db_manager()
        await self.embedding_service.initialize()
        
    async def import_from_csv(self, csv_file_path: str, batch_size: int = 100) -> BatchProcessingStatus:
        """从CSV文件导入艺术品数据"""
        try:
            logger.info(f"开始导入CSV文件: {csv_file_path}")
            
            # 读取CSV文件
            df = pd.read_csv(csv_file_path, encoding='utf-8')
            total_rows = len(df)
            
            logger.info(f"CSV文件包含 {total_rows} 行数据")
            
            # 创建批处理状态
            task_id = str(uuid4())
            status = BatchProcessingStatus(
                task_id=task_id,
                status="running",
                progress=0.0,
                total_items=total_rows,
                processed_items=0
            )
            
            # 分批处理
            processed_count = 0
            failed_count = 0
            
            for i in range(0, total_rows, batch_size):
                batch_df = df.iloc[i:i + batch_size]
                
                try:
                    # 转换为Artwork对象
                    artworks = await self._convert_df_to_artworks(batch_df)
                    
                    # 批量插入数据库
                    success_count = await self._batch_insert_artworks(artworks)
                    processed_count += success_count
                    
                    # 更新进度
                    status.processed_items = processed_count
                    status.progress = processed_count / total_rows
                    
                    logger.info(f"已处理 {processed_count}/{total_rows} 条记录")
                    
                except Exception as e:
                    logger.error(f"批次处理失败: {e}")
                    failed_count += len(batch_df)
                    continue
            
            # 完成状态
            status.status = "completed"
            status.progress = 1.0
            
            logger.info(f"导入完成: 成功 {processed_count} 条，失败 {failed_count} 条")
            
            return status
            
        except Exception as e:
            logger.error(f"CSV导入失败: {e}")
            status.status = "failed"
            status.error_message = str(e)
            return status
    
    async def _convert_df_to_artworks(self, df: pd.DataFrame) -> List[Artwork]:
        """将DataFrame转换为Artwork对象列表"""
        artworks = []
        
        for _, row in df.iterrows():
            try:
                # 基础字段映射
                artwork_data = {
                    'object_id': str(row.get('Object ID', '')),
                    'title': str(row.get('Title', '')),
                    'object_name': str(row.get('Object Name', '')) if pd.notna(row.get('Object Name')) else None,
                    'department': str(row.get('Department', '')) if pd.notna(row.get('Department')) else None,
                    'culture': str(row.get('Culture', '')) if pd.notna(row.get('Culture')) else None,
                    'period': str(row.get('Period', '')) if pd.notna(row.get('Period')) else None,
                    'artist_display_name': str(row.get('Artist Display Name', '')) if pd.notna(row.get('Artist Display Name')) else None,
                    'medium': str(row.get('Medium', '')) if pd.notna(row.get('Medium')) else None,
                    'dimensions': str(row.get('Dimensions', '')) if pd.notna(row.get('Dimensions')) else None,
                    'classification': str(row.get('Classification', '')) if pd.notna(row.get('Classification')) else None,
                    'object_date': str(row.get('Object Date', '')) if pd.notna(row.get('Object Date')) else None,
                    'general_text_description': str(row.get('General_Text_Description', '')) if pd.notna(row.get('General_Text_Description')) else None,
                    'url': str(row.get('url', '')) if pd.notna(row.get('url')) else None,
                }
                
                # 提取标签
                tags = await self._extract_tags_from_artwork(artwork_data)
                artwork_data.update(tags)
                
                # 计算初始评分
                scores = self._calculate_initial_scores(artwork_data)
                artwork_data.update(scores)
                
                artwork = Artwork(**artwork_data)
                artworks.append(artwork)
                
            except Exception as e:
                logger.error(f"转换艺术品数据失败: {e}, 行数据: {row.to_dict()}")
                continue
        
        return artworks
    
    async def _extract_tags_from_artwork(self, artwork_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """从艺术品数据中提取标签"""
        try:
            # 组合文本用于标签提取
            text_content = []
            
            if artwork_data.get('title'):
                text_content.append(artwork_data['title'])
            if artwork_data.get('general_text_description'):
                text_content.append(artwork_data['general_text_description'])
            if artwork_data.get('medium'):
                text_content.append(artwork_data['medium'])
            if artwork_data.get('culture'):
                text_content.append(artwork_data['culture'])
            if artwork_data.get('period'):
                text_content.append(artwork_data['period'])
            
            combined_text = ' '.join(text_content)
            
            # 提取各类标签
            tags = await self.tag_extractor.extract_tags(combined_text)
            
            return {
                'color_tags': tags.get('colors', []),
                'style_tags': tags.get('styles', []),
                'theme_tags': tags.get('themes', []),
                'emotion_tags': tags.get('emotions', [])
            }
            
        except Exception as e:
            logger.error(f"标签提取失败: {e}")
            return {
                'color_tags': [],
                'style_tags': [],
                'theme_tags': [],
                'emotion_tags': []
            }
    
    def _calculate_initial_scores(self, artwork_data: Dict[str, Any]) -> Dict[str, float]:
        """计算艺术品的初始评分"""
        try:
            popularity_score = 0.0
            quality_score = 0.0
            
            # 基于艺术家知名度的评分
            artist = artwork_data.get('artist_display_name', '').lower()
            if artist and artist != 'unknown' and artist != 'unidentified artist':
                popularity_score += 2.0
                quality_score += 1.0
            
            # 基于文化和时期的评分
            culture = artwork_data.get('culture', '').lower()
            period = artwork_data.get('period', '').lower()
            
            famous_cultures = ['italian', 'french', 'dutch', 'chinese', 'japanese', 'greek', 'roman']
            if any(fc in culture for fc in famous_cultures):
                popularity_score += 1.0
                quality_score += 0.5
            
            # 基于描述长度的质量评分
            description = artwork_data.get('general_text_description', '')
            if description and len(description) > 100:
                quality_score += 1.0
            
            # 基于标题长度的评分
            title = artwork_data.get('title', '')
            if title and len(title) > 10:
                quality_score += 0.5
            
            # 确保评分在合理范围内
            popularity_score = min(popularity_score, 5.0)
            quality_score = min(quality_score, 5.0)
            
            return {
                'popularity_score': popularity_score,
                'quality_score': quality_score
            }
            
        except Exception as e:
            logger.error(f"评分计算失败: {e}")
            return {
                'popularity_score': 0.0,
                'quality_score': 0.0
            }
    
    async def _batch_insert_artworks(self, artworks: List[Artwork]) -> int:
        """批量插入艺术品到数据库"""
        if not artworks:
            return 0
        
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                success_count = 0
                
                for artwork in artworks:
                    try:
                        # 检查是否已存在
                        existing = await conn.fetchrow(
                            "SELECT id FROM artworks WHERE object_id = $1",
                            artwork.object_id
                        )
                        
                        if existing:
                            logger.debug(f"艺术品已存在，跳过: {artwork.object_id}")
                            continue
                        
                        # 插入艺术品
                        artwork_id = await conn.fetchval("""
                            INSERT INTO artworks (
                                object_id, title, object_name, department, culture, period,
                                artist_display_name, medium, dimensions, classification,
                                object_date, general_text_description, url,
                                color_tags, style_tags, theme_tags, emotion_tags,
                                popularity_score, quality_score
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                                $11, $12, $13, $14, $15, $16, $17, $18, $19
                            ) RETURNING id
                        """,
                            artwork.object_id, artwork.title, artwork.object_name,
                            artwork.department, artwork.culture, artwork.period,
                            artwork.artist_display_name, artwork.medium, artwork.dimensions,
                            artwork.classification, artwork.object_date,
                            artwork.general_text_description, artwork.url,
                            artwork.color_tags, artwork.style_tags, artwork.theme_tags,
                            artwork.emotion_tags, artwork.popularity_score, artwork.quality_score
                        )
                        
                        # 生成并存储嵌入向量
                        await self._generate_and_store_embeddings(conn, artwork_id, artwork)
                        
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"插入艺术品失败: {e}, artwork: {artwork.object_id}")
                        continue
                
                return success_count
                
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            return 0
    
    async def _generate_and_store_embeddings(self, conn, artwork_id: str, artwork: Artwork):
        """生成并存储艺术品的嵌入向量"""
        try:
            # 生成标题嵌入
            if artwork.title:
                title_embedding = await self.embedding_service.encode_text(artwork.title)
                await self._store_embedding(conn, artwork_id, 'title', title_embedding)
            
            # 生成描述嵌入
            if artwork.general_text_description:
                desc_embedding = await self.embedding_service.encode_text(artwork.general_text_description)
                await self._store_embedding(conn, artwork_id, 'description', desc_embedding)
            
            # 生成组合嵌入
            combined_text = f"{artwork.title or ''} {artwork.general_text_description or ''}"
            if combined_text.strip():
                combined_embedding = await self.embedding_service.encode_text(combined_text)
                await self._store_embedding(conn, artwork_id, 'combined', combined_embedding)
                
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
    
    async def _store_embedding(self, conn, artwork_id: str, embedding_type: str, embedding_vector: List[float]):
        """存储嵌入向量到数据库"""
        try:
            await conn.execute("""
                INSERT INTO artwork_embeddings (artwork_id, embedding_type, embedding_vector, model_name)
                VALUES ($1, $2, $3, $4)
            """, artwork_id, embedding_type, json.dumps(embedding_vector), self.embedding_service.model_name)
            
        except Exception as e:
            logger.error(f"存储嵌入向量失败: {e}")
    
    async def get_import_stats(self) -> Dict[str, Any]:
        """获取导入统计信息"""
        try:
            conn_ctx = await self.db_manager.get_connection()
            async with conn_ctx as conn:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_artworks,
                        COUNT(DISTINCT artist_display_name) as total_artists,
                        COUNT(DISTINCT culture) as total_cultures,
                        COUNT(DISTINCT department) as total_departments,
                        AVG(popularity_score) as avg_popularity,
                        AVG(quality_score) as avg_quality
                    FROM artworks
                    WHERE artist_display_name IS NOT NULL
                """)
                
                return dict(stats) if stats else {}
                
        except Exception as e:
            logger.error(f"获取导入统计失败: {e}")
            return {}


# 便捷函数
async def import_artworks_from_csv(csv_file_path: str, batch_size: int = 100) -> BatchProcessingStatus:
    """便捷函数：从CSV导入艺术品数据"""
    importer = ArtworkDataImporter()
    await importer.initialize()
    return await importer.import_from_csv(csv_file_path, batch_size)

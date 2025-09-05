"""
艺术品标签提取器
"""

import re
import logging
from typing import Dict, List, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class TagExtractor:
    """艺术品标签提取器"""
    
    def __init__(self):
        self.color_keywords = self._load_color_keywords()
        self.style_keywords = self._load_style_keywords()
        self.theme_keywords = self._load_theme_keywords()
        self.emotion_keywords = self._load_emotion_keywords()
        
    def _load_color_keywords(self) -> Dict[str, List[str]]:
        """加载颜色关键词"""
        return {
            'red': ['red', 'crimson', 'scarlet', 'ruby', 'cherry', 'rose', 'pink', 'coral'],
            'blue': ['blue', 'azure', 'navy', 'cobalt', 'sapphire', 'turquoise', 'cyan', 'indigo'],
            'green': ['green', 'emerald', 'jade', 'olive', 'lime', 'mint', 'forest', 'sage'],
            'yellow': ['yellow', 'gold', 'golden', 'amber', 'lemon', 'cream', 'ivory', 'beige'],
            'orange': ['orange', 'tangerine', 'peach', 'apricot', 'copper', 'bronze'],
            'purple': ['purple', 'violet', 'lavender', 'plum', 'magenta', 'lilac', 'mauve'],
            'brown': ['brown', 'tan', 'chocolate', 'coffee', 'mahogany', 'chestnut', 'sienna'],
            'black': ['black', 'ebony', 'charcoal', 'jet', 'onyx', 'coal'],
            'white': ['white', 'pearl', 'snow', 'ivory', 'cream', 'alabaster'],
            'gray': ['gray', 'grey', 'silver', 'ash', 'slate', 'pewter'],
            'multicolor': ['multicolor', 'colorful', 'rainbow', 'varied', 'diverse']
        }
    
    def _load_style_keywords(self) -> Dict[str, List[str]]:
        """加载艺术风格关键词"""
        return {
            'impressionism': ['impressionist', 'impressionism', 'monet', 'renoir', 'degas'],
            'realism': ['realist', 'realistic', 'realism', 'naturalistic', 'lifelike'],
            'abstract': ['abstract', 'abstraction', 'non-representational', 'non-figurative'],
            'expressionism': ['expressionist', 'expressionism', 'emotional', 'expressive'],
            'cubism': ['cubist', 'cubism', 'geometric', 'fragmented', 'picasso'],
            'surrealism': ['surrealist', 'surrealism', 'dreamlike', 'fantastical', 'dali'],
            'baroque': ['baroque', 'ornate', 'dramatic', 'elaborate', 'decorative'],
            'renaissance': ['renaissance', 'classical', 'humanistic', 'perspective'],
            'modern': ['modern', 'contemporary', 'avant-garde', 'innovative'],
            'traditional': ['traditional', 'classical', 'conventional', 'historic'],
            'minimalist': ['minimalist', 'minimal', 'simple', 'clean', 'sparse'],
            'romantic': ['romantic', 'romanticism', 'emotional', 'passionate'],
            'gothic': ['gothic', 'medieval', 'dark', 'mysterious'],
            'pop_art': ['pop art', 'popular', 'commercial', 'warhol'],
            'folk': ['folk', 'traditional', 'cultural', 'ethnic', 'indigenous']
        }
    
    def _load_theme_keywords(self) -> Dict[str, List[str]]:
        """加载主题关键词"""
        return {
            'landscape': ['landscape', 'scenery', 'nature', 'countryside', 'mountain', 'forest', 'river'],
            'portrait': ['portrait', 'figure', 'person', 'face', 'human', 'people'],
            'still_life': ['still life', 'objects', 'flowers', 'fruit', 'vase', 'table'],
            'religious': ['religious', 'sacred', 'holy', 'divine', 'spiritual', 'church', 'temple'],
            'mythology': ['mythological', 'myth', 'legend', 'gods', 'goddess', 'hero'],
            'historical': ['historical', 'history', 'battle', 'war', 'event', 'commemoration'],
            'animals': ['animal', 'bird', 'horse', 'dog', 'cat', 'wildlife', 'creature'],
            'architecture': ['building', 'architecture', 'structure', 'palace', 'house', 'bridge'],
            'marine': ['sea', 'ocean', 'water', 'ship', 'boat', 'wave', 'coastal'],
            'urban': ['city', 'urban', 'street', 'building', 'metropolitan', 'town'],
            'rural': ['rural', 'countryside', 'farm', 'village', 'pastoral', 'agricultural'],
            'abstract_theme': ['abstract', 'geometric', 'pattern', 'form', 'composition'],
            'family': ['family', 'mother', 'father', 'child', 'domestic', 'home'],
            'work': ['work', 'labor', 'occupation', 'craft', 'industry', 'profession']
        }
    
    def _load_emotion_keywords(self) -> Dict[str, List[str]]:
        """加载情感关键词"""
        return {
            'peaceful': ['peaceful', 'calm', 'serene', 'tranquil', 'quiet', 'restful'],
            'joyful': ['joyful', 'happy', 'cheerful', 'bright', 'celebratory', 'festive'],
            'melancholic': ['melancholic', 'sad', 'sorrowful', 'mournful', 'tragic', 'somber'],
            'dramatic': ['dramatic', 'intense', 'powerful', 'striking', 'bold', 'dynamic'],
            'mysterious': ['mysterious', 'enigmatic', 'secretive', 'hidden', 'obscure'],
            'romantic': ['romantic', 'loving', 'tender', 'intimate', 'passionate'],
            'nostalgic': ['nostalgic', 'reminiscent', 'wistful', 'sentimental', 'memory'],
            'energetic': ['energetic', 'vibrant', 'lively', 'active', 'dynamic', 'spirited'],
            'contemplative': ['contemplative', 'thoughtful', 'reflective', 'meditative', 'introspective'],
            'majestic': ['majestic', 'grand', 'noble', 'dignified', 'impressive', 'magnificent']
        }
    
    async def extract_tags(self, text: str) -> Dict[str, List[str]]:
        """从文本中提取标签"""
        if not text:
            return {
                'colors': [],
                'styles': [],
                'themes': [],
                'emotions': []
            }
        
        text_lower = text.lower()
        
        # 提取各类标签
        colors = self._extract_category_tags(text_lower, self.color_keywords)
        styles = self._extract_category_tags(text_lower, self.style_keywords)
        themes = self._extract_category_tags(text_lower, self.theme_keywords)
        emotions = self._extract_category_tags(text_lower, self.emotion_keywords)
        
        return {
            'colors': list(colors),
            'styles': list(styles),
            'themes': list(themes),
            'emotions': list(emotions)
        }
    
    def _extract_category_tags(self, text: str, category_keywords: Dict[str, List[str]]) -> Set[str]:
        """从文本中提取特定类别的标签"""
        found_tags = set()
        
        for tag, keywords in category_keywords.items():
            for keyword in keywords:
                # 使用词边界匹配，避免部分匹配
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, text):
                    found_tags.add(tag)
                    break  # 找到一个关键词就足够了
        
        return found_tags
    
    def extract_artist_style(self, artist_name: str) -> List[str]:
        """根据艺术家名字推断风格"""
        if not artist_name or artist_name.lower() in ['unknown', 'unidentified artist']:
            return []
        
        artist_lower = artist_name.lower()
        styles = []
        
        # 著名艺术家风格映射
        artist_style_mapping = {
            'monet': ['impressionism'],
            'renoir': ['impressionism'],
            'degas': ['impressionism'],
            'picasso': ['cubism', 'modern'],
            'van gogh': ['post-impressionism', 'expressionism'],
            'dali': ['surrealism'],
            'warhol': ['pop_art', 'modern'],
            'leonardo': ['renaissance'],
            'michelangelo': ['renaissance'],
            'raphael': ['renaissance'],
            'rembrandt': ['baroque'],
            'vermeer': ['baroque'],
            'cezanne': ['post-impressionism'],
            'matisse': ['fauvism', 'modern'],
            'kandinsky': ['abstract', 'expressionism'],
            'pollock': ['abstract', 'modern'],
            'rothko': ['abstract', 'modern']
        }
        
        for artist_key, artist_styles in artist_style_mapping.items():
            if artist_key in artist_lower:
                styles.extend(artist_styles)
        
        return styles
    
    def extract_period_style(self, period: str) -> List[str]:
        """根据时期推断风格"""
        if not period:
            return []
        
        period_lower = period.lower()
        styles = []
        
        # 时期风格映射
        period_style_mapping = {
            'renaissance': ['renaissance', 'classical'],
            'baroque': ['baroque'],
            'rococo': ['rococo'],
            'neoclassical': ['neoclassical', 'classical'],
            'romantic': ['romantic'],
            'impressionist': ['impressionism'],
            'modern': ['modern'],
            'contemporary': ['contemporary', 'modern'],
            'medieval': ['gothic', 'medieval'],
            'ancient': ['classical', 'traditional'],
            'ming': ['traditional', 'chinese'],
            'qing': ['traditional', 'chinese'],
            'edo': ['traditional', 'japanese'],
            'meiji': ['traditional', 'japanese']
        }
        
        for period_key, period_styles in period_style_mapping.items():
            if period_key in period_lower:
                styles.extend(period_styles)
        
        return styles
    
    def extract_culture_themes(self, culture: str) -> List[str]:
        """根据文化背景推断主题"""
        if not culture:
            return []
        
        culture_lower = culture.lower()
        themes = []
        
        # 文化主题映射
        culture_theme_mapping = {
            'chinese': ['traditional', 'landscape', 'calligraphy'],
            'japanese': ['traditional', 'nature', 'zen'],
            'italian': ['renaissance', 'religious', 'classical'],
            'french': ['romantic', 'impressionist', 'elegant'],
            'dutch': ['realistic', 'domestic', 'landscape'],
            'german': ['expressionist', 'romantic', 'gothic'],
            'american': ['modern', 'pop_art', 'contemporary'],
            'greek': ['classical', 'mythology', 'ancient'],
            'roman': ['classical', 'historical', 'ancient'],
            'egyptian': ['ancient', 'religious', 'symbolic'],
            'indian': ['religious', 'spiritual', 'traditional'],
            'islamic': ['geometric', 'decorative', 'religious']
        }
        
        for culture_key, culture_themes in culture_theme_mapping.items():
            if culture_key in culture_lower:
                themes.extend(culture_themes)
        
        return themes
    
    def enhance_tags_with_metadata(self, base_tags: Dict[str, List[str]], 
                                 artist: str = None, period: str = None, 
                                 culture: str = None) -> Dict[str, List[str]]:
        """使用元数据增强标签"""
        enhanced_tags = {
            'colors': list(base_tags.get('colors', [])),
            'styles': list(base_tags.get('styles', [])),
            'themes': list(base_tags.get('themes', [])),
            'emotions': list(base_tags.get('emotions', []))
        }
        
        # 添加艺术家风格
        if artist:
            artist_styles = self.extract_artist_style(artist)
            enhanced_tags['styles'].extend(artist_styles)
        
        # 添加时期风格
        if period:
            period_styles = self.extract_period_style(period)
            enhanced_tags['styles'].extend(period_styles)
        
        # 添加文化主题
        if culture:
            culture_themes = self.extract_culture_themes(culture)
            enhanced_tags['themes'].extend(culture_themes)
        
        # 去重
        for category in enhanced_tags:
            enhanced_tags[category] = list(set(enhanced_tags[category]))
        
        return enhanced_tags

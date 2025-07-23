import re
from typing import List

class SecurityUtils:
    """安全工具类，用于检测恶意输入和垃圾信息"""
    
    # 恶意关键词列表
    MALICIOUS_KEYWORDS = [
        "hack", "attack", "exploit", "injection", "script", "malware",
        "virus", "trojan", "phishing", "spam", "bot", "crawler",
        "sql injection", "xss", "csrf", "ddos", "破解", "攻击",
        "注入", "恶意", "病毒", "木马", "钓鱼", "垃圾", "机器人"
    ]
    
    # 垃圾信息模式
    SPAM_PATTERNS = [
        r"(.)\1{10,}",  # 重复字符超过10次
        r"[A-Z]{20,}",  # 连续大写字母超过20个
        r"\d{15,}",     # 连续数字超过15个
        r"[!@#$%^&*()]{5,}",  # 连续特殊字符超过5个
    ]
    
    @classmethod
    def contains_malicious_keywords(cls, text: str) -> bool:
        """检查文本是否包含恶意关键词"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in cls.MALICIOUS_KEYWORDS)
    
    @classmethod
    def is_spam_or_irrelevant(cls, text: str) -> bool:
        """检查文本是否为垃圾信息或无关内容"""
        # 检查垃圾信息模式
        for pattern in cls.SPAM_PATTERNS:
            if re.search(pattern, text):
                return True
        
        # 检查文本长度
        if len(text.strip()) < 2:
            return True
        
        # 检查是否只包含特殊字符
        if re.match(r'^[^a-zA-Z0-9\u4e00-\u9fff\s]+$', text):
            return True
        
        return False
    
    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """清理输入文本"""
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 限制长度
        if len(text) > 1000:
            text = text[:1000]
        
        return text

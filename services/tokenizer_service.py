"""
中文分词服务
使用 jieba 进行中文分词
"""
import jieba
import re
from typing import List
import logging

logger = logging.getLogger(__name__)


class TokenizerService:
    """中文分词服务"""

    # 店铺类型关键词（需要过滤）
    SHOP_TYPE_KEYWORDS = [
        "旗舰店", "专营店", "专卖店", "体验店", "概念店",
        "官方店", "旗舰店", "总店", "分店", "连锁店",
        "加盟店", "直营店", "授权店", "经销店", "代理店"
    ]

    # 常见停用词
    STOPWORDS = {"的", "了", "在", "是", "我", "有", "和", "与", "等", "及", "为"}

    def __init__(self):
        # 加载自定义词典（可选）
        # jieba.load_userdict("custom_dict.txt")
        pass

    def clean_shop_name(self, text: str) -> str:
        """
        清理店铺名称，去除店铺类型关键词

        Args:
            text: 原始店铺名称

        Returns:
            清理后的店铺名称
        """
        cleaned = text
        for keyword in self.SHOP_TYPE_KEYWORDS:
            cleaned = cleaned.replace(keyword, "")
        
        # 去除多余空格
        cleaned = re.sub(r'\s+', '', cleaned)
        
        return cleaned.strip()

    def tokenize(self, text: str) -> List[str]:
        """
        对文本进行分词

        Args:
            text: 输入文本

        Returns:
            分词后的列表
        """
        # 使用精确模式分词
        words = list(jieba.cut(text, cut_all=False))
        # 过滤空白字符
        return [w.strip() for w in words if w.strip()]

    def tokenize_for_search(self, text: str) -> List[str]:
        """
        对搜索关键词进行分词，返回适合搜索的关键词列表

        Args:
            text: 输入文本（店铺名称）

        Returns:
            去重后的关键词列表
        """
        # 先清理店铺名称
        cleaned_text = self.clean_shop_name(text)
        
        # 分词
        words = self.tokenize(cleaned_text)
        
        # 过滤停用词和店铺类型关键词
        all_stopwords = self.STOPWORDS.union(set(self.SHOP_TYPE_KEYWORDS))
        
        # 过滤：非停用词、非店铺类型、长度>1
        keywords = [
            w for w in words 
            if w not in all_stopwords 
            and len(w) > 1
            and not w.isdigit()  # 过滤纯数字
        ]
        
        return list(set(keywords))


# 全局实例
tokenizer_service = TokenizerService()
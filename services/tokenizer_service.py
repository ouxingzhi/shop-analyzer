"""
中文分词服务
使用 jieba 进行中文分词
"""
import jieba
from typing import List
import logging

logger = logging.getLogger(__name__)


class TokenizerService:
    """中文分词服务"""

    def __init__(self):
        # 加载自定义词典（可选）
        # jieba.load_userdict("custom_dict.txt")
        pass

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
            text: 输入文本

        Returns:
            去重后的关键词列表
        """
        words = self.tokenize(text)
        # 过滤常见停用词
        stopwords = {"的", "了", "在", "是", "我", "有", "和", "与", "等", "及", "等"}
        return list(set(w for w in words if w not in stopwords and len(w) > 1))


# 全局实例
tokenizer_service = TokenizerService()

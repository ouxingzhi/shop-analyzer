"""
店铺名称处理服务
过滤店铺类型关键词
"""
import re
from typing import List
import logging

logger = logging.getLogger(__name__)


class TokenizerService:
    """店铺名称处理服务"""

    # 店铺类型关键词（需要过滤）
    SHOP_TYPE_KEYWORDS = [
        "旗舰店", "专营店", "专卖店", "体验店", "概念店",
        "官方店", "总店", "分店", "连锁店",
        "加盟店", "直营店", "授权店", "经销店", "代理店"
    ]

    def __init__(self):
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

    def tokenize_for_search(self, text: str) -> List[str]:
        """
        获取搜索关键词（直接返回清理后的名称）

        Args:
            text: 输入文本（店铺名称）

        Returns:
            搜索关键词列表
        """
        cleaned = self.clean_shop_name(text)
        return [cleaned] if cleaned else []


# 全局实例
tokenizer_service = TokenizerService()
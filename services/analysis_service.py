"""
AI 分析服务
使用阿里通义千问进行关联性分析
"""
import dashscope
from typing import List, Dict, Any
import logging

from config import config
from services.search_service import SearchResult

logger = logging.getLogger(__name__)


class AnalysisService:
    """AI 分析服务"""

    def __init__(self):
        dashscope.api_key = config.dashscope.api_key
        self.model = config.dashscope.model
        self.max_tokens = config.dashscope.max_tokens

    def analyze_shops(self, search_results: List[SearchResult]) -> str:
        """
        对店铺搜索结果进行关联性分析

        Args:
            search_results: 搜索结果列表

        Returns:
            分析报告
        """
        # 构建分析提示词
        prompt = self._build_analysis_prompt(search_results)

        try:
            response = dashscope.Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=0.7
            )

            if response.status_code == 200:
                return response.output.text
            else:
                logger.error(f"AI 分析失败：{response.code} - {response.message}")
                return f"分析失败：{response.message}"

        except Exception as e:
            logger.error(f"AI 分析异常：{e}")
            return f"分析出现异常：{str(e)}"

    def _build_analysis_prompt(self, search_results: List[SearchResult]) -> str:
        """构建分析提示词"""
        shop_info = []
        for i, result in enumerate(search_results, 1):
            info = f"""
{i}. 店铺名称：{result.shop_name}
   关键词：{", ".join(result.keywords)}
   搜索信息：{result.info}
"""
            shop_info.append(info)

        shops_text = "\n".join(shop_info)

        prompt = f"""你是一名专业的商业分析专家。请对以下店铺信息进行关联性分析，并生成详细报告。

【店铺信息】
{shops_text}

【分析要求】
1. 分析各店铺之间的关联性（如：是否属于同一行业、是否存在竞争或合作关系）
2. 识别店铺的业务特点和定位
3. 分析关键词与店铺业务的匹配程度
4. 提供综合性的商业洞察和建议

【输出格式】
请以结构化报告形式输出，包含以下章节：
- 总体概述
- 店铺 individually 分析
- 关联性分析
- 商业洞察
- 建议

请用中文回答。
"""
        return prompt

    def generate_summary(self, shops: List[str]) -> str:
        """
        生成店铺列表的简要总结

        Args:
            shops: 店铺名称列表

        Returns:
            总结文本
        """
        shops_text = "\n".join(f"- {shop}" for shop in shops)

        prompt = f"""请对以下店铺名称列表进行简要分析，概述这些店铺可能涉及的业务领域：

{shops_text}

请用 100-200 字进行概括。
"""

        try:
            response = dashscope.Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=500,
                temperature=0.5
            )

            if response.status_code == 200:
                return response.output.text
            else:
                return f"无法生成摘要：{response.message}"

        except Exception as e:
            logger.error(f"生成摘要异常：{e}")
            return f"生成摘要出现异常：{str(e)}"


# 全局实例
analysis_service = AnalysisService()

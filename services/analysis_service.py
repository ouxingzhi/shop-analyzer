"""
AI 分析服务
使用阿里云百炼 GLM-5 模型进行关联性分析
OpenAI 兼容 API
"""
import aiohttp
import asyncio
from typing import List, Dict, Any
import logging
import json

from config import config
from services.search_service import SearchResult

logger = logging.getLogger(__name__)


class AnalysisService:
    """AI 分析服务 - 百炼 GLM-5"""

    def __init__(self):
        self.base_url = "https://coding.dashscope.aliyuncs.com/v1"
        self.api_key = config.ai.api_key
        self.model = config.ai.model
        self.max_tokens = config.ai.max_tokens
        self._session: aiohttp.ClientSession = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        return self._session

    async def analyze_shops(self, search_results: List[SearchResult]) -> str:
        """
        对店铺搜索结果进行关联性分析

        Args:
            search_results: 搜索结果列表

        Returns:
            分析报告
        """
        prompt = self._build_analysis_prompt(search_results)
        return await self._call_model(prompt, self.max_tokens, 0.7)

    async def _call_model(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """调用 AI 模型"""
        try:
            session = await self._get_session()

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            async with session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    error_text = await response.text()
                    logger.error(f"AI 分析失败：{response.status} - {error_text[:200]}")
                    return f"分析失败：HTTP {response.status}"

        except Exception as e:
            logger.error(f"AI 分析异常：{e}")
            return f"分析出现异常：{str(e)}"

    def _build_analysis_prompt(self, search_results: List[SearchResult]) -> str:
        """构建分析提示词"""
        shop_info = []
        for i, result in enumerate(search_results, 1):
            company_detail = ""
            if result.company_list:
                for j, company in enumerate(result.company_list[:2], 1):
                    company_detail += f"\n      公司{j}: {company['name']} | 法人: {company['legalPerson']} | 状态: {company['regStatus']}"

            info = f"""
{i}. 店铺名称：{result.shop_name}
   搜索名称：{result.search_name}
   搜索结果：{company_detail if company_detail else "未找到相关企业"}
"""
            shop_info.append(info)

        shops_text = "\n".join(shop_info)

        prompt = f"""你是一名专业的商业分析专家。请对以下店铺/企业信息进行关联性分析，并生成详细报告。

【店铺信息】
{shops_text}

【分析要求】
1. 分析各店铺之间的关联性（如：是否属于同一行业、是否存在竞争或合作关系、是否属于同一法人）
2. 识别店铺的业务特点和行业定位
3. 分析搜索名称与实际企业的匹配程度
4. 提供综合性的商业洞察和建议

【输出格式】
请以结构化报告形式输出，包含以下章节：

## 总体概述
简要概述这些店铺的整体特征

## 各店铺分析
逐个分析每个店铺的工商信息（公司名、法人、注册资本、成立时间等）

## 关联性分析
分析店铺之间可能存在的关联（行业关联、法人关联、地域关联等）

## 商业洞察
基于分析得出的商业结论

## 建议
针对发现的情况提出建议

请用中文回答，保持专业和客观。
"""
        return prompt

    async def generate_summary(self, shops: List[str]) -> str:
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

请用 100-200 字进行概括，指出主要行业和特点。"""

        return await self._call_model(prompt, 500, 0.5)

    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()


# 全局实例
analysis_service = AnalysisService()
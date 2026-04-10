"""
AI 分析服务
使用阿里云百炼 GLM-5 模型进行关联性分析
OpenAI 兼容 API
"""
import aiohttp
import asyncio
from typing import List, Dict, Any, Tuple
import logging
import json
import re

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

    async def analyze_shops(self, search_results: List[SearchResult]) -> Tuple[str, Dict[str, str]]:
        """
        对店铺搜索结果进行关联性分析

        Args:
            search_results: 搜索结果列表

        Returns:
            (分析报告, 匹配的公司字典 {店铺名: 匹配的公司名})
        """
        prompt = self._build_analysis_prompt(search_results)
        response = await self._call_model(prompt, self.max_tokens, 0.7)
        
        # 提取匹配结果
        matched_companies = self._extract_matched_companies(response, search_results)
        
        return response, matched_companies

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

    def _extract_matched_companies(self, response: str, search_results: List[SearchResult]) -> Dict[str, str]:
        """从 AI 响应中提取匹配的公司"""
        matched = {}
        
        # 尝试从JSON块中提取
        json_match = re.search(r'\[MATCHED_COMPANY\]\s*(\{.*?\})\s*\[/MATCHED_COMPANY\]', response, re.DOTALL)
        if json_match:
            try:
                matched = json.loads(json_match.group(1))
                return matched
            except:
                pass
        
        # 如果没有找到JSON，尝试从文本中提取
        for result in search_results:
            shop_name = result.shop_name
            # 查找该店铺的匹配公司
            pattern = rf'{shop_name}.*?匹配[：:]\s*([^\n]+)'
            match = re.search(pattern, response)
            if match:
                matched[shop_name] = match.group(1).strip()
        
        return matched

    def _build_analysis_prompt(self, search_results: List[SearchResult]) -> str:
        """构建分析提示词"""
        shop_info = []
        company_names = {}
        
        for i, result in enumerate(search_results, 1):
            company_names[result.shop_name] = [c.get('name', '') for c in result.company_list[:5]]
            
            company_detail = ""
            if result.company_list:
                for j, company in enumerate(result.company_list[:3], 1):
                    company_detail += f"\n      {j}. {company.get('name', '未知')} | 法人: {company.get('legalPerson', '未知')} | 状态: {company.get('regStatus', '未知')} | 电话: {company.get('phone', '无')} | 邮箱: {company.get('email', '无')}"

            info = f"""
{i}. 店铺名称：{result.shop_name}
   搜索名称：{result.search_name}
   搜索到的公司：{company_detail if company_detail else "未找到相关企业"}
"""
            shop_info.append(info)

        shops_text = "\n".join(shop_info)

        prompt = f"""你是一名专业的商业分析专家。请对以下店铺信息进行分析，判断每个店铺最匹配的公司。

【店铺信息】
{shops_text}

【分析任务】
1. 对于每个店铺，从搜索到的公司列表中选择最匹配的公司（名称最接近、业务最相关）
2. 如果没有找到匹配的公司，标注"未匹配"
3. 分析各店铺之间的关联性（同一行业、同一法人、竞争关系等）
4. 提供商业洞察和建议

【输出格式要求】
请按以下格式输出：

## 匹配结果
请为每个店铺标注最匹配的公司名，格式如下：
- 店铺A：匹配公司XXX
- 店铺B：匹配公司YYY

## 总体概述
简要概述这些店铺的整体特征

## 各店铺详细分析
逐个分析每个店铺的情况

## 关联性分析
分析店铺之间可能存在的关联

## 商业洞察和建议
基于分析得出的结论和建议

请用中文回答，保持专业和客观。
"""
        return prompt

    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()


# 全局实例
analysis_service = AnalysisService()
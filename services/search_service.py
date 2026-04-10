"""
搜索服务
调用天眼查/企查查 API 搜索企业信息
"""
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from config import config

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    shop_name: str
    keywords: List[str]
    info: str
    company_list: List[Dict[str, Any]]  # 搜索到的公司列表
    raw_data: Dict[str, Any]


class SearchService:
    """搜索服务 - 支持天眼查和企查查"""

    def __init__(self):
        self.base_url = config.search.base_url  # e.g. http://localhost:3000
        self.api_type = config.search.api_type  # tianyancha or qichacha
        self.timeout = config.search.timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def search_shop(self, shop_name: str, keywords: List[str]) -> Optional[SearchResult]:
        """
        搜索企业信息（调用天眼查或企查查 API）

        Args:
            shop_name: 店铺/企业名称
            keywords: 分词后的关键词列表

        Returns:
            搜索结果
        """
        try:
            session = await self._get_session()

            # 根据配置选择 API
            if self.api_type == "qichacha":
                url = f"{self.base_url}/api/qichacha/search"
                params = {"keyword": shop_name, "pageIndex": 1}
                async with session.get(url, params=params) as response:
                    return await self._handle_response(response, shop_name, keywords)
            else:  # 默认天眼查
                url = f"{self.base_url}/api/tianyancha/search"
                params = {"keyword": shop_name, "pageNum": 1, "pageSize": 5}
                async with session.get(url, params=params) as response:
                    return await self._handle_response(response, shop_name, keywords)

        except aiohttp.ClientError as e:
            logger.error(f"搜索请求失败：{e}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"搜索请求超时：{shop_name}")
            return None

    async def _handle_response(self, response, shop_name: str, keywords: List[str]) -> Optional[SearchResult]:
        """处理 API 响应"""
        if response.status == 200:
            data = await response.json()
            company_list = self._extract_company_list(data)
            info = self._format_company_info(company_list)
            return SearchResult(
                shop_name=shop_name,
                keywords=keywords,
                info=info,
                company_list=company_list,
                raw_data=data
            )
        else:
            logger.warning(f"搜索 API 返回错误状态：{response.status}")
            return None

    def _extract_company_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从搜索响应中提取公司列表"""
        companies = []
        
        # 天眼查响应格式
        if "result" in data and "resultList" in data.get("result", {}):
            for item in data["result"]["resultList"]:
                companies.append({
                    "name": item.get("name", ""),
                    "id": item.get("id", ""),
                    "legalPerson": item.get("legalPersonName", ""),
                    "regStatus": item.get("regStatus", ""),
                    "capital": item.get("regCapital", ""),
                    "establishDate": item.get("estiblishTime", ""),
                    "address": item.get("address", ""),
                })
        
        # 企查查响应格式
        elif "Result" in data:
            for item in data.get("Result", []):
                companies.append({
                    "name": item.get("Name", ""),
                    "keyNo": item.get("KeyNo", ""),
                    "legalPerson": item.get("Oper", ""),
                    "regStatus": item.get("Status", ""),
                    "capital": item.get("RegistCapi", ""),
                    "establishDate": item.get("StartDate", ""),
                    "address": item.get("Address", ""),
                })
        
        return companies[:5]  # 最多取前5个

    def _format_company_info(self, companies: List[Dict[str, Any]]) -> str:
        """格式化公司信息为文本"""
        if not companies:
            return "未找到相关企业信息"
        
        info_lines = []
        for i, company in enumerate(companies, 1):
            info_lines.append(
                f"{i}. {company['name']}\n"
                f"   法人: {company['legalPerson']}\n"
                f"   状态: {company['regStatus']}\n"
                f"   注册资本: {company['capital']}\n"
                f"   成立日期: {company['establishDate']}\n"
                f"   地址: {company['address']}"
            )
        return "\n".join(info_lines)

    async def search_multiple(self, shops: List[Dict[str, Any]]) -> List[SearchResult]:
        """
        批量搜索多个店铺

        Args:
            shops: 店铺列表，每项包含 name 和 keywords

        Returns:
            搜索结果列表
        """
        tasks = [
            self.search_shop(shop["name"], shop["keywords"])
            for shop in shops
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 过滤失败的搜索
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, SearchResult):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"店铺 {shops[i]['name']} 搜索失败：{result}")

        return valid_results

    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()


# 全局实例
search_service = SearchService()

"""
搜索服务
调用外部 API 搜索店铺相关信息
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
    raw_data: Dict[str, Any]


class SearchService:
    """搜索服务"""

    def __init__(self):
        self.base_url = config.search.base_url
        self.api_key = config.search.api_key
        self.timeout = config.search.timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                    "Content-Type": "application/json"
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def search_shop(self, shop_name: str, keywords: List[str]) -> Optional[SearchResult]:
        """
        搜索店铺信息

        Args:
            shop_name: 店铺名称
            keywords: 分词后的关键词列表

        Returns:
            搜索结果
        """
        try:
            session = await self._get_session()

            # 构建搜索请求
            payload = {
                "query": shop_name,
                "keywords": keywords,
                "limit": 5
            }

            async with session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return SearchResult(
                        shop_name=shop_name,
                        keywords=keywords,
                        info=self._extract_info(data),
                        raw_data=data
                    )
                else:
                    logger.warning(f"搜索 API 返回错误状态：{response.status}")
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"搜索请求失败：{e}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"搜索请求超时：{shop_name}")
            return None

    def _extract_info(self, data: Dict[str, Any]) -> str:
        """从搜索响应中提取关键信息"""
        # 根据实际 API 响应结构调整
        if isinstance(data, dict):
            return data.get("summary", data.get("info", str(data)))
        elif isinstance(data, list):
            return "\n".join(str(item) for item in data[:3])
        return str(data)

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

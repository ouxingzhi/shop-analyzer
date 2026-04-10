"""
搜索服务
直接调用天眼查 API 搜索企业信息
"""
import aiohttp
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

from config import config

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    shop_name: str
    search_name: str  # 实际搜索的名称（清理后）
    info: str
    company_list: List[Dict[str, Any]]  # 搜索到的公司列表
    raw_data: Dict[str, Any]


class SearchService:
    """搜索服务 - 直接调用天眼查 API"""

    def __init__(self):
        self.search_url = "https://capi.tianyancha.com/cloud-tempest/app/searchCompany"
        self.timeout = config.search.timeout
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    def _get_search_headers(self) -> Dict[str, str]:
        """获取搜索请求的 Headers"""
        timestamp = int(time.time() * 1000)
        return {
            'Host': 'capi.tianyancha.com',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Mac MacWechat/WMPF MacWechat/3.8.7(0x13080712) UnifiedPCMacWechat(0xf2641843) XWEB/19346',
            'xweb_xhr': '1',
            'Content-Type': 'application/json',
            'version': 'TYC-XCX-WX',
            'Accept': '*/*',
            'Cookie': f'HWWAFSESID=54f151b79a5c0aa1566; HWWAFSESTIME={timestamp}'
        }

    async def search_shop(self, shop_name: str) -> Optional[SearchResult]:
        """
        搜索企业信息（直接调用天眼查 API）

        Args:
            shop_name: 店铺/企业名称（清理后）

        Returns:
            搜索结果
        """
        try:
            session = await self._get_session()
            headers = self._get_search_headers()

            # 构建搜索请求体
            payload = {
                "sortType": 0,
                "pageSize": 5,
                "pageNum": 1,
                "word": shop_name,
                "allowModifyQuery": 1
            }

            async with session.post(self.search_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"天眼查API返回: {str(data)[:1000]}")  # 日志输出
                    company_list = self._extract_company_list(data)
                    logger.info(f"提取到的公司列表: {len(company_list)} 个")
                    info = self._format_company_info(company_list)
                    return SearchResult(
                        shop_name=shop_name,  # 这里先用搜索名称，后面会被替换成原始名称
                        search_name=shop_name,
                        info=info,
                        company_list=company_list,
                        raw_data=data
                    )
                else:
                    logger.warning(f"天眼查 API 返回错误状态：{response.status}")
                    try:
                        error_text = await response.text()
                        logger.warning(f"错误内容：{error_text[:500]}")
                    except:
                        pass
                    return None

        except aiohttp.ClientError as e:
            logger.error(f"搜索请求失败：{e}")
            return None
        except asyncio.TimeoutError:
            logger.error(f"搜索请求超时：{shop_name}")
            return None

    def _extract_company_list(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从搜索响应中提取公司列表"""
        import re
        companies = []

        # 天眼查响应格式 - 新格式
        if "data" in data and "companyList" in data.get("data", {}):
            for item in data["data"]["companyList"]:
                # 清理公司名中的 <em> 标签
                name = item.get("name", "")
                name = re.sub(r'</?em>', '', name)
                
                companies.append({
                    "name": name,
                    "id": item.get("id", ""),
                    "legalPerson": item.get("legalPersonName", "") or item.get("legalPerson", ""),
                    "regStatus": item.get("regStatus", "") or item.get("status", ""),
                    "capital": item.get("regCapital", "") or item.get("capital", ""),
                    "establishDate": item.get("estiblishTime", "") or item.get("establishDate", ""),
                    "address": item.get("regLocation", "") or item.get("address", ""),
                    "phone": item.get("phoneNum", "") or (item.get("phoneList", [""])[0] if item.get("phoneList") else ""),
                    "email": item.get("emails", "") or (item.get("emailList", [""])[0] if item.get("emailList") else ""),
                    "creditCode": item.get("creditCode", ""),
                    "businessScope": item.get("businessScope", "")[:100] if item.get("businessScope") else "",
                })

        # 天眼查响应格式 - 旧格式（兼容）
        elif "result" in data and "resultList" in data.get("result", {}):
            for item in data["result"]["resultList"]:
                name = item.get("name", "")
                name = re.sub(r'</?em>', '', name)
                
                companies.append({
                    "name": name,
                    "id": item.get("id", ""),
                    "legalPerson": item.get("legalPersonName", ""),
                    "regStatus": item.get("regStatus", ""),
                    "capital": item.get("regCapital", ""),
                    "establishDate": item.get("estiblishTime", ""),
                    "address": item.get("regLocation", "") or item.get("address", ""),
                    "phone": "",
                    "email": "",
                    "creditCode": "",
                    "businessScope": "",
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
                f"   地址: {company['address']}\n"
                f"   电话: {company.get('phone', '')}\n"
                f"   邮箱: {company.get('email', '')}"
            )
        return "\n".join(info_lines)

    async def search_multiple(self, shops: List[Dict[str, Any]]) -> List[SearchResult]:
        """
        批量搜索多个店铺（串行执行，避免被封）

        Args:
            shops: 店铺列表，每项包含 name（清理后）、original_name（原始）

        Returns:
            搜索结果列表
        """
        results = []
        for shop in shops:
            # 串行搜索，避免并发请求被封禁
            result = await self.search_shop(shop["name"])
            if result:
                # 用原始名称替换
                result.shop_name = shop.get("original_name", shop["name"])
                results.append(result)
            else:
                # 如果搜索失败，创建一个空结果
                results.append(SearchResult(
                    shop_name=shop.get("original_name", shop["name"]),
                    search_name=shop["name"],
                    info="搜索失败",
                    company_list=[],
                    raw_data={}
                ))
            # 添加延迟，避免请求过快
            await asyncio.sleep(0.5)

        return results

    async def close(self):
        """关闭 HTTP 会话"""
        if self._session and not self._session.closed:
            await self._session.close()


# 全局实例
search_service = SearchService()
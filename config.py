"""
配置文件
从环境变量加载配置，支持 Docker 部署
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TelegramConfig:
    """Telegram Bot 配置"""
    token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    allowed_user_ids: str = os.getenv("TELEGRAM_ALLOWED_USER_IDS", "")  # 逗号分隔的用户 ID 列表，为空则允许所有用户


@dataclass
class DashScopeConfig:
    """阿里云 DashScope（通义千问）配置"""
    api_key: str = os.getenv("DASHSCOPE_API_KEY", "")
    model: str = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
    max_tokens: int = int(os.getenv("DASHSCOPE_MAX_TOKENS", "2000"))


@dataclass
class SearchConfig:
    """搜索 API 配置"""
    base_url: str = os.getenv("SEARCH_API_URL", "http://localhost:3000")  # API 服务地址
    api_type: str = os.getenv("SEARCH_API_TYPE", "tianyancha")  # tianyancha 或 qichacha
    timeout: int = int(os.getenv("SEARCH_TIMEOUT", "30"))


@dataclass
class AppConfig:
    """应用配置"""
    telegram: TelegramConfig
    dashscope: DashScopeConfig
    search: SearchConfig
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


def load_config() -> AppConfig:
    """加载配置"""
    return AppConfig(
        telegram=TelegramConfig(),
        dashscope=DashScopeConfig(),
        search=SearchConfig(),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )


# 全局配置实例
config = load_config()

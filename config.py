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
class AIConfig:
    """AI 模型配置（百炼 GLM-5）"""
    api_key: str = os.getenv("AI_API_KEY", "sk-sp-7a2ad6970c2b4985a640e800d44ffaad")
    model: str = os.getenv("AI_MODEL", "glm-5")
    max_tokens: int = int(os.getenv("AI_MAX_TOKENS", "2000"))


@dataclass
class SearchConfig:
    """搜索配置"""
    timeout: int = int(os.getenv("SEARCH_TIMEOUT", "30"))


@dataclass
class AppConfig:
    """应用配置"""
    telegram: TelegramConfig
    ai: AIConfig
    search: SearchConfig
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"


def load_config() -> AppConfig:
    """加载配置"""
    return AppConfig(
        telegram=TelegramConfig(),
        ai=AIConfig(),
        search=SearchConfig(),
        debug=os.getenv("DEBUG", "false").lower() == "true"
    )


# 全局配置实例
config = load_config()
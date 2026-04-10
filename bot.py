"""
Telegram Bot 主程序
"""
import logging
from typing import List

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import config
from services.tokenizer_service import tokenizer_service
from services.search_service import search_service, SearchResult
from services.analysis_service import analysis_service

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if config.debug else logging.INFO,
)
logger = logging.getLogger(__name__)


def is_user_allowed(user_id: int) -> bool:
    """检查用户是否在允许列表中"""
    if not config.telegram.allowed_user_ids:
        return True  # 空列表表示允许所有用户
    allowed_ids = [int(x.strip()) for x in config.telegram.allowed_user_ids.split(",")]
    return user_id in allowed_ids


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /start 命令"""
    user = update.effective_user
    if not is_user_allowed(user.id):
        await update.message.reply_text("抱歉，您没有权限使用此 Bot。")
        return

    welcome_text = """
👋 欢迎使用店铺分析 Bot！

我可以帮您分析店铺名称列表，进行智能关联分析。

【使用方法】
1. 发送店铺名称列表（每行一个店铺名称）
2. 系统将自动进行分词、搜索和 AI 分析
3. 获取详细的分析报告

【命令列表】
/start - 重启 Bot
/help - 查看帮助
/analyze - 分析已发送的店铺列表

请发送您的店铺名称列表开始使用！
"""
    await update.message.reply_text(welcome_text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /help 命令"""
    user = update.effective_user
    if not is_user_allowed(user.id):
        return

    help_text = """
【使用说明】

1. 发送店铺名称列表，格式如下：
   ```
   星巴克咖啡
   瑞幸咖啡
   库迪咖啡
   麦当劳
   肯德基
   ```

2. 系统处理流程：
   - 对每个店铺名称进行中文分词
   - 调用搜索 API 获取相关信息
   - 使用通义千问 AI 进行关联性分析
   - 输出详细分析报告

3. 支持一次处理 1-20 个店铺名称

【注意事项】
- 请使用中文店铺名称
- 每个店铺名称占一行
- 处理时间取决于店铺数量和搜索速度
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理 /analyze 命令"""
    user = update.effective_user
    if not is_user_allowed(user.id):
        return

    # 检查是否有缓存的店铺列表
    if "shops" not in context.user_data:
        await update.message.reply_text(
            "请先发送店铺名称列表，或使用 /start 重新开始。"
        )
        return

    shops = context.user_data["shops"]
    await process_shops(update, context, shops)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """处理普通消息"""
    user = update.effective_user
    if not is_user_allowed(user.id):
        await update.message.reply_text("抱歉，您没有权限使用此 Bot。")
        return

    text = update.message.text
    if not text:
        return

    # 解析店铺列表
    shops = parse_shop_list(text)

    if not shops:
        await update.message.reply_text(
            "未检测到有效的店铺名称，请每行输入一个店铺名称。"
        )
        return

    if len(shops) > 20:
        await update.message.reply_text(
            f"店铺数量过多（{len(shops)}个），请限制在 20 个以内。"
        )
        return

    # 缓存店铺列表
    context.user_data["shops"] = shops

    await update.message.reply_text(
        f"✅ 已收到 {len(shops)} 个店铺名称，开始分析...\n\n"
        f"店铺列表:\n" + "\n".join(f"• {shop}" for shop in shops)
    )

    await process_shops(update, context, shops)


def parse_shop_list(text: str) -> List[str]:
    """解析店铺列表文本"""
    lines = text.strip().split("\n")
    shops = []
    for line in lines:
        shop = line.strip()
        if shop and len(shop) >= 2:  # 过滤太短的文本
            shops.append(shop)
    return shops


async def process_shops(
    update: Update, context: ContextTypes.DEFAULT_TYPE, shops: List[str]
) -> None:
    """处理店铺列表"""
    status_message = await update.message.reply_text("🔍 正在进行分词处理...")

    try:
        # 1. 分词
        tokenized_shops = []
        for shop in shops:
            keywords = tokenizer_service.tokenize_for_search(shop)
            tokenized_shops.append({"name": shop, "keywords": keywords})
            logger.info(f"分词：{shop} -> {keywords}")

        await status_message.edit_text(
            f"✅ 分词完成，共 {len(tokenized_shops)} 个店铺\n"
            f"🌐 开始搜索..."
        )

        # 2. 搜索
        search_results = await search_service.search_multiple(tokenized_shops)

        if not search_results:
            await status_message.edit_text("⚠️ 搜索失败，请稍后重试。")
            return

        await status_message.edit_text(
            f"✅ 搜索完成，获取到 {len(search_results)} 条结果\n"
            f"🤖 正在进行 AI 分析..."
        )

        # 3. AI 分析
        report = analysis_service.analyze_shops(search_results)

        # 4. 发送报告
        await status_message.edit_text("✅ 分析完成，生成报告中...")

        # 分割长消息发送
        await send_long_message(update, report)

        # 保存搜索结果到上下文（可选）
        context.user_data["search_results"] = search_results

    except Exception as e:
        logger.exception("处理店铺列表时出错")
        await status_message.edit_text(f"❌ 处理失败：{str(e)}")


async def send_long_message(update: Update, text: str) -> None:
    """发送长消息（超过 4096 字符时分段）"""
    max_length = 4096
    chunks = [text[i : i + max_length] for i in range(0, len(text), max_length)]

    for chunk in chunks:
        await update.message.reply_text(chunk, parse_mode="Markdown")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """错误处理"""
    logger.error(f"更新 {update} 导致错误：{context.error}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "抱歉，发生了一个错误。请稍后重试。"
        )


def main() -> None:
    """启动 Bot"""
    # 验证配置
    if not config.telegram.token:
        logger.error("未设置 TELEGRAM_BOT_TOKEN 环境变量")
        return

    if not config.dashscope.api_key:
        logger.error("未设置 DASHSCOPE_API_KEY 环境变量")
        return

    # 创建应用
    application = Application.builder().token(config.telegram.token).build()

    # 添加处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("analyze", analyze_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # 错误处理
    application.add_error_handler(error_handler)

    # 启动 Bot
    logger.info("Bot 启动中...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

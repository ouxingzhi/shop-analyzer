# Telegram Shop Analysis Bot

基于 Telegram 的店铺分析 Bot，使用通义千问 AI 进行智能关联分析。

## 功能特性

- 📝 **中文分词** - 使用 jieba 对店铺名称进行精确分词
- 🔍 **异步搜索** - 使用 aiohttp 并发搜索多个店铺
- 🤖 **AI 分析** - 使用阿里通义千问进行关联性分析
- 📊 **详细报告** - 输出结构化的商业分析报告

## 项目结构

```
.
├── bot.py                  # Bot 主程序
├── config.py               # 配置管理
├── requirements.txt        # Python 依赖
├── Dockerfile             # Docker 构建文件
├── .env.example           # 环境变量示例
└── services/
    ├── __init__.py
    ├── tokenizer_service.py   # 分词服务
    ├── search_service.py      # 搜索服务
    └── analysis_service.py    # AI 分析服务
```

## 快速开始

### 1. 克隆项目

```bash
cd /path/to/project
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入以下配置：
# - TELEGRAM_BOT_TOKEN: 从 @BotFather 获取
# - DASHSCOPE_API_KEY: 阿里云 DashScope API Key
# - SEARCH_API_URL: 搜索 API 地址
# - SEARCH_API_KEY: 搜索 API Key
```

### 4. 运行 Bot

```bash
python bot.py
```

## Docker 部署

### 构建镜像

```bash
docker build -t shop-analysis-bot .
```

### 运行容器

```bash
docker run -d \
  --name shop-bot \
  --env-file .env \
  shop-analysis-bot
```

### 或使用 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  bot:
    build: .
    env_file: .env
    restart: unless-stopped
```

```bash
docker-compose up -d
```

## 使用说明

1. 在 Telegram 中启动 Bot
2. 发送店铺名称列表（每行一个）：
   ```
   星巴克咖啡
   瑞幸咖啡
   库迪咖啡
   麦当劳
   肯德基
   ```
3. Bot 将自动进行分词、搜索和 AI 分析
4. 获取详细的分析报告

## 命令列表

- `/start` - 重启 Bot
- `/help` - 查看帮助
- `/analyze` - 分析已发送的店铺列表

## 环境要求

- Python 3.10+
- Telegram Bot Token
- 阿里云 DashScope API Key
- 搜索 API（可根据实际需求配置或跳过）

## 许可证

MIT License

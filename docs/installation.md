# 安装指南

## 系统要求

- Python 3.10 或更高版本（支持 3.10 / 3.11 / 3.12）
- pip 包管理器
- 操作系统：Linux / macOS / Windows

## 从 PyPI 安装

```bash
pip install fund-cli
```

安装完成后，系统将注册两个命令行入口：

| 命令 | 说明 |
|------|------|
| `fund-cli` | 完整命令 |
| `fund` | 短命令（推荐） |

## 从源码安装

```bash
git clone https://github.com/jarrey-0804/fund-cli.git
cd fund-cli
pip install -e ".[dev]"
```

## Docker 安装

### 使用 docker run

```bash
# 拉取镜像并运行
docker run --rm -it \
  -e FUND_DATA_TUSHARE_TOKEN=your_token \
  -e FUND_AI_API_KEY=your_api_key \
  -v $(pwd)/data:/app/data \
  fund-cli:3.1.0 fund --help
```

### 使用 docker-compose

项目提供了 `docker-compose.yml`，支持一键启动：

```bash
# 基础启动（仅 fund-cli 服务）
docker-compose up fund-cli

# 启动 fund-cli + PostgreSQL 持久化
docker-compose --profile with-db up
```

在项目根目录创建 `.env` 文件，填入以下环境变量：

```bash
TUSHARE_TOKEN=your_tushare_token
AI_API_KEY=your_ai_api_key
```

### Docker 注意事项

- 容器默认以非 root 用户 `fundcli` 运行
- 数据缓存挂载至 Docker volume `fund-cache`
- PostgreSQL 服务需通过 `--profile with-db` 显式启用
- 如需自定义 Docker 镜像，可基于项目 `Dockerfile` 进行构建：

```bash
docker build -t fund-cli:custom .
```

## 可选依赖组

Fund CLI 提供多个可选依赖组，按需安装即可启用对应功能：

| 依赖组 | 安装命令 | 说明 |
|--------|----------|------|
| `docs` | `pip install fund-cli[docs]` | MkDocs 文档构建工具 |
| `postgres` | `pip install fund-cli[postgres]` | PostgreSQL 持久化（LangGraph checkpoint） |
| `mcp` | `pip install fund-cli[mcp]` | MCP 协议支持 |
| `memory` | `pip install fund-cli[memory]` | 长期记忆（ChromaDB 向量数据库） |
| `all-extras` | `pip install fund-cli[all-extras]` | 安装全部可选依赖 |
| `dev` | `pip install fund-cli[dev]` | 开发工具（pytest / black / ruff / mypy） |

示例：

```bash
# 安装全部可选功能依赖
pip install fund-cli[all-extras]

# 开发环境：安装项目 + 全部可选依赖 + 开发工具
pip install -e ".[all-extras,dev]"
```

## 验证安装

```bash
fund --version
fund --help
```

预期输出示例：

```
Fund CLI v3.1.0
```

## 配置详解

复制环境变量模板并编辑：

```bash
cp .env.example .env
```

### 数据源配置

| 环境变量 | 说明 | 默认值 | 必填 |
|----------|------|--------|------|
| `FUND_DATA_AKSHARE_ENABLED` | 启用 AKShare 数据源（免费，无需 Token） | `true` | 否 |
| `FUND_DATA_TUSHARE_TOKEN` | Tushare API Token（[注册获取](https://tushare.pro/register)） | 无 | 否* |
| `FUND_DATA_WIND_ENABLED` | 启用 Wind 数据源（商业授权） | `false` | 否 |
| `FUND_DATA_WIND_USERNAME` | Wind 用户名 | 无 | 否 |
| `FUND_DATA_WIND_PASSWORD` | Wind 密码 | 无 | 否 |
| `FUND_DATA_CACHE_TTL` | 数据缓存有效期（秒） | `3600` | 否 |
| `FUND_DATA_CACHE_DIR` | 数据缓存目录 | `~/.fund_cli/cache` | 否 |

!!! note
    \* Tushare Token 为可选配置。未配置时系统将自动降级使用 AKShare 数据源。

### AI 配置

| 环境变量 | 说明 | 默认值 | 必填 |
|----------|------|--------|------|
| `FUND_AI_PROVIDER` | LLM 提供商（`openai` / `anthropic` / `azure` 等） | `openai` | 否 |
| `FUND_AI_MODEL` | 模型名称 | `gpt-4` | 否 |
| `FUND_AI_API_KEY` | API Key | 无 | 是** |
| `FUND_AI_API_BASE` | API Base URL（可选，用于代理或私有部署） | 无 | 否 |
| `FUND_AI_TEMPERATURE` | 生成温度（0.0 ~ 1.0） | `0.7` | 否 |
| `FUND_AI_MAX_TOKENS` | 最大生成 Token 数 | `2000` | 否 |

!!! note
    \** AI 功能为可选模块。未配置 API Key 时，系统将使用内置规则引擎提供基础分析能力。

### 分析配置

| 环境变量 | 说明 | 默认值 | 必填 |
|----------|------|--------|------|
| `FUND_ANALYSIS_RISK_FREE_RATE` | 无风险利率（用于夏普比率等计算） | `0.03` | 否 |
| `FUND_ANALYSIS_DEFAULT_BENCHMARK` | 默认基准指数代码 | `000300` | 否 |
| `FUND_ANALYSIS_DEFAULT_PERIOD` | 分析周期默认值 | `1y` | 否 |

### 日志与调试配置

| 环境变量 | 说明 | 默认值 | 必填 |
|----------|------|--------|------|
| `FUND_LOG_LEVEL` | 日志级别（`DEBUG` / `INFO` / `WARNING` / `ERROR`） | `INFO` | 否 |
| `FUND_LOG_FILE` | 日志文件路径 | 无（仅输出到控制台） | 否 |
| `FUND_DEBUG` | 调试模式 | `false` | 否 |
| `FUND_DEV_MODE` | 开发模式（跳过缓存等） | `false` | 否 |

## 常见问题

### Python 版本不满足要求

**问题**：安装时提示 `ERROR: Package 'fund-cli' requires a different Python`。

**解决方案**：Fund CLI 要求 Python 3.10 或更高版本。请检查并升级 Python 版本：

```bash
python --version

# 推荐使用 pyenv 管理多版本 Python
pyenv install 3.11
pyenv global 3.11
```

### AKShare 安装失败

**问题**：安装 AKShare 时出现编译错误或依赖冲突。

**解决方案**：

```bash
# 升级 pip 和 setuptools
pip install --upgrade pip setuptools wheel

# 单独安装 AKShare
pip install akshare --upgrade

# 如果仍失败，尝试指定版本
pip install akshare==1.12.0
```

### Tushare Token 如何获取

**问题**：配置了 Tushare Token 但数据获取失败。

**解决方案**：

1. 前往 [Tushare 官网](https://tushare.pro/register) 注册账号
2. 登录后在个人主页获取 API Token
3. 将 Token 填入环境变量 `FUND_DATA_TUSHARE_TOKEN`
4. 新注册账号部分接口有积分限制，详见 [Tushare 积分规则](https://tushare.pro/document/1)

### Docker 权限问题

**问题**：运行 Docker 容器时提示权限不足。

**解决方案**：

```bash
# Linux 用户需要加入 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使组变更生效
newgrp docker

# 验证 Docker 权限
docker run hello-world
```

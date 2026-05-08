# 安装指南

## 系统要求

- Python 3.10+
- pip

## 从 PyPI 安装

```bash
pip install fund-cli
```

## 从源码安装

```bash
git clone https://github.com/your-org/fund-cli.git
cd fund-cli
pip install -e ".[dev]"
```

## 验证安装

```bash
fund --version
fund --help
```

## 配置

复制环境变量模板并编辑：

```bash
cp .env.example .env
```

主要配置项：

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `FUND_DATA_AKSHARE_ENABLED` | 启用AKShare数据源 | `true` |
| `FUND_DATA_TUSHARE_TOKEN` | Tushare API Token | 无 |
| `FUND_ANALYSIS_RISK_FREE_RATE` | 无风险利率 | `0.03` |
| `FUND_ANALYSIS_DEFAULT_BENCHMARK` | 默认基准指数 | `000300` |
| `FUND_AI_PROVIDER` | AI提供商 (V2.0) | `openai` |
| `FUND_AI_API_KEY` | AI API Key (V2.0) | 无 |

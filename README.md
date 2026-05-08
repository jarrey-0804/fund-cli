# Fund CLI

<div align="center">

**专业基金分析CLI工具 - 面向机构客户**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## 简介

Fund CLI 是一款面向机构客户的专业基金分析命令行工具，提供基金筛选、业绩分析、组合对比、风险监控等功能。基于开源技术栈构建，支持多数据源接入和AI辅助分析。

## 核心功能

- **基金筛选** - 多维度筛选条件，支持业绩、风险、规模等指标
- **业绩分析** - 收益率、夏普比率、最大回撤等专业指标
- **基金对比** - 多基金横向对比分析
- **组合优化** - 基于现代投资组合理论的资产配置优化
- **AI分析** (V2.0) - AI辅助投资分析和报告生成
- **多数据源** - 支持AKShare、Tushare、Wind等数据源

---

## 安装指南

### 系统要求

- Python 3.10 或更高版本
- pip 包管理器

### 使用 pip 安装

```bash
pip install fund-cli
```

### 从源码安装

```bash
git clone https://github.com/jarrey-0804/fund-cli.git
cd fund-cli
pip install -e ".[dev]"
```

### 验证安装

```bash
fund --version
fund --help
```

---

## 使用教程

### 基本命令

```bash
# 查看帮助
fund --help

# 筛选基金
fund filter --type 股票型 --min-scale 10

# 分析基金
fund analyze 000001

# 对比基金
fund compare 000001 000002 000003

# 查看基金信息
fund info 000001
```

### AI分析功能 (V2.0)

```bash
# 配置AI服务
fund ai config --provider qwen --api-key YOUR_API_KEY

# AI基金分析
fund ai summarize 000001

# AI投资建议
fund ai advice --risk-level 中等

# AI风险评估
fund ai risk 000001
```

### 组合优化

```bash
# 均值方差优化
fund optimize mean-variance 000001 000002 000003

# 风险平价优化
fund optimize risk-parity 000001 000002 000003

# 最大夏普比率优化
fund optimize max-sharpe 000001 000002 000003
```

### 数据管理

```bash
# 更新基金数据
fund data update

# 查看数据缓存
fund data cache info

# 清理缓存
fund data cache clear
```

---

## API文档

### Python API 使用

```python
from fund_cli import FundClient

# 创建客户端
client = FundClient()

# 获取基金信息
fund_info = client.get_fund("000001")

# 分析基金
analysis = client.analyze("000001")

# 筛选基金
funds = client.screen(type="股票型", min_scale=10)

# 对比基金
comparison = client.compare(["000001", "000002", "000003"])
```

### AI分析 API

```python
from fund_cli.ai import AIAnalyzer

# 创建分析器
analyzer = AIAnalyzer(provider="qwen", api_key="YOUR_API_KEY")

# 基金摘要
summary = analyzer.summarize_fund("000001")

# 投资建议
advice = analyzer.investment_advice(risk_level="中等")

# 风险评估
risk = analyzer.risk_assessment("000001")
```

---

## 开发指南

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/jarrey-0804/fund-cli.git
cd fund-cli

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit 钩子
pre-commit install
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行带覆盖率
pytest --cov=src/fund_cli tests/

# 运行特定测试
pytest tests/unit/test_core/ -v
```

### 代码质量

```bash
# 代码格式化
black src tests

# Lint检查
ruff check src tests

# 类型检查
mypy src
```

### 项目结构

```
fund-cli/
├── src/fund_cli/          # 源代码
│   ├── cli.py             # CLI入口
│   ├── config.py          # 配置管理
│   ├── core/              # 核心模块
│   ├── data/              # 数据层
│   ├── analysis/          # 分析模块
│   ├── ai/                # AI模块 (V2.0)
│   ├── commands/          # CLI命令
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
├── docs/                  # 文档
└── examples/              # 示例脚本
```

---

## 技术栈

| 类别 | 技术 |
|------|------|
| CLI框架 | Typer, Rich |
| 数据处理 | Pandas, NumPy |
| 数据源 | AKShare, Tushare |
| 量化分析 | QuantStats, PyPortfolioOpt |
| 可视化 | Plotly, Matplotlib |
| AI集成 | LiteLLM, Qwen |

---

## 更多文档

- [安装指南](https://github.com/jarrey-0804/fund-cli/blob/main/docs/installation.md)
- [使用教程](https://github.com/jarrey-0804/fund-cli/blob/main/docs/usage/tutorial.md)
- [API参考](https://github.com/jarrey-0804/fund-cli/blob/main/docs/api/reference.md)
- [开发指南](https://github.com/jarrey-0804/fund-cli/blob/main/docs/development.md)

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 联系方式

- 问题反馈: [GitHub Issues](https://github.com/jarrey-0804/fund-cli/issues)
- 功能建议: [GitHub Discussions](https://github.com/jarrey-0804/fund-cli/discussions)

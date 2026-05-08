# Fund CLI

<div align="center">

**专业基金分析CLI工具 - 面向机构客户**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## 📖 简介

Fund CLI 是一款面向机构客户的专业基金分析命令行工具，提供基金筛选、业绩分析、组合对比、风险监控等功能。基于开源技术栈构建，支持多数据源接入和AI辅助分析。

## ✨ 核心功能

- 🔍 **基金筛选** - 多维度筛选条件，支持业绩、风险、规模等指标
- 📊 **业绩分析** - 收益率、夏普比率、最大回撤等专业指标
- ⚖️ **基金对比** - 多基金横向对比分析
- 📈 **组合优化** - 基于现代投资组合理论的资产配置优化
- 🤖 **AI分析** (V2.0) - AI辅助投资分析和报告生成
- 💾 **多数据源** - 支持AKShare、Tushare、Wind等数据源

## 🚀 快速开始

### 安装

```bash
# 使用 pip 安装
pip install fund-cli

# 或从源码安装
git clone https://github.com/your-org/fund-cli.git
cd fund-cli
pip install -e ".[dev]"
```

### 基本使用

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

## 📚 文档

- [安装指南](docs/installation.md)
- [使用教程](docs/usage/)
- [API文档](docs/api/)
- [开发指南](docs/development.md)

## 🛠️ 技术栈

| 类别 | 技术 |
|------|------|
| CLI框架 | Typer, Rich |
| 数据处理 | Pandas, NumPy |
| 数据源 | AKShare, Tushare |
| 量化分析 | QuantStats, PyPortfolioOpt |
| 可视化 | Plotly, Matplotlib |
| AI集成 | LiteLLM |

## 📁 项目结构

```
fund-cli/
├── src/fund_cli/          # 源代码
│   ├── cli.py             # CLI入口
│   ├── config.py          # 配置管理
│   ├── core/              # 核心模块
│   ├── data/              # 数据层
│   ├── analysis/          # 分析模块
│   ├── commands/          # CLI命令
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
├── docs/                  # 文档
└── examples/              # 示例脚本
```

## 🧪 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit 钩子
pre-commit install

# 运行测试
pytest tests/

# 代码格式化
black src tests

# Lint检查
ruff check src tests

# 类型检查
mypy src
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 📧 联系方式

- 问题反馈: [GitHub Issues](https://github.com/your-org/fund-cli/issues)
- 功能建议: [GitHub Discussions](https://github.com/your-org/fund-cli/discussions)

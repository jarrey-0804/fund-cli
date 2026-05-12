# Fund CLI

<div align="center">

**专业基金分析CLI工具 - 面向机构客户**

[![Version](https://img.shields.io/badge/version-3.5.0-blue.svg)](https://github.com/jarrey-0804/fund-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## 简介

Fund CLI 是一款面向机构客户的专业基金分析命令行工具，提供基金筛选、业绩分析、组合对比、风险监控等功能。基于开源技术栈构建，支持多数据源接入和AI辅助分析。

## v3.2 新特性

### 五层数据质量治理架构
- **Layer 1 数据采集层**: Gateway路由 + 熔断器/重试/降级机制
- **Layer 2 数据标准化管道**: Pydantic模型验证 + 重复检测 + 净值范围校验
- **Layer 3 质量检查引擎**: 8项Expectation风格自动化检查
- **Layer 4 计算验证层**: 12项指标合理性边界验证 + 交叉验证
- **Layer 5 输出合规层**: 报告完整性验证 + 免责声明检查

### 新增质量模块
- **QualityGate**: 分析入口强制执行数据质量检查
- **CalcValidator**: Sharpe/回撤/波动率等12项指标合理性验证
- **CrossValidator**: PerformanceAnalyzer与RiskAnalyzer交叉验证
- **AIOutputValidator**: AI生成内容与源数据一致性校验
- **ReportValidator**: 报告必需字段和合规性检查
- **AuditLogger**: 质量检查/分析操作/报告生成审计日志

## v3.1 新特性

### 多数据源架构
- **统一适配器接口**: 支持 Tushare、AKShare、Wind 三大数据源
- **数据源网关**: 熔断器 + 降级 + 重试机制，保障数据获取稳定性
- **数据标准化**: 跨数据源字段映射、日期格式统一、基金代码标准化

### 报告引擎增强
- **5种报告格式**: HTML、Markdown、PDF、Word、PowerPoint
- **4类报告模板**: 单基金研究、投资组合、市场资金流向、合规风控
- **Jinja2模板引擎**: 支持自定义模板和过滤器

### AI分析增强
- **双后端支持**: 规则引擎（零配置）+ OpenAI API（高精度）
- **智能分析**: 基金/组合摘要、风险提示、投资建议、亮点/风险点提取

### v3.0 新特性

- **AI Agent 对话** - 基于 LangGraph 的智能对话系统
  - 12+ 数据接口工具自动调用
  - 多轮对话上下文保持
  - 记忆系统（可选 ChromaDB）
- **MCP 协议支持** - Model Context Protocol 集成
- **持仓分析** - 行业分布、集中度、风格分析
- **基金经理分析** - 业绩、稳定性、管理规模
- **组合优化** - 均值方差/最大夏普/风险平价
- **归因分析** - Brinson 归因模型
- **监控预警** - 净值变动监控和预警
- **交互式模式** - REPL 交互式命令行

## 核心功能

- **基金筛选** - 多维度筛选条件，支持业绩、风险、规模等指标
- **业绩分析** - 收益率、夏普比率、最大回撤等专业指标
- **基金对比** - 多基金横向对比分析
- **组合优化** - 基于现代投资组合理论的资产配置优化
- **AI分析** (V2.0) - AI辅助投资分析和报告生成
- **多数据源架构** (v3.1) - Tushare/AKShare/Wind 统一接入，熔断降级机制
- **报告引擎** (v3.1) - HTML/Markdown/PDF/Word/PPT 5种格式报告
- **AI增强** (v3.1) - 规则引擎 + OpenAI 双后端智能分析
- **数据质量治理** (v3.2) - 五层质量架构 + 审计日志 + 合规验证

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

### Docker 部署

```bash
# 拉取镜像并运行
docker run --rm -e FUND_DATA_TUSHARE_TOKEN=your_token fund-cli:latest fund --help

# 使用 docker-compose
docker compose up fund-cli
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

### 报告生成功能 (v3.1)

```bash
# 生成单基金研究报告
fund report --type single_fund --fund 000001 --format pdf

# 生成投资组合报告
fund report --type portfolio --funds 000001,000002 --format html

# 列出可用模板
fund list-templates
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
│   │   ├── adapters/      # 数据源适配器 (v3.1)
│   │   ├── gateway.py     # 数据源网关 (v3.1)
│   │   └── normalizer.py  # 数据标准化 (v3.1)
│   ├── analysis/          # 分析模块
│   ├── ai/                # AI模块 (V2.0/V3.1)
│   ├── report/            # 报告引擎 (v3.1)
│   ├── commands/          # CLI命令
│   └── utils/             # 工具函数
├── tests/                 # 测试代码
├── docs/                  # 文档
└── examples/              # 示例脚本
```

## 架构设计

### 多数据源架构

```
┌─────────────────────────────────────────────────────────────┐
│                      DataSourceGateway                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  熔断器     │  │  降级策略   │  │  重试机制           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ TushareAdapter│    │ AKShareAdapter│    │  WindAdapter  │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 报告引擎架构

```
┌─────────────────────────────────────────────────────────────┐
│                      ReportEngine                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Template   │  │  Data       │  │  Export             │  │
│  │  Engine     │  │  Provider   │  │  Adapters           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  HTML/Markdown│    │  PDF (Weasy)  │    │ Word/PPT      │
└───────────────┘    └───────────────┘    └───────────────┘
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

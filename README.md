# Fund CLI

<div align="center">

**专业基金分析CLI工具 - 面向机构客户**

[![Version](https://img.shields.io/badge/version-3.8.0-blue.svg)](https://github.com/jarrey-0804/fund-cli)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

</div>

---

## 简介

Fund CLI 是一款面向机构客户的专业基金分析命令行工具，提供基金筛选、业绩分析、组合对比、风险监控等功能。基于开源技术栈构建，支持多数据源接入和AI辅助分析。

## v3.8.0 新特性

### Qieman MCP 数据源集成
- **74个专业接口**: 完整集成Qieman MCP服务器，覆盖基金分析、资产配置、策略研究、行情资讯等
- **双数据源架构**: AKShare + Qieman MCP 双数据源互补，提升数据质量和分析深度
- **QDII基金持仓穿透**: 通过Qieman获取QDII基金持仓明细，解决AKShare无法获取的问题
- **Brinson归因分析**: 股票收益归因分析，量化选股和配置贡献
- **Campisi债券归因**: 债券基金收益归因分析
- **组合诊断与回测**: 一键组合诊断和历史回测
- **蒙特卡洛模拟**: 基于模拟的资产配置分析
- **基金筛选器**: 按换手率、信用评级、券种风格筛选基金
- **行业分析**: 行业偏好、收益贡献、配置、集中度多维分析
- **策略研究**: 投顾策略搜索、持仓、风险分析
- **资讯整合**: AI资讯解读、基金经理观点、财经新闻搜索

### 数据源配置

```bash
# 环境变量配置
export FUND_DATA_QIEMAN_API_KEY="your-api-key"
export FUND_DATA_QIEMAN_ENABLED="true"
```

### Qieman 接口分类

| 分类 | 数量 | 代表接口 |
|------|------|---------|
| 基金分析 | 30 | 净值、业绩、诊断、回测 |
| 策略研究 | 7 | 策略搜索、持仓、风险 |
| 行情资讯 | 7 | AI解读、经理观点、新闻 |
| 资产配置 | 6 | 配置分析、蒙特卡洛、风险评估 |
| 基金指标 | 6 | Brinson/Campisi归因、择时 |
| 债券基金 | 3 | 券种配置、信用评级 |
| 基金筛选 | 3 | 换手率、信用评级筛选 |
| 其他 | 12 | 公告、分红、PDF渲染等 |

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
│  AKShareAdapter│   │ QiemanAdapter │    │  WindAdapter  │
│  (开源数据)    │   │ (74个MCP接口) │    │  (专业数据)   │
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
| 数据源 | AKShare, Qieman MCP |
| 量化分析 | QuantStats, PyPortfolioOpt |
| 可视化 | Plotly, Matplotlib |
| AI集成 | LiteLLM, Qwen |

---

## 已知限制

### 数据源限制

| 限制项 | 说明 | 建议 |
|--------|------|------|
| **QDII基金持仓穿透** | AKShare数据源无法获取QDII基金的持仓明细数据 | 如需完整穿透分析，建议接入Wind或Bloomberg等专业数据源 |
| **推荐新基金** | 当前推荐基于同类排名的模拟推荐，非真实基金池筛选 | 建议结合专业基金池数据（如朝阳永续）使用 |
| **相关性分析** | 依赖基金净值数据，当数据不足时将显示提示信息 | 确保网络连接正常，或稍后重试 |

### 功能限制

- **基金经理评分**：细分得分（择股/择时/创新高等）为基于公开数据的估算值
- **舆情核查**：当前仅检查公开公告，不包含社交媒体舆情
- **调仓建议**：推荐基金列表为模拟数据，不构成投资建议

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

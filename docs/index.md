# Fund CLI

**专业基金分析 CLI 工具 -- 面向机构客户**

Fund CLI 是一款面向机构客户的专业基金分析命令行工具，提供基金筛选、业绩分析、组合对比、风险监控、AI 辅助分析等全流程功能。基于多数据源架构构建，支持 Tushare、AKShare、Wind 三大数据源统一接入，内置熔断降级机制保障数据获取稳定性。

---

## 功能亮点

### :material-database-multiple: 多数据源架构

统一适配器接口接入 Tushare、AKShare、Wind 三大数据源，内置数据源网关（熔断器 + 降级策略 + 重试机制），跨数据源字段映射与日期格式标准化，保障数据获取的稳定性与一致性。

### :material-brain: 智能分析引擎

双后端智能分析：规则引擎（零配置即可使用）与 OpenAI API（高精度分析）。支持基金摘要生成、风险评估、投资建议、亮点与风险点提取等能力，并可扩展接入 Qwen、Anthropic 等多家 LLM 提供商。

### :material-file-chart: 报告生成引擎

基于 Jinja2 模板引擎，支持 HTML、Markdown、PDF、Word、PowerPoint 五种输出格式。内置单基金研究、投资组合、市场资金流向、合规风控四类报告模板，支持自定义模板扩展。

### :material-chart-bell-curve-cumulative: 组合优化

基于现代投资组合理论，提供均值方差优化、最大夏普比率优化、风险平价优化、有效前沿分析等多种资产配置策略，辅助机构客户构建最优投资组合。

### :material-robot-outline: AI Agent 对话

基于 LangGraph 构建的 AI Agent 系统，支持多轮对话、工具调用、长期记忆和 MCP 协议扩展。通过自然语言交互完成基金筛选、数据查询、分析报告生成等复杂任务。

### :material-bell-alert-outline: 监控预警

实时监控基金净值变动、异常波动和风险指标，支持自定义预警规则与多渠道通知。帮助机构客户及时捕捉市场变化，控制投资风险。

---

## 快速开始

### 1. 安装

```bash
pip install fund-cli
```

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件，填入数据源 Token 和 AI API Key
# AKShare 免费无需 Token，开箱即用
```

### 3. 首次分析

```bash
# 查看版本与帮助
fund --version
fund --help

# 筛选股票型基金
fund filter basic --type 股票型

# 分析单只基金
fund analyze info 000001
fund analyze metrics 000001

# 对比多只基金
fund compare funds 000001 000002 000003
```

---

## 版本信息

### v3.1.0 核心特性

| 特性 | 说明 |
|------|------|
| 多数据源架构 | Tushare / AKShare / Wind 统一接入，熔断降级机制 |
| 报告引擎 | 5 种格式（HTML/MD/PDF/Word/PPT），4 类模板 |
| AI 双后端 | 规则引擎（零配置）+ OpenAI API（高精度） |
| 数据标准化 | 跨数据源字段映射、日期格式统一、基金代码标准化 |
| 数据质量校验 | 完整性检查、异常值检测、数据一致性验证 |

---

## 文档导航

### 投资分析师

- [快速入门](usage/index.md) -- 5 分钟上手核心功能
- [基金分析](usage/analysis.md) -- 收益率、夏普比率、最大回撤等专业指标
- [基金对比](usage/comparison.md) -- 多基金横向对比分析
- [AI 分析](usage/ai-analysis.md) -- AI 辅助投资分析与报告生成

### 风控与合规人员

- [监控预警](usage/monitoring.md) -- 实时监控与预警规则配置
- [组合优化](usage/optimization.md) -- 资产配置优化策略
- [报告生成](usage/report-generation.md) -- 合规风控报告模板

### 开发与运维人员

- [安装指南](installation.md) -- pip / Docker / 源码安装
- [API 参考](api/reference.md) -- Python API 完整文档
- [开发指南](development.md) -- 项目结构、代码规范、扩展开发
- [贡献指南](contributing.md) -- 代码提交规范与审查流程

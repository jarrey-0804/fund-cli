# API 参考文档

Fund CLI v3.1 完整 API 参考。所有文档通过 [mkdocstrings](https://mkdocstrings.github.io/) 自动从源码 docstring 生成，确保文档与代码始终保持同步。

## 模块索引

| 模块 | 说明 | 文档链接 |
|------|------|----------|
| 核心模块 | 数据管理、分析引擎、报告生成、模板引擎 | [core.md](core.md) |
| 分析模块 | 业绩分析、风险分析、归因分析、组合分析 | [analysis.md](analysis.md) |
| AI 模块 | AI Agent、LLM 提供商、智能分析 | [ai.md](ai.md) |
| 数据层 | 数据源适配器、数据模型、标准化 | [data.md](data.md) |
| 优化器 | 均值方差、最大夏普、风险平价、有效前沿 | [optimizers.md](optimizers.md) |
| 报告生成器 | HTML、Markdown、PDF、Word、PPT 报告 | [reporters.md](reporters.md) |

## 快速示例

```python
from fund_cli.core.data_manager import DataManager
from fund_cli.analysis.performance import PerformanceAnalyzer
from fund_cli.analysis.risk import RiskAnalyzer

# 获取基金数据
dm = DataManager()
nav_data = dm.get_fund_nav("000001")

# 业绩分析
perf = PerformanceAnalyzer(risk_free_rate=0.03)
metrics = perf.analyze(returns, benchmark=benchmark_returns)

# 风险分析
risk = RiskAnalyzer()
risk_metrics = risk.analyze(returns)
```

## 文档约定

- 所有 API 文档使用 `:::` 语法自动生成，源码中的 docstring 即为文档源
- 标记 `show_inheritance_diagram: true` 的类会展示继承关系图
- 类型注解和默认参数值会自动从函数签名提取

# API 文档

## 核心模块

### DataManager

数据管理器，统一管理多数据源。

```python
from fund_cli.core.data_manager import DataManager

dm = DataManager()
info = dm.get_fund_info("000001")
nav = dm.get_fund_nav("000001")
```

### PerformanceAnalyzer

业绩分析引擎。

```python
from fund_cli.analysis.performance import PerformanceAnalyzer

analyzer = PerformanceAnalyzer(risk_free_rate=0.03)
metrics = analyzer.analyze(returns, benchmark=benchmark_returns)
```

### RiskAnalyzer

风险分析引擎。

```python
from fund_cli.analysis.risk import RiskAnalyzer

analyzer = RiskAnalyzer()
metrics = analyzer.analyze(returns)
```

## 数据模型

### FundInfo

```python
from fund_cli.data.models import FundInfo

fund = FundInfo(
    code="000001",
    name="华夏成长混合",
    type=FundType.MIXED,
)
```

### FundFilter

```python
from fund_cli.data.models import FundFilter

f = FundFilter(
    fund_type=FundType.EQUITY,
    min_scale=10.0,
    min_return_1y=10.0,
)
```

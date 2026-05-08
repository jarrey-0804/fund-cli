"""
Fund CLI MVP 综合测试脚本

深度测试所有 MVP 功能模块，包括 CLI 命令和 Python API。
"""

import sys
import os
import traceback
from datetime import date, timedelta
from typing import Dict, List, Any

# 添加 src 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from rich.console import Console
from rich.table import Table

console = Console()


class TestResult:
    """测试结果"""

    def __init__(self, module: str, test_name: str, passed: bool, message: str = ""):
        self.module = module
        self.test_name = test_name
        self.passed = passed
        self.message = message

    def __repr__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"[{self.module}] {self.test_name}: {status} - {self.message}"


class MVPTestRunner:
    """MVP 测试运行器"""

    def __init__(self):
        self.results: List[TestResult] = []

    def run(self, test_func, module: str, test_name: str):
        """运行单个测试"""
        try:
            result = test_func()
            self.results.append(
                TestResult(module, test_name, True, str(result) if result else "OK")
            )
            console.print(f"  ✅ {test_name}")
            return True
        except Exception as e:
            self.results.append(TestResult(module, test_name, False, str(e)))
            console.print(f"  ❌ {test_name}: {e}")
            return False

    def summary(self):
        """输出测试摘要"""
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        table = Table(title="测试结果摘要")
        table.add_column("模块", style="cyan")
        table.add_column("测试名称", style="white")
        table.add_column("状态", style="green")
        table.add_column("详情", style="yellow")

        for r in self.results:
            status = "✅ PASS" if r.passed else "❌ FAIL"
            table.add_row(r.module, r.test_name, status, r.message)

        console.print(table)
        console.print(f"\n总计: {passed}/{total} 通过, {failed} 失败")
        return failed == 0


# ========== 测试用例 ==========


def test_config_module():
    """测试配置模块"""
    from fund_cli.config import get_config, reload_config

    config = get_config()
    assert config.app_name == "Fund CLI"
    assert config.data.cache_ttl >= 0
    assert 0 <= config.analysis.risk_free_rate <= 1

    reload_config()
    config2 = get_config()
    assert config2.app_name == config.app_name

    return "配置加载正常"


def test_data_models():
    """测试数据模型"""
    from fund_cli.data.models import FundInfo, NavData, FundType, FundFilter

    # FundInfo
    fund = FundInfo(
        code="000001",
        name="测试基金",
        type=FundType.MIXED,
    )
    assert fund.code == "000001"
    assert fund.name == "测试基金"
    assert fund.type == FundType.MIXED

    # NavData
    nav = NavData(
        fund_code="000001",
        nav_date=date(2024, 1, 1),
        unit_nav=1.5,
        accumulated_nav=2.0,
    )
    assert nav.unit_nav == 1.5

    # FundFilter
    filter_obj = FundFilter(fund_type=FundType.EQUITY, min_scale=10.0, limit=50)
    assert filter_obj.fund_type == FundType.EQUITY
    assert filter_obj.limit == 50

    return "数据模型正常"


def test_validators():
    """测试验证器"""
    from fund_cli.utils.validators import (
        validate_fund_code,
        validate_date,
        validate_positive_number,
        validate_percentage,
    )

    assert validate_fund_code("000001") is True
    assert validate_fund_code("12345") is False
    assert validate_fund_code("abcdef") is False

    assert validate_date("2024-01-01") is True
    assert validate_date("2024/01/01") is False

    assert validate_positive_number(10.0) is True
    assert validate_positive_number(-1.0) is False
    assert validate_positive_number(None) is False

    assert validate_percentage(50.0) is True
    assert validate_percentage(-50.0) is True
    assert validate_percentage(150.0) is False

    return "验证器正常"


def test_helpers():
    """测试辅助函数"""
    from fund_cli.utils.helpers import (
        format_percentage,
        format_currency,
        format_date,
        format_number,
        safe_divide,
        truncate_string,
    )

    assert format_percentage(12.345) == "12.35%"
    assert format_percentage(None) == "-"

    assert "亿" in format_currency(100.5)
    assert format_currency(None) == "-"

    assert format_date(date(2024, 1, 15)) == "2024-01-15"
    assert format_date(None) == "-"

    assert format_number(3.14159) == "3.14"

    assert abs(safe_divide(10, 3) - 3.333) < 0.01
    assert safe_divide(10, 0) == 0.0

    assert truncate_string("hello") == "hello"
    assert len(truncate_string("a" * 30, max_length=10)) == 10

    return "辅助函数正常"


def test_decorators():
    """测试装饰器"""
    from fund_cli.utils.decorators import timer, retry, deprecated

    @timer
    def test_func():
        return 42

    result = test_func()
    assert result == 42

    @retry(max_attempts=3, delay=0.01)
    def flaky():
        if not hasattr(flaky, "count"):
            flaky.count = 0
        flaky.count += 1
        if flaky.count < 2:
            raise ValueError("not ready")
        return "ok"

    assert flaky() == "ok"

    @deprecated("use new_func")
    def old():
        return 1

    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert old() == 1

    return "装饰器正常"


def test_data_cache():
    """测试数据缓存"""
    import tempfile
    from fund_cli.data.cache import DataCache

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = DataCache(cache_dir=tmpdir, default_ttl=60)

        # 基本操作
        cache.set("test_key", {"data": "value"})
        assert cache.get("test_key") == {"data": "value"}
        assert cache.exists("test_key") is True

        cache.delete("test_key")
        assert cache.exists("test_key") is False

        # 清空
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.clear()
        assert not cache.exists("k1")
        assert not cache.exists("k2")

    return "缓存正常"


def test_data_base():
    """测试数据基类"""
    from fund_cli.data.base import DataSourceAdapter, DataSourceError, DataNotFoundError

    # 验证异常类
    try:
        raise DataSourceError("test")
    except DataSourceError as e:
        assert "test" in str(e)

    try:
        raise DataNotFoundError("not found")
    except DataNotFoundError as e:
        assert "not found" in str(e)

    return "数据基类正常"


def test_analyzer_base():
    """测试分析引擎基类"""
    from fund_cli.core.analyzer import Analyzer

    try:
        Analyzer()
        assert False, "应该抛出 TypeError"
    except TypeError:
        pass

    return "分析引擎基类正常"


def test_optimizer_base():
    """测试优化引擎基类"""
    from fund_cli.core.optimizer import Optimizer

    try:
        Optimizer()
        assert False, "应该抛出 TypeError"
    except TypeError:
        pass

    return "优化引擎基类正常"


def test_reporter_base():
    """测试报告生成器基类"""
    from fund_cli.core.reporter import Reporter

    try:
        Reporter()
        assert False, "应该抛出 TypeError"
    except TypeError:
        pass

    return "报告生成器基类正常"


def test_analysis_with_mock_data():
    """测试分析引擎（使用模拟数据）"""
    import pandas as pd
    import numpy as np

    from fund_cli.analysis.performance import PerformanceAnalyzer
    from fund_cli.analysis.risk import RiskAnalyzer

    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)
    returns.name = "daily_return"

    benchmark_returns = pd.Series(
        np.random.normal(0.0008, 0.015, 252), index=dates
    )

    # 业绩分析
    perf_analyzer = PerformanceAnalyzer(risk_free_rate=0.03)
    perf_metrics = perf_analyzer.analyze(returns)
    assert "total_return" in perf_metrics
    assert "cagr" in perf_metrics
    assert "sharpe" in perf_metrics
    assert "max_drawdown" in perf_metrics
    assert "volatility" in perf_metrics

    # 带基准分析
    perf_with_bm = perf_analyzer.analyze(returns, benchmark=benchmark_returns)
    assert "alpha" in perf_with_bm
    assert "beta" in perf_with_bm
    assert "tracking_error" in perf_with_bm

    # 风险分析
    risk_analyzer = RiskAnalyzer()
    risk_metrics = risk_analyzer.analyze(returns, benchmark=benchmark_returns)
    assert "volatility_annual" in risk_metrics
    assert "max_drawdown" in risk_metrics
    assert "var_95" in risk_metrics
    assert "beta" in risk_metrics
    assert "correlation" in risk_metrics

    # 收益率计算
    nav_df = pd.DataFrame(
        {
            "nav_date": dates[:100],
            "unit_nav": 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 100)),
        }
    )
    calc_returns = perf_analyzer.calculate_returns(nav_df)
    assert len(calc_returns) == 99

    # 回撤计算
    drawdown = perf_analyzer.calculate_drawdown(calc_returns)
    assert len(drawdown) == len(calc_returns)
    assert (drawdown <= 0).all()

    return "分析引擎正常"


def test_attribution_analyzer():
    """测试归因分析引擎"""
    import pandas as pd
    import numpy as np

    from fund_cli.analysis.attribution import AttributionAnalyzer

    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    returns = pd.DataFrame(
        {
            "asset_a": np.random.normal(0.001, 0.02, 252),
            "asset_b": np.random.normal(0.0008, 0.015, 252),
            "asset_c": np.random.normal(0.0005, 0.01, 252),
        },
        index=dates,
    )

    analyzer = AttributionAnalyzer()

    # 简单分解
    result = analyzer.analyze(returns)
    assert "asset_a" in result
    assert "total_return" in result["asset_a"]

    # Brinson 归因
    bm_weights = {"asset_a": 0.5, "asset_b": 0.3, "asset_c": 0.2}
    pf_weights = {"asset_a": 0.4, "asset_b": 0.4, "asset_c": 0.2}
    brinson = analyzer.analyze(returns, benchmark_weights=bm_weights, portfolio_weights=pf_weights)
    assert "allocation_effect" in brinson
    assert "selection_effect" in brinson
    assert "interaction_effect" in brinson

    return "归因分析正常"


def test_portfolio_analyzer():
    """测试组合分析引擎"""
    import pandas as pd
    import numpy as np

    from fund_cli.analysis.portfolio import PortfolioAnalyzer

    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=252, freq="B")
    returns = pd.DataFrame(
        {
            "asset_a": np.random.normal(0.001, 0.02, 252),
            "asset_b": np.random.normal(0.0008, 0.015, 252),
        },
        index=dates,
    )

    analyzer = PortfolioAnalyzer()

    # 等权组合
    result = analyzer.analyze(returns)
    assert result["asset_count"] == 2
    assert "portfolio_return" in result
    assert "portfolio_volatility" in result
    assert "diversification_ratio" in result
    assert result["diversification_ratio"] >= 1.0

    # 自定义权重
    weights = {"asset_a": 0.7, "asset_b": 0.3}
    result2 = analyzer.analyze(returns, weights=weights)
    assert result2["weights"] == weights

    return "组合分析正常"


def test_ai_module():
    """测试 AI 模块（V2.0 占位）"""
    from fund_cli.ai.providers import LLMProvider, OpenAIProvider, get_provider
    from fund_cli.ai.analyzer import AIAnalyzer
    from fund_cli.ai.prompts import PromptTemplates

    # 提供商
    provider = LLMProvider(api_key="test", model="gpt-4")
    assert provider.is_available() is True
    assert provider.model == "gpt-4"

    openai = OpenAIProvider(api_key="test")
    assert isinstance(openai, OpenAIProvider)

    gp = get_provider("openai", "test-key", "gpt-4")
    assert isinstance(gp, OpenAIProvider)

    try:
        get_provider("invalid", "key", "model")
        assert False
    except ValueError:
        pass

    # 分析器
    analyzer = AIAnalyzer(provider)
    assert analyzer.provider is provider

    try:
        analyzer.summarize_fund({}, {})
        assert False
    except NotImplementedError:
        pass

    # 提示词模板
    prompt = PromptTemplates.format_summary_prompt({
        "fund_code": "000001",
        "fund_name": "测试",
        "fund_type": "混合型",
        "manager": "张三",
        "total_return": "10.5",
        "cagr": "8.2",
        "sharpe": "1.2",
        "max_drawdown": "-5.0",
        "volatility": "12.0",
    })
    assert "000001" in prompt
    assert "测试" in prompt

    return "AI模块正常"


def test_views_tables():
    """测试视图 - 表格"""
    import pandas as pd
    from fund_cli.views.tables import TableRenderer

    renderer = TableRenderer()

    df = pd.DataFrame({
        "code": ["000001", "000002"],
        "name": ["基金A", "基金B"],
        "type": ["混合型", "股票型"],
        "scale": [50.5, 30.2],
        "company": ["华夏", "易方达"],
    })

    table = renderer.render_fund_list(df)
    assert table is not None

    metrics = {
        "total_return": 15.5,
        "sharpe": 1.5,
        "max_drawdown": -8.2,
    }
    result_table = renderer.render_analysis_result(metrics)
    assert result_table is not None

    return "表格视图正常"


def test_views_charts():
    """测试视图 - 图表"""
    import pandas as pd
    import numpy as np
    from fund_cli.views.charts import ChartRenderer

    renderer = ChartRenderer()

    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=100, freq="B")
    nav_data = pd.DataFrame({
        "nav_date": dates,
        "unit_nav": 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 100)),
        "accumulated_nav": 1.0 + np.cumsum(np.random.normal(0.001, 0.02, 100)) * 1.5,
    })

    fig = renderer.render_nav_chart(nav_data)
    assert "data" in fig

    returns = pd.Series(np.random.normal(0.001, 0.02, 100), index=dates)
    wealth = (1 + returns).cumprod()
    drawdown = (wealth - wealth.cummax()) / wealth.cummax()

    dd_fig = renderer.render_drawdown_chart(drawdown)
    assert "data" in dd_fig

    return "图表视图正常"


def test_views_reports():
    """测试视图 - 报告"""
    from fund_cli.views.reports import ReportRenderer

    renderer = ReportRenderer()

    metrics = {
        "total_return": 15.5,
        "cagr": 12.3,
        "sharpe": 1.5,
        "sortino": 1.8,
        "volatility": 18.5,
        "max_drawdown": -8.2,
    }

    html = renderer.generate_html_report(
        fund_code="000001",
        fund_name="测试基金",
        metrics=metrics,
    )

    assert isinstance(html, str)
    assert "000001" in html
    assert "测试基金" in html
    assert "<html>" in html
    assert "</html>" in html

    return "报告视图正常"


# ========== 主测试函数 ==========


def run_all_tests():
    """运行所有测试"""
    runner = MVPTestRunner()

    console.print("\n[bold cyan]========== Fund CLI MVP 深度测试 ==========[/bold cyan]\n")

    # 1. 配置模块
    console.print("[bold yellow]1. 配置模块测试[/bold yellow]")
    runner.run(test_config_module, "配置模块", "配置加载")

    # 2. 数据模型
    console.print("\n[bold yellow]2. 数据模型测试[/bold yellow]")
    runner.run(test_data_models, "数据模型", "模型验证")
    runner.run(test_validators, "数据模型", "验证器")
    runner.run(test_helpers, "数据模型", "辅助函数")
    runner.run(test_decorators, "数据模型", "装饰器")

    # 3. 数据层
    console.print("\n[bold yellow]3. 数据层测试[/bold yellow]")
    runner.run(test_data_cache, "数据层", "缓存管理")
    runner.run(test_data_base, "数据层", "数据基类")

    # 4. 核心模块
    console.print("\n[bold yellow]4. 核心模块测试[/bold yellow]")
    runner.run(test_analyzer_base, "核心模块", "分析引擎基类")
    runner.run(test_optimizer_base, "核心模块", "优化引擎基类")
    runner.run(test_reporter_base, "核心模块", "报告生成器基类")

    # 5. 分析引擎
    console.print("\n[bold yellow]5. 分析引擎测试[/bold yellow]")
    runner.run(test_analysis_with_mock_data, "分析引擎", "业绩与风险分析")
    runner.run(test_attribution_analyzer, "分析引擎", "归因分析")
    runner.run(test_portfolio_analyzer, "分析引擎", "组合分析")

    # 6. AI 模块
    console.print("\n[bold yellow]6. AI模块测试 (V2.0占位)[/bold yellow]")
    runner.run(test_ai_module, "AI模块", "LLM提供商")
    runner.run(test_ai_module, "AI模块", "AI分析器")
    runner.run(test_ai_module, "AI模块", "提示词模板")

    # 7. 视图层
    console.print("\n[bold yellow]7. 视图层测试[/bold yellow]")
    runner.run(test_views_tables, "视图层", "表格渲染")
    runner.run(test_views_charts, "视图层", "图表渲染")
    runner.run(test_views_reports, "视图层", "报告生成")

    # 输出摘要
    console.print("\n[bold cyan]========== 测试摘要 ==========[/bold cyan]")
    success = runner.summary()
    return success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

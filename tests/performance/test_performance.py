"""
性能测试

测试核心模块的性能表现，确保优化后的代码满足性能要求。
"""
import time


class TestDataNormalizerPerformance:
    """DataNormalizer 性能测试"""

    def test_normalize_fund_code_performance(self):
        """测试基金代码标准化性能"""
        from fund_cli.data.normalizer import DataNormalizer

        start = time.time()
        for _i in range(1000):
            DataNormalizer.normalize_fund_code("000001.OF")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"标准化1000次基金代码耗时 {elapsed:.2f}s，超过1秒"

    def test_normalize_fund_code_cached_performance(self):
        """测试带缓存的基金代码标准化性能"""
        from fund_cli.data.normalizer import DataNormalizer

        # 预热缓存
        for i in range(100):
            DataNormalizer.normalize_fund_code_cached(f"{i:06d}.OF")

        start = time.time()
        for _i in range(1000):
            DataNormalizer.normalize_fund_code_cached("000001.OF")
        elapsed = time.time() - start

        # 缓存后应该非常快
        assert elapsed < 0.01, f"缓存标准化1000次耗时 {elapsed:.4f}s，超过0.01秒"

    def test_normalize_date_performance(self):
        """测试日期标准化性能"""
        from fund_cli.data.normalizer import DataNormalizer

        start = time.time()
        for _i in range(1000):
            DataNormalizer.normalize_date("2024-01-01")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"标准化1000次日期耗时 {elapsed:.2f}s，超过1秒"

    def test_normalize_date_cached_performance(self):
        """测试带缓存的日期标准化性能"""
        from fund_cli.data.normalizer import DataNormalizer

        # 预热缓存
        DataNormalizer.normalize_date_cached("2024-01-01")

        start = time.time()
        for _i in range(1000):
            DataNormalizer.normalize_date_cached("2024-01-01")
        elapsed = time.time() - start

        # 缓存后应该非常快
        assert elapsed < 0.01, f"缓存标准化1000次日期耗时 {elapsed:.4f}s，超过0.01秒"


class TestTemplateEnginePerformance:
    """TemplateEngine 性能测试"""

    def test_template_engine_initialization(self):
        """测试模板引擎初始化性能"""
        from fund_cli.core.template_engine import TemplateEngine

        start = time.time()
        TemplateEngine()
        elapsed = time.time() - start

        assert elapsed < 1.0, f"模板引擎初始化耗时 {elapsed:.2f}s，超过1秒"

    def test_render_string_performance(self):
        """测试模板字符串渲染性能"""
        from fund_cli.core.template_engine import TemplateEngine

        engine = TemplateEngine()

        start = time.time()
        for _i in range(100):
            engine.render_string("{{ name }}", name="test")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"渲染100次耗时 {elapsed:.2f}s，超过1秒"

    def test_render_complex_template_performance(self):
        """测试复杂模板渲染性能"""
        from fund_cli.core.template_engine import TemplateEngine

        engine = TemplateEngine()
        template = """
        {% for item in items %}
            {{ item.name }}: {{ item.value }}
        {% endfor %}
        """
        items = [{"name": f"item_{i}", "value": i} for i in range(100)]

        start = time.time()
        for _i in range(10):
            engine.render_string(template, items=items)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"复杂模板渲染10次耗时 {elapsed:.2f}s，超过1秒"


class TestAIAnalyzerPerformance:
    """AIAnalyzer 性能测试"""

    def test_analyze_fund_performance(self):
        """测试基金分析性能"""
        from fund_cli.core.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        metrics = {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.1,
            "volatility": 0.2,
        }

        start = time.time()
        for _i in range(10):
            result = analyzer.analyze_fund("000001", "测试基金", metrics)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"分析10次耗时 {elapsed:.2f}s，超过1秒"
        assert result.summary != ""

    def test_analyze_fund_cached_performance(self):
        """测试带缓存的基金分析性能"""
        from fund_cli.core.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer()
        metrics = {
            "total_return": 0.15,
            "sharpe_ratio": 1.2,
            "max_drawdown": -0.1,
            "volatility": 0.2,
        }

        # 第一次分析（无缓存）
        analyzer.analyze_fund("000001", "测试基金", metrics)

        # 第二次分析（有缓存）
        start = time.time()
        for _i in range(100):
            analyzer.analyze_fund("000001", "测试基金", metrics)
        elapsed = time.time() - start

        # 缓存后应该非常快
        assert elapsed < 0.1, f"缓存分析100次耗时 {elapsed:.4f}s，超过0.1秒"


class TestDataGatewayPerformance:
    """DataSourceGateway 性能测试"""

    def test_gateway_initialization(self):
        """测试网关初始化性能"""
        from fund_cli.core.data_gateway import DataSourceGateway

        start = time.time()
        DataSourceGateway()
        elapsed = time.time() - start

        assert elapsed < 1.0, f"网关初始化耗时 {elapsed:.2f}s，超过1秒"

    def test_cache_operations(self):
        """测试缓存操作性能"""
        from fund_cli.core.data_gateway import DataSourceGateway

        gateway = DataSourceGateway()

        # 测试缓存设置
        start = time.time()
        for i in range(1000):
            gateway._set_cache(f"key_{i}", f"value_{i}")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"设置1000个缓存耗时 {elapsed:.2f}s，超过1秒"

        # 测试缓存获取
        start = time.time()
        for i in range(1000):
            gateway._get_from_cache(f"key_{i}")
        elapsed = time.time() - start

        assert elapsed < 1.0, f"获取1000个缓存耗时 {elapsed:.2f}s，超过1秒"


class TestOverallPerformance:
    """整体性能测试"""

    def test_import_performance(self):
        """测试模块导入性能"""
        start = time.time()
        elapsed = time.time() - start

        assert elapsed < 3.0, f"导入核心模块耗时 {elapsed:.2f}s，超过3秒"

    def test_end_to_end_performance(self):
        """测试端到端性能"""
        from fund_cli.core.ai_analyzer import AIAnalyzer
        from fund_cli.core.template_engine import TemplateEngine
        from fund_cli.data.normalizer import DataNormalizer

        start = time.time()

        # 数据标准化
        for i in range(100):
            DataNormalizer.normalize_fund_code(f"{i:06d}.OF")

        # 模板渲染
        engine = TemplateEngine()
        for _i in range(10):
            engine.render_string("{{ name }}", name="test")

        # AI分析
        analyzer = AIAnalyzer()
        metrics = {"total_return": 0.15, "sharpe_ratio": 1.2}
        analyzer.analyze_fund("000001", "测试基金", metrics)

        elapsed = time.time() - start

        assert elapsed < 2.0, f"端到端测试耗时 {elapsed:.2f}s，超过2秒"

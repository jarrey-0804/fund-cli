"""TemplateEngine 模板引擎单元测试"""

from datetime import date

import pytest

from fund_cli.core.template_engine import TemplateEngine, get_template_engine


@pytest.fixture
def engine():
    """创建模板引擎实例"""
    return TemplateEngine()


@pytest.fixture
def single_fund_context():
    """单只基金报告的完整上下文数据"""
    return {
        "title": "000001 华夏成长 - 基金研究报告",
        "fund_code": "000001",
        "fund_name": "华夏成长",
        "fund_type": "混合型",
        "found_date": "2001-12-18",
        "performance_metrics": [
            {"name": "总收益率", "value": 0.255, "comment": "优秀"},
            {"name": "年化收益率", "value": 0.082, "comment": "良好"},
            {"name": "波动率", "value": 0.153, "comment": "中等"},
            {"name": "夏普比率", "value": 0.45, "comment": "良好"},
            {"name": "最大回撤", "value": -0.125, "comment": "需关注"},
        ],
        "risk_metrics": [
            {"name": "年化波动率", "value": 0.153},
            {"name": "最大回撤", "value": -0.125},
            {"name": "VaR(95%)", "value": -0.025},
        ],
        "asset_allocation": [
            {"name": "股票", "ratio": 0.75},
            {"name": "债券", "ratio": 0.15},
            {"name": "现金", "ratio": 0.10},
        ],
        "top_holdings": [
            {"code": "600519", "name": "贵州茅台", "proportion": 0.095},
            {"code": "000858", "name": "五粮液", "proportion": 0.062},
            {"code": "601318", "name": "中国平安", "proportion": 0.051},
        ],
    }


@pytest.fixture
def portfolio_context():
    """投资组合报告的完整上下文数据"""
    return {
        "title": "投资组合分析报告",
        "total_asset": "1,000,000.00",
        "funds": [
            {
                "code": "000001",
                "name": "华夏成长",
                "type": "混合型",
                "weight": 0.40,
                "return_1y": 0.255,
            },
            {
                "code": "000002",
                "name": "华夏回报",
                "type": "混合型",
                "weight": 0.35,
                "return_1y": -0.032,
            },
            {
                "code": "110011",
                "name": "易方达中小盘",
                "type": "股票型",
                "weight": 0.25,
                "return_1y": 0.128,
            },
        ],
        "portfolio_metrics": [
            {"name": "组合收益率", "portfolio": 0.128, "benchmark": 0.095},
            {"name": "夏普比率", "portfolio": 0.65, "benchmark": 0.42},
        ],
        "risk_metrics": [
            {"name": "组合波动率", "value": 0.12},
            {"name": "最大回撤", "value": -0.08},
        ],
    }


class TestTemplateEngineInit:
    """TemplateEngine 初始化测试"""

    def test_create_instance(self, engine):
        """测试创建TemplateEngine实例"""
        assert engine is not None
        assert hasattr(engine, "_env")

    def test_default_template_dirs(self, engine):
        """测试默认模板目录配置"""
        # 默认模板目录应包含项目模板
        loader = engine._env.loader
        assert loader is not None
        # 验证可以找到模板文件
        templates = engine.list_templates()
        assert len(templates) > 0

    def test_custom_template_dirs(self, tmp_path):
        """测试自定义模板目录"""
        (tmp_path / "test.html").write_text("<html>{{ msg }}</html>")
        engine = TemplateEngine(template_dirs=[str(tmp_path)])
        result = engine.render("test.html", msg="hello")
        assert "hello" in result


class TestCustomFilters:
    """自定义过滤器测试"""

    def test_percentage_filter_positive(self, engine):
        """测试percentage过滤器 - 正值"""
        result = engine.render_string("{{ value | percentage }}", value=0.255)
        assert "25.50%" in result

    def test_percentage_filter_negative(self, engine):
        """测试percentage过滤器 - 负值"""
        result = engine.render_string("{{ value | percentage }}", value=-0.125)
        assert "-12.50%" in result

    def test_percentage_filter_decimals(self, engine):
        """测试percentage过滤器 - 自定义小数位"""
        result = engine.render_string("{{ value | percentage(1) }}", value=0.255)
        assert "25.5%" in result

    def test_percentage_filter_none(self, engine):
        """测试percentage过滤器 - None值"""
        result = engine.render_string("{{ value | percentage }}", value=None)
        assert "N/A" in result

    def test_format_number_filter(self, engine):
        """测试format_number过滤器"""
        result = engine.render_string("{{ value | format_number }}", value=3.14159265)
        assert "3.1416" in result

    def test_format_number_filter_decimals(self, engine):
        """测试format_number过滤器 - 自定义小数位"""
        result = engine.render_string("{{ value | format_number(2) }}", value=3.14159)
        assert "3.14" in result

    def test_format_number_filter_none(self, engine):
        """测试format_number过滤器 - None值"""
        result = engine.render_string("{{ value | format_number }}", value=None)
        assert "N/A" in result

    def test_color_class_positive(self, engine):
        """测试color_class过滤器 - 正值"""
        result = engine.render_string("{{ value | color_class }}", value=0.5)
        assert "positive" in result

    def test_color_class_negative(self, engine):
        """测试color_class过滤器 - 负值"""
        result = engine.render_string("{{ value | color_class }}", value=-0.5)
        assert "negative" in result

    def test_color_class_zero(self, engine):
        """测试color_class过滤器 - 零值"""
        result = engine.render_string("{{ value | color_class }}", value=0)
        assert result.strip() == ""

    def test_color_class_none(self, engine):
        """测试color_class过滤器 - None值"""
        result = engine.render_string("{{ value | color_class }}", value=None)
        assert result.strip() == ""


class TestRenderString:
    """render_string 字符串模板渲染测试"""

    def test_render_simple_string(self, engine):
        """测试渲染简单字符串模板"""
        result = engine.render_string("Hello, {{ name }}!", name="World")
        assert result == "Hello, World!"

    def test_render_with_filter(self, engine):
        """测试字符串模板中使用过滤器"""
        result = engine.render_string(
            "收益率: {{ value | percentage }}", value=0.082
        )
        assert "8.20%" in result

    def test_render_with_loop(self, engine):
        """测试字符串模板中使用循环"""
        result = engine.render_string(
            "{% for item in items %}{{ item }}{% endfor %}",
            items=["A", "B", "C"],
        )
        assert result == "ABC"

    def test_render_with_condition(self, engine):
        """测试字符串模板中使用条件判断"""
        result = engine.render_string(
            "{% if show %}visible{% else %}hidden{% endif %}",
            show=True,
        )
        assert result == "visible"


class TestListTemplates:
    """list_templates 模板列表测试"""

    def test_list_all_templates(self, engine):
        """测试列出所有可用模板，应返回5个模板"""
        templates = engine.list_templates()
        assert len(templates) == 5

    def test_list_templates_contains_base(self, engine):
        """测试模板列表包含base.html"""
        templates = engine.list_templates()
        assert "base.html" in templates

    def test_list_templates_contains_single_fund(self, engine):
        """测试模板列表包含single_fund/report.html"""
        templates = engine.list_templates()
        assert "single_fund/report.html" in templates

    def test_list_templates_contains_portfolio(self, engine):
        """测试模板列表包含portfolio/report.html"""
        templates = engine.list_templates()
        assert "portfolio/report.html" in templates

    def test_list_templates_contains_market_flow(self, engine):
        """测试模板列表包含market_flow/report.html"""
        templates = engine.list_templates()
        assert "market_flow/report.html" in templates

    def test_list_templates_contains_risk_control(self, engine):
        """测试模板列表包含risk_control/report.html"""
        templates = engine.list_templates()
        assert "risk_control/report.html" in templates

    def test_list_templates_filter_by_directory(self, engine):
        """测试按目录过滤模板列表"""
        templates = engine.list_templates(directory="single_fund")
        assert len(templates) == 1
        assert "single_fund/report.html" in templates


class TestRenderBaseTemplate:
    """base.html 模板渲染测试"""

    def test_render_base_with_title(self, engine):
        """测试渲染base.html并传入title"""
        result = engine.render("base.html", title="测试报告")
        assert "测试报告" in result
        assert "<!DOCTYPE html>" in result

    def test_render_base_has_css(self, engine):
        """测试base.html包含CSS样式"""
        result = engine.render("base.html", title="测试")
        assert "@page" in result
        assert ".positive" in result
        assert ".negative" in result

    def test_render_base_has_blocks(self, engine):
        """测试base.html渲染后包含header和footer区块内容"""
        result = engine.render("base.html", title="测试")
        # block标签在渲染后消失，验证渲染后的实际内容
        assert "<h1>" in result  # header block 渲染的标题
        assert "<body>" in result
        assert "footer" in result  # footer block 渲染的页脚

    def test_render_base_has_footer(self, engine):
        """测试base.html包含页脚信息"""
        result = engine.render("base.html", title="测试")
        assert "Fund CLI" in result


class TestRenderSingleFundTemplate:
    """single_fund/report.html 模板渲染测试"""

    def test_render_single_fund(self, engine, single_fund_context):
        """测试渲染单只基金报告"""
        result = engine.render("single_fund/report.html", **single_fund_context)
        assert "000001" in result
        assert "华夏成长" in result
        assert "混合型" in result

    def test_single_fund_has_performance_table(self, engine, single_fund_context):
        """测试单只基金报告包含绩效指标表"""
        result = engine.render("single_fund/report.html", **single_fund_context)
        assert "核心绩效指标" in result
        assert "总收益率" in result

    def test_single_fund_has_risk_table(self, engine, single_fund_context):
        """测试单只基金报告包含风险指标表"""
        result = engine.render("single_fund/report.html", **single_fund_context)
        assert "风险指标" in result

    def test_single_fund_has_asset_allocation(self, engine, single_fund_context):
        """测试单只基金报告包含资产配置"""
        result = engine.render("single_fund/report.html", **single_fund_context)
        assert "资产配置" in result
        assert "75.00%" in result  # 股票占比

    def test_single_fund_has_top_holdings(self, engine, single_fund_context):
        """测试单只基金报告包含前十大重仓股"""
        result = engine.render("single_fund/report.html", **single_fund_context)
        assert "前十大重仓股" in result
        assert "贵州茅台" in result
        assert "600519" in result

    def test_single_fund_color_classes(self, engine, single_fund_context):
        """测试单只基金报告正确应用颜色类"""
        result = engine.render("single_fund/report.html", **single_fund_context)
        assert "positive" in result  # 总收益率为正
        assert "negative" in result  # 最大回撤为负


class TestRenderPortfolioTemplate:
    """portfolio/report.html 模板渲染测试"""

    def test_render_portfolio(self, engine, portfolio_context):
        """测试渲染投资组合报告"""
        result = engine.render("portfolio/report.html", **portfolio_context)
        assert "投资组合" in result
        assert "000001" in result
        assert "000002" in result

    def test_portfolio_has_holdings_table(self, engine, portfolio_context):
        """测试组合报告包含持仓表"""
        result = engine.render("portfolio/report.html", **portfolio_context)
        assert "组合持仓" in result
        assert "华夏成长" in result
        assert "华夏回报" in result

    def test_portfolio_has_performance_table(self, engine, portfolio_context):
        """测试组合报告包含绩效表"""
        result = engine.render("portfolio/report.html", **portfolio_context)
        assert "组合绩效" in result

    def test_portfolio_has_risk_table(self, engine, portfolio_context):
        """测试组合报告包含风险分析表"""
        result = engine.render("portfolio/report.html", **portfolio_context)
        assert "风险分析" in result

    def test_portfolio_weight_percentage(self, engine, portfolio_context):
        """测试组合报告正确显示权重百分比"""
        result = engine.render("portfolio/report.html", **portfolio_context)
        assert "40.00%" in result  # 第一只基金权重
        assert "35.00%" in result  # 第二只基金权重

    def test_portfolio_return_color(self, engine, portfolio_context):
        """测试组合报告正确处理收益率颜色"""
        result = engine.render("portfolio/report.html", **portfolio_context)
        assert "positive" in result  # 000001收益为正
        assert "negative" in result  # 000002收益为负


class TestGetTemplate:
    """get_template 获取模板对象测试"""

    def test_get_template_returns_template(self, engine):
        """测试get_template返回模板对象"""
        template = engine.get_template("base.html")
        assert template is not None
        assert hasattr(template, "render")

    def test_get_template_and_render(self, engine):
        """测试获取模板后渲染"""
        template = engine.get_template("base.html")
        result = template.render(title="测试标题")
        assert "测试标题" in result


class TestGlobalVariables:
    """全局变量测试"""

    def test_today_global(self, engine):
        """测试today全局变量"""
        result = engine.render_string("{{ today }}")
        assert str(date.today()) in result

    def test_now_global(self, engine):
        """测试now()全局函数"""
        result = engine.render_string("{{ now() }}")
        expected = date.today().strftime("%Y-%m-%d")
        assert expected in result


class TestGetTemplateEngineSingleton:
    """get_template_engine 单例测试"""

    def test_singleton_returns_instance(self):
        """测试get_template_engine返回TemplateEngine实例"""
        engine = get_template_engine()
        assert isinstance(engine, TemplateEngine)

    def test_singleton_same_instance(self):
        """测试get_template_engine返回同一实例"""
        engine1 = get_template_engine()
        engine2 = get_template_engine()
        assert engine1 is engine2

    def test_singleton_can_render(self):
        """测试单例实例可以正常渲染模板"""
        engine = get_template_engine()
        result = engine.render("base.html", title="单例测试")
        assert "单例测试" in result

    def test_reset_singleton(self):
        """测试重置单例后获取新实例"""
        import fund_cli.core.template_engine as te_module

        engine1 = get_template_engine()
        te_module._engine = None
        engine2 = get_template_engine()
        # 重置后应该是新实例（不是同一个对象）
        assert engine1 is not engine2
        # 清理：恢复单例
        te_module._engine = engine1

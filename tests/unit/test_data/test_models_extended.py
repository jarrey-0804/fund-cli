"""扩展数据模型测试"""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from fund_cli.data.models import (
    FundFilter,
    FundManager,
    HoldingInfo,
    HoldingSnapshot,
    MonitorRule,
    OptimizationConstraint,
    OutputConfig,
)


class TestHoldingInfo:
    def test_create_valid(self):
        h = HoldingInfo(
            fund_code="000001",
            report_date=date(2024, 6, 30),
            stock_code="600519",
            stock_name="贵州茅台",
            weight=9.5,
        )
        assert h.fund_code == "000001"
        assert h.weight == 9.5

    def test_weight_validation(self):
        with pytest.raises(ValidationError):
            HoldingInfo(
                fund_code="000001",
                report_date=date(2024, 6, 30),
                stock_code="600519",
                stock_name="贵州茅台",
                weight=101,
            )

    def test_optional_fields(self):
        h = HoldingInfo(
            fund_code="000001",
            report_date=date(2024, 6, 30),
            stock_code="600519",
            stock_name="贵州茅台",
            weight=5.0,
        )
        assert h.market_value is None
        assert h.industry is None


class TestFundManager:
    def test_create_valid(self):
        m = FundManager(name="张三", fund_code="000001")
        assert m.name == "张三"

    def test_empty_name_raises(self):
        with pytest.raises(ValidationError):
            FundManager(name="", fund_code="000001")

    def test_optional_fields(self):
        m = FundManager(
            name="张三",
            fund_code="000001",
            start_date=date(2020, 1, 1),
            tenure_days=1500,
            total_return=20.5,
            annual_return=8.0,
        )
        assert m.tenure_days == 1500


class TestHoldingSnapshot:
    def test_create_valid(self):
        s = HoldingSnapshot(
            fund_code="000001",
            report_date=date(2024, 6, 30),
            total_stock_count=50,
            top10_weight=45.5,
            industry_distribution={"食品饮料": 20.0, "银行": 15.0},
        )
        assert s.total_stock_count == 50
        assert len(s.industry_distribution) == 2


class TestOptimizationConstraint:
    def test_defaults(self):
        c = OptimizationConstraint()
        assert c.min_weight == 0.0
        assert c.max_weight == 1.0
        assert c.target_return is None

    def test_custom_values(self):
        c = OptimizationConstraint(min_weight=0.05, max_weight=0.3, target_return=0.1)
        assert c.min_weight == 0.05

    def test_invalid_weight(self):
        with pytest.raises(ValidationError):
            OptimizationConstraint(min_weight=-0.1)


class TestMonitorRule:
    def test_create_valid(self):
        r = MonitorRule(fund_code="000001", rule_type="nav_change", threshold=-3.0)
        assert r.enabled is True
        assert isinstance(r.created_at, datetime)

    def test_disabled(self):
        r = MonitorRule(fund_code="000001", enabled=False)
        assert r.enabled is False


class TestOutputConfig:
    def test_defaults(self):
        c = OutputConfig()
        assert c.default_format == "table"
        assert c.csv_encoding == "utf-8-sig"
        assert c.number_decimal == 2


class TestFundFilterExtended:
    def test_new_fields(self):
        f = FundFilter(fee_rate_max=1.5, manager_name="张三", min_rating=3)
        assert f.fee_rate_max == 1.5
        assert f.manager_name == "张三"
        assert f.min_rating == 3

    def test_rating_validation(self):
        with pytest.raises(ValidationError):
            FundFilter(min_rating=6)

    def test_rating_min(self):
        with pytest.raises(ValidationError):
            FundFilter(min_rating=0)

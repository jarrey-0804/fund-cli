"""
数据质量趋势分析器测试.

验证质量趋势分析功能。
"""

import json
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from fund_cli.core.quality_trend_analyzer import (
    QualityTrend,
    QualityTrendAnalyzer,
    get_quality_trend_analyzer,
)


class TestQualityTrend(unittest.TestCase):
    """测试质量趋势数据类."""

    def test_trend_creation(self):
        """测试创建趋势记录."""
        trend = QualityTrend(
            fund_code="000001",
            date=datetime.now(),
            quality_score=85.0,
            quality_level="good",
            error_count=0,
            warning_count=2,
            trend="stable",
        )

        self.assertEqual(trend.fund_code, "000001")
        self.assertEqual(trend.quality_score, 85.0)
        self.assertEqual(trend.trend, "stable")


class TestQualityTrendAnalyzer(unittest.TestCase):
    """测试质量趋势分析器."""

    def setUp(self):
        """设置测试环境."""
        self.temp_dir = TemporaryDirectory()
        self.analyzer = QualityTrendAnalyzer(audit_log_dir=self.temp_dir.name)

    def tearDown(self):
        """清理测试环境."""
        self.temp_dir.cleanup()

    def _create_test_log_file(self, records):
        """创建测试日志文件."""
        log_file = Path(self.temp_dir.name) / "audit_2024.jsonl"
        with open(log_file, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

    def test_load_quality_logs_empty(self):
        """测试加载空日志."""
        df = self.analyzer.load_quality_logs()
        self.assertTrue(df.empty)

    def test_load_quality_logs_with_data(self):
        """测试加载有数据的日志."""
        records = [
            {
                "type": "quality_check",
                "timestamp": datetime.now().isoformat(),
                "fund_code": "000001",
                "quality_score": 85.0,
                "quality_level": "good",
                "blocked": False,
                "details": {},
            },
            {
                "type": "quality_check",
                "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                "fund_code": "000002",
                "quality_score": 70.0,
                "quality_level": "warning",
                "blocked": False,
                "details": {},
            },
        ]
        self._create_test_log_file(records)

        df = self.analyzer.load_quality_logs()

        self.assertEqual(len(df), 2)
        self.assertIn("000001", df["fund_code"].values)
        self.assertIn("000002", df["fund_code"].values)

    def test_load_quality_logs_with_filter(self):
        """测试带过滤的日志加载."""
        now = datetime.now()
        records = [
            {
                "type": "quality_check",
                "timestamp": now.isoformat(),
                "fund_code": "000001",
                "quality_score": 85.0,
                "quality_level": "good",
                "blocked": False,
            },
            {
                "type": "quality_check",
                "timestamp": (now - timedelta(days=10)).isoformat(),
                "fund_code": "000002",
                "quality_score": 70.0,
                "quality_level": "warning",
                "blocked": False,
            },
        ]
        self._create_test_log_file(records)

        # 按基金代码过滤
        df = self.analyzer.load_quality_logs(fund_code="000001")
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["fund_code"], "000001")

        # 按日期过滤
        start_date = now - timedelta(days=5)
        df = self.analyzer.load_quality_logs(start_date=start_date)
        self.assertEqual(len(df), 1)

    def test_analyze_trend_no_data(self):
        """测试无数据时的趋势分析."""
        result = self.analyzer.analyze_trend("000001", days=30)

        self.assertEqual(result["fund_code"], "000001")
        self.assertFalse(result["has_data"])
        self.assertIn("message", result)

    def test_analyze_trend_with_data(self):
        """测试有数据时的趋势分析."""
        now = datetime.now()
        records = [
            {
                "type": "quality_check",
                "timestamp": (now - timedelta(days=i)).isoformat(),
                "fund_code": "000001",
                "quality_score": 80.0 + (9 - i) * 2,  # 逐渐改善（越早分数越低）
                "quality_level": "good",
                "blocked": False,
            }
            for i in range(10)
        ]
        self._create_test_log_file(records)

        result = self.analyzer.analyze_trend("000001", days=30)

        self.assertTrue(result["has_data"])
        self.assertEqual(result["fund_code"], "000001")
        self.assertEqual(result["check_count"], 10)
        self.assertEqual(result["trend"], "improving")
        self.assertIn("avg_score", result)
        self.assertIn("recommendation", result)

    def test_analyze_trend_deteriorating(self):
        """测试下降趋势检测."""
        now = datetime.now()
        records = [
            {
                "type": "quality_check",
                "timestamp": (now - timedelta(days=i)).isoformat(),
                "fund_code": "000001",
                "quality_score": 90.0 - (9 - i) * 3,  # 逐渐下降（越早分数越高）
                "quality_level": "warning" if i > 5 else "good",
                "blocked": False,
            }
            for i in range(10)
        ]
        self._create_test_log_file(records)

        result = self.analyzer.analyze_trend("000001", days=30)

        self.assertEqual(result["trend"], "deteriorating")

    def test_generate_recommendation(self):
        """测试建议生成."""
        rec = self.analyzer._generate_recommendation("stable", 80.0, 0)
        self.assertEqual(rec, "数据质量稳定")

        rec = self.analyzer._generate_recommendation("deteriorating", 80.0, 0)
        self.assertEqual(rec, "数据质量呈下降趋势，建议关注")

        rec = self.analyzer._generate_recommendation("stable", 60.0, 0)
        self.assertEqual(rec, "数据质量评分较低，建议优化")

        rec = self.analyzer._generate_recommendation("stable", 80.0, 1)
        self.assertEqual(rec, "数据质量问题严重，建议立即检查数据源")

    def test_detect_anomalies(self):
        """测试异常检测."""
        now = datetime.now()
        records = [
            {
                "type": "quality_check",
                "timestamp": now.isoformat(),
                "fund_code": "000001",
                "quality_score": 40.0,  # 低分
                "quality_level": "critical",
                "blocked": True,
            },
            {
                "type": "quality_check",
                "timestamp": (now - timedelta(days=1)).isoformat(),
                "fund_code": "000001",
                "quality_score": 85.0,
                "quality_level": "good",
                "blocked": False,
            },
        ]
        self._create_test_log_file(records)

        anomalies = self.analyzer.detect_anomalies(days=7, score_threshold=50.0)

        self.assertEqual(len(anomalies), 2)  # 低分 + 被拦截
        low_score_anomalies = [a for a in anomalies if a["type"] == "low_score"]
        blocked_anomalies = [a for a in anomalies if a["type"] == "blocked"]
        self.assertEqual(len(low_score_anomalies), 1)
        self.assertEqual(len(blocked_anomalies), 1)

    def test_get_summary_report_no_data(self):
        """测试无数据的汇总报告."""
        report = self.analyzer.get_summary_report(days=30)

        self.assertFalse(report["has_data"])

    def test_get_summary_report_with_data(self):
        """测试有数据的汇总报告."""
        now = datetime.now()
        records = [
            {
                "type": "quality_check",
                "timestamp": (now - timedelta(days=i % 5)).isoformat(),
                "fund_code": f"00000{i % 3 + 1}",
                "quality_score": 80.0 + i,
                "quality_level": "good",
                "blocked": i == 0,
            }
            for i in range(15)
        ]
        self._create_test_log_file(records)

        report = self.analyzer.get_summary_report(days=30)

        self.assertTrue(report["has_data"])
        self.assertEqual(report["total_checks"], 15)
        self.assertEqual(report["unique_funds"], 3)
        self.assertIn("overall_avg_score", report)
        self.assertIn("fund_stats", report)

    def test_get_quality_trend_analyzer_singleton(self):
        """测试全局单例."""
        analyzer1 = get_quality_trend_analyzer()
        analyzer2 = get_quality_trend_analyzer()
        self.assertIs(analyzer1, analyzer2)


if __name__ == "__main__":
    unittest.main()

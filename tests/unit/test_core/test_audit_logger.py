"""审计日志单元测试."""

import json
import pytest
from pathlib import Path
from fund_cli.core.audit_logger import AuditLogger


class TestAuditLogger:
    """AuditLogger 测试."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        self.log_dir = str(tmp_path / "audit_test")
        self.logger = AuditLogger(log_dir=self.log_dir)

    def test_log_quality_check(self):
        """测试记录质量检查日志."""
        log_id = self.logger.log_quality_check(
            fund_code="000001",
            quality_score=85.0,
            quality_level="good",
            blocked=False,
        )
        assert log_id is not None
        assert len(log_id) == 16

    def test_log_analysis(self):
        """测试记录分析操作日志."""
        log_id = self.logger.log_analysis(
            fund_code="000001",
            analysis_type="performance",
            metrics={"total_return": 10.0},
        )
        assert log_id is not None

    def test_log_report_generation(self):
        """测试记录报告生成日志."""
        log_id = self.logger.log_report_generation(
            fund_code="000001",
            report_type="single_fund",
            output_path="/tmp/report.html",
        )
        assert log_id is not None

    def test_get_logs(self):
        """测试查询日志."""
        self.logger.log_quality_check("000001", 85.0, "good", False)
        self.logger.log_quality_check("000002", 40.0, "poor", True)
        self.logger.log_analysis("000001", "performance", {"total_return": 10.0})

        # Query all
        logs = self.logger.get_logs()
        assert len(logs) == 3

        # Filter by operation
        quality_logs = self.logger.get_logs(operation="quality_check")
        assert len(quality_logs) == 2

        # Filter by fund_code
        fund_logs = self.logger.get_logs(fund_code="000001")
        assert len(fund_logs) == 2

    def test_log_file_persistence(self):
        """测试日志文件持久化."""
        self.logger.log_quality_check("000001", 90.0, "good", False)

        # Create new logger instance pointing to same dir
        logger2 = AuditLogger(log_dir=self.log_dir)
        logs = logger2.get_logs()
        assert len(logs) == 1

        # Verify JSON structure
        record = logs[0]
        assert "timestamp" in record
        assert "log_id" in record
        assert record["fund_code"] == "000001"

    def test_log_limit(self):
        """测试日志查询数量限制."""
        for i in range(10):
            self.logger.log_quality_check(f"00000{i}", 80.0, "good", False)

        logs = self.logger.get_logs(limit=5)
        assert len(logs) == 5

    def test_log_quality_check_with_details(self):
        """测试带详情的质量检查日志."""
        log_id = self.logger.log_quality_check(
            fund_code="000001",
            quality_score=85.0,
            quality_level="good",
            blocked=False,
            details={"error_count": 0, "warning_count": 1},
        )
        assert log_id is not None
        logs = self.logger.get_logs(fund_code="000001")
        assert logs[0]["details"]["error_count"] == 0

    def test_get_logs_empty(self):
        """测试空日志查询."""
        logger = AuditLogger(log_dir=str(Path(self.log_dir) / "empty"))
        logs = logger.get_logs()
        assert logs == []

    def test_log_analysis_filters_none_metrics(self):
        """测试分析日志过滤None值指标."""
        log_id = self.logger.log_analysis(
            fund_code="000001",
            analysis_type="performance",
            metrics={"total_return": 10.0, "sharpe_ratio": None},
        )
        assert log_id is not None
        logs = self.logger.get_logs(operation="analysis")
        assert "sharpe_ratio" not in logs[0]["metrics_summary"]
        assert "total_return" in logs[0]["metrics_summary"]

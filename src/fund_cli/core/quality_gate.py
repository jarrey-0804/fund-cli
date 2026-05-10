"""
数据质量门禁.

在分析流程入口强制执行数据质量检查。
"""

import logging

import pandas as pd

from fund_cli.core.data_quality import DataQualityChecker, QualityReport

logger = logging.getLogger(__name__)


class QualityGate:
    """
    数据质量门禁.

    在数据进入分析流程前执行质量检查，
    不达标的数据将被拦截并返回质量报告。
    """

    def __init__(self, data_manager=None):
        try:
            from fund_cli.config import get_config

            config = get_config()
            self._min_score = config.quality.min_quality_score
        except Exception:
            self._min_score = 60.0
        self._checker = DataQualityChecker(data_manager)
        self._audit_logger = None
        try:
            from fund_cli.core.audit_logger import get_audit_logger

            self._audit_logger = get_audit_logger()
        except Exception:
            pass

    def check(self, fund_code: str, nav_data: pd.DataFrame) -> QualityReport:
        """
        执行质量门禁检查.

        Args:
            fund_code: 基金代码
            nav_data: 净值数据

        Returns:
            质量报告，包含评分和是否阻止分析
        """
        report = self._checker.run_expectations(fund_code, nav_data)

        if report.blocked:
            logger.warning(
                "质量门禁拦截: 基金 %s 质量评分 %.0f/100 (%s), %d 个错误",
                fund_code,
                report.score,
                report.level,
                report.error_count,
            )
        elif report.level == "warning":
            logger.warning(
                "质量门禁警告: 基金 %s 质量评分 %.0f/100 (%s)",
                fund_code,
                report.score,
                report.level,
            )
        else:
            logger.info(
                "质量门禁通过: 基金 %s 质量评分 %.0f/100 (%s)",
                fund_code,
                report.score,
                report.level,
            )

        # 记录审计日志
        if self._audit_logger is not None:
            details = {
                "error_count": report.error_count,
                "warning_count": report.warning_count,
                "data_rows": len(nav_data) if nav_data is not None else 0,
            }
            self._audit_logger.log_quality_check(
                fund_code=fund_code,
                quality_score=report.score,
                quality_level=report.level,
                blocked=report.blocked,
                details=details,
            )

        return report

    def check_and_raise(self, fund_code: str, nav_data: pd.DataFrame) -> QualityReport:
        """
        执行质量门禁检查，不达标时抛出异常.

        Args:
            fund_code: 基金代码
            nav_data: 净值数据

        Returns:
            质量报告

        Raises:
            ValueError: 质量检查未通过且 blocked=True
        """
        report = self.check(fund_code, nav_data)

        if report.score < self._min_score:
            error_details = "; ".join(
                f"{r.name}: {r.message}"
                for r in report.results
                if not r.passed and r.severity == "error"
            )
            raise ValueError(f"数据质量检查未通过 (评分: {report.score:.0f}/100): {error_details}")

        return report

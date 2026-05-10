"""
报告完整性验证器.

验证报告生成前的数据完整性和合规性。
"""

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ReportValidationResult:
    """报告验证结果."""

    passed: bool
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    compliance_status: str = "unknown"  # pass, warning, fail


class ReportValidator:
    """
    报告完整性验证器.

    在报告生成前验证所有必需字段和合规要求。
    """

    # 必需字段列表
    REQUIRED_METRICS = [
        "total_return",
        "annualized_return",
        "volatility",
        "max_drawdown",
        "sharpe_ratio",
    ]

    # 风控报告必需字段
    RISK_REQUIRED_FIELDS = [
        "risk_overview",
        "concentration",
        "compliance_checks",
    ]

    def __init__(self):
        self._disclaimer_required = True

    def validate_metrics(
        self, metrics: dict, report_type: str = "single_fund"
    ) -> ReportValidationResult:
        """
        验证指标数据完整性.

        Args:
            metrics: 指标字典
            report_type: 报告类型

        Returns:
            验证结果
        """
        missing = []
        warnings = []

        # 检查必需指标
        for required_field in self.REQUIRED_METRICS:
            if required_field not in metrics or metrics[required_field] is None:
                missing.append(required_field)

        # 检查NaN比例
        nan_count = sum(
            1 for v in metrics.values() if v is None or (isinstance(v, float) and v != v)
        )
        if nan_count > len(metrics) * 0.3:
            warnings.append(f"NaN比例过高: {nan_count}/{len(metrics)}")

        # 风控报告额外检查 - 这些字段由 RiskControlReporter 生成，不需要在输入中检查
        # if report_type == "risk_control":
        #     for field in self.RISK_REQUIRED_FIELDS:
        #         if field not in metrics:
        #             missing.append(field)

        return ReportValidationResult(
            passed=len(missing) == 0,
            missing_fields=missing,
            warnings=warnings,
            compliance_status="pass" if len(missing) == 0 else "fail",
        )

    def validate_template_data(
        self, data: dict, template_path: str | None = None
    ) -> ReportValidationResult:
        """验证模板数据完整性."""
        missing = []
        warnings = []

        # 基本字段检查
        if "fund_code" not in data or not data["fund_code"]:
            missing.append("fund_code")

        if "report_date" not in data or not data["report_date"]:
            missing.append("report_date")

        # 风控模板数据检查
        if "risk_overview" in data:
            if not data["risk_overview"]:
                warnings.append("risk_overview为空")

        if "compliance_checks" in data:
            checks = data["compliance_checks"]
            if isinstance(checks, list):
                failed_checks = [c for c in checks if not c.get("passed", True)]
                if len(failed_checks) > len(checks) * 0.5:
                    warnings.append(f"合规检查失败率过高: {len(failed_checks)}/{len(checks)}")

        return ReportValidationResult(
            passed=len(missing) == 0,
            missing_fields=missing,
            warnings=warnings,
            compliance_status="warning" if warnings else "pass",
        )

    def check_disclaimer(self, content: str) -> bool:
        """检查是否包含免责声明."""
        disclaimer_keywords = [
            "仅供参考",
            "不构成投资建议",
            "投资有风险",
            "past performance",
        ]
        return any(kw in content for kw in disclaimer_keywords)

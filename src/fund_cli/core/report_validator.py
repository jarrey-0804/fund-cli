"""
报告完整性验证器.

验证报告生成前的数据完整性和合规性。
"""

import logging
from dataclasses import dataclass, field
from typing import Any

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

    def validate_template_variables(
        self,
        template_variables: dict[str, Any],
        required_schema: dict[str, type] | None = None,
    ) -> ReportValidationResult:
        """
        验证模板变量类型和范围.

        Args:
            template_variables: 模板变量字典
            required_schema: 必需字段类型定义，如 {"fund_code": str, "nav": float}

        Returns:
            验证结果
        """
        missing = []
        warnings = []

        # 默认schema
        if required_schema is None:
            required_schema = {
                "fund_code": str,
                "report_date": str,
            }

        # 检查必需字段和类型
        for field_name, field_type in required_schema.items():
            if field_name not in template_variables:
                missing.append(field_name)
            elif template_variables[field_name] is None:
                missing.append(f"{field_name}(None)")
            elif not isinstance(template_variables[field_name], field_type):
                warnings.append(
                    f"{field_name}类型错误: 期望{field_type.__name__}, "
                    f"实际{type(template_variables[field_name]).__name__}"
                )

        # 检查数值范围
        numeric_fields = ["nav", "unit_nav", "total_return", "annualized_return"]
        for fld in numeric_fields:
            if fld in template_variables:
                value = template_variables[fld]
                if isinstance(value, (int, float)):
                    if value < 0:
                        warnings.append(f"{fld}为负数: {value}")
                    elif value > 10000:  # 净值上限
                        warnings.append(f"{fld}超出合理范围: {value}")

        return ReportValidationResult(
            passed=len(missing) == 0,
            missing_fields=missing,
            warnings=warnings,
            compliance_status="pass" if len(missing) == 0 and not warnings else "warning",
        )

    def validate_rendered_output(
        self,
        rendered_content: str,
        min_length: int = 100,
        check_placeholders: bool = True,
    ) -> ReportValidationResult:
        """
        验证渲染后的输出质量.

        Args:
            rendered_content: 渲染后的内容
            min_length: 最小内容长度
            check_placeholders: 是否检查未替换的占位符

        Returns:
            验证结果
        """
        missing = []
        warnings = []

        # 检查内容长度
        if len(rendered_content) < min_length:
            warnings.append(f"内容过短: {len(rendered_content)}字符")

        # 检查未替换的Jinja2占位符
        if check_placeholders:
            import re

            # 匹配 {{ variable }} 或 {% %}
            placeholder_pattern = r"\{\{\s*\w+\s*\}\}|\{%\s*\w+\s*%\}"
            placeholders = re.findall(placeholder_pattern, rendered_content)
            if placeholders:
                warnings.append(f"存在未替换的占位符: {placeholders[:3]}")

        # 检查HTML标签完整性（如果是HTML内容）
        if "<" in rendered_content and ">" in rendered_content:
            open_tags = rendered_content.count("<")
            close_tags = rendered_content.count(">")
            if open_tags != close_tags:
                warnings.append(f"HTML标签不匹配: {open_tags}个<, {close_tags}个>")

        return ReportValidationResult(
            passed=len(missing) == 0 and not warnings,
            missing_fields=missing,
            warnings=warnings,
            compliance_status="pass" if not warnings else "warning",
        )

    def validate_report_schema(
        self,
        report_data: dict,
        schema: dict[str, dict[str, Any]] | None = None,
    ) -> ReportValidationResult:
        """
        验证报告数据结构schema.

        Args:
            report_data: 报告数据
            schema: 字段schema定义，如 {"field": {"type": str, "required": True, "min_length": 1}}

        Returns:
            验证结果
        """
        missing = []
        warnings = []

        # 默认schema
        if schema is None:
            schema = {
                "fund_code": {"type": str, "required": True, "min_length": 6, "max_length": 6},
                "report_date": {"type": str, "required": True},
                "metrics": {"type": dict, "required": True},
            }

        for field_name, field_schema in schema.items():
            # 检查必需字段
            if field_schema.get("required", False):
                if field_name not in report_data:
                    missing.append(field_name)
                    continue

            if field_name not in report_data:
                continue

            value = report_data[field_name]
            field_type = field_schema.get("type")

            # 检查类型
            if field_type and not isinstance(value, field_type):
                warnings.append(
                    f"{field_name}类型错误: 期望{field_type.__name__}, 实际{type(value).__name__}"
                )

            # 检查字符串长度
            if isinstance(value, str):
                min_len = field_schema.get("min_length")
                max_len = field_schema.get("max_length")
                if min_len and len(value) < min_len:
                    warnings.append(f"{field_name}长度不足: {len(value)} < {min_len}")
                if max_len and len(value) > max_len:
                    warnings.append(f"{field_name}长度超出: {len(value)} > {max_len}")

            # 检查数值范围
            if isinstance(value, (int, float)):
                min_val = field_schema.get("min")
                max_val = field_schema.get("max")
                if min_val is not None and value < min_val:
                    warnings.append(f"{field_name}值过小: {value} < {min_val}")
                if max_val is not None and value > max_val:
                    warnings.append(f"{field_name}值过大: {value} > {max_val}")

        return ReportValidationResult(
            passed=len(missing) == 0,
            missing_fields=missing,
            warnings=warnings,
            compliance_status="pass" if len(missing) == 0 and not warnings else "warning",
        )

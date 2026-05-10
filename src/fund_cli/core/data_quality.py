"""数据质量检查器.

提供基金数据质量检查功能，包括完整性、准确性、时效性检查，
以及 Expectation 风格的自动化数据验证。
"""

import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

import pandas as pd

from fund_cli.utils.validators import (
    validate_daily_return,
    validate_data_min_rows,
    validate_nav_value,
)

logger = logging.getLogger(__name__)


@dataclass
class ExpectationResult:
    """
    单条期望检查结果.

    Attributes:
        name: 期望名称
        passed: 是否通过
        message: 结果消息
        severity: 严重级别 (error, warning, info)
    """

    name: str
    passed: bool
    message: str = ""
    severity: str = "error"  # error, warning, info


@dataclass
class QualityReport:
    """
    数据质量报告.

    包含质量评分、级别和详细检查结果。

    Attributes:
        fund_code: 基金代码
        score: 质量评分 (0-100)
        level: 质量级别 (good, warning, poor)
        results: 期望检查结果列表
        blocked: 是否阻止分析
    """

    fund_code: str
    score: float
    level: str  # good, warning, poor
    results: list[ExpectationResult] = field(default_factory=list)
    blocked: bool = False  # 是否阻止分析

    @property
    def passed_count(self) -> int:
        """返回通过的检查数量."""
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        """返回失败的检查数量."""
        return sum(1 for r in self.results if not r.passed)

    @property
    def error_count(self) -> int:
        """返回错误级别的失败数量."""
        return sum(1 for r in self.results if not r.passed and r.severity == "error")

    @property
    def warning_count(self) -> int:
        """返回警告级别的失败数量."""
        return sum(1 for r in self.results if not r.passed and r.severity == "warning")


class DataQualityChecker:
    """
    数据质量检查器.

    提供数据完整性、准确性、时效性检查，以及 Expectation 风格的自动化验证。

    功能:
        - 数据质量检查 (FUND-DATA-005)
        - 增量更新 (FUND-DATA-006)
        - 批量下载 (FUND-DATA-007)

    Attributes:
        _dm: DataManager 实例
    """

    def __init__(self, data_manager=None):
        """
        初始化数据质量检查器.

        Args:
            data_manager: DataManager 实例，默认自动创建
        """
        from fund_cli.core.data_manager import DataManager

        self._dm = data_manager or DataManager()

    def check(self, fund_code: str) -> dict[str, Any]:
        """
        执行完整数据质量检查.

        Args:
            fund_code: 基金代码

        Returns:
            包含完整性、准确性、时效性评分的字典
        """
        try:
            nav_df = self._dm.get_fund_nav(fund_code)
            if nav_df.empty:
                return {"fund_code": fund_code, "status": "error", "message": "无数据"}
            completeness = self.check_completeness(nav_df)
            accuracy = self.check_accuracy(nav_df)
            timeliness = self.check_timeliness(nav_df)
            overall = (
                "good"
                if completeness["score"] >= 90 and accuracy["score"] >= 90
                else ("warning" if completeness["score"] >= 70 else "poor")
            )
            return {
                "fund_code": fund_code,
                "overall_status": overall,
                "completeness": completeness,
                "accuracy": accuracy,
                "timeliness": timeliness,
            }
        except Exception as e:
            return {"fund_code": fund_code, "status": "error", "message": str(e)}

    def check_completeness(self, nav_data: pd.DataFrame) -> dict[str, Any]:
        """
        完整性检查 (FUND-DATA-005).

        检查数据完整性，包括缺失值和日期连续性。

        Args:
            nav_data: 净值数据 DataFrame

        Returns:
            包含 score, total_rows, missing_values, date_gaps 的字典
        """
        total_rows = len(nav_data)
        if total_rows == 0:
            return {"score": 0, "total_rows": 0, "missing_values": {}, "date_gaps": 0}

        missing = {}
        for col in ["unit_nav", "daily_return"]:
            if col in nav_data.columns:
                missing[col] = int(nav_data[col].isna().sum())

        # 检查日期连续性
        if "nav_date" in nav_data.columns:
            dates = pd.to_datetime(nav_data["nav_date"]).sort_values()
            business_days = pd.bdate_range(dates.min(), dates.max())
            expected_count = len(business_days)
            gaps = expected_count - total_rows
        else:
            gaps = 0

        score = max(0, 100 - (sum(missing.values()) + gaps) * 2)
        return {
            "score": min(100, score),
            "total_rows": total_rows,
            "missing_values": missing,
            "date_gaps": max(0, gaps),
        }

    def check_accuracy(self, nav_data: pd.DataFrame) -> dict[str, Any]:
        """
        准确性检查（异常值检测）.

        使用 IQR 方法检测净值异常值。

        Args:
            nav_data: 净值数据 DataFrame

        Returns:
            包含 score, anomaly_count, anomalies 的字典
        """
        if nav_data.empty or "unit_nav" not in nav_data.columns:
            return {"score": 100, "anomalies": []}

        nav = nav_data["unit_nav"].dropna()
        if len(nav) < 10:
            return {"score": 100, "anomalies": []}

        q1 = nav.quantile(0.25)
        q3 = nav.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 3 * iqr
        upper = q3 + 3 * iqr

        anomalies = nav[(nav < lower) | (nav > upper)]
        score = max(0, 100 - len(anomalies) * 5)
        return {
            "score": min(100, score),
            "anomaly_count": len(anomalies),
            "anomalies": anomalies.head(5).tolist(),
        }

    def check_timeliness(self, nav_data: pd.DataFrame) -> dict[str, Any]:
        """
        时效性检查.

        检查数据最后更新时间。

        Args:
            nav_data: 净值数据 DataFrame

        Returns:
            包含 last_date, days_since_update, status 的字典
        """
        if nav_data.empty or "nav_date" not in nav_data.columns:
            return {"last_date": None, "days_since_update": None, "status": "unknown"}

        last_date = pd.to_datetime(nav_data["nav_date"]).max()
        today = pd.Timestamp.now().normalize()
        days_since = (today - last_date).days

        if days_since <= 1:
            status = "current"
        elif days_since <= 7:
            status = "recent"
        else:
            status = "outdated"

        return {
            "last_date": str(last_date.date()),
            "days_since_update": days_since,
            "status": status,
        }

    def incremental_update(self, fund_code: str) -> dict[str, Any]:
        """增量更新 (FUND-DATA-006)"""
        try:
            # 获取缓存中最新日期
            cache = self._dm._cache
            cached = cache.get(
                f"fund_nav:{fund_code}:19900101:{pd.Timestamp.now().strftime('%Y%m%d')}"
            )
            if cached is not None and not cached.empty and "nav_date" in cached.columns:
                last_date = pd.to_datetime(cached["nav_date"]).max().date()
                start = last_date + timedelta(days=1)
            else:
                start = None

            new_data = self._dm.get_fund_nav(fund_code, start_date=start)
            return {
                "fund_code": fund_code,
                "new_records": len(new_data),
                "start_date": str(start) if start else "all",
                "status": "success",
            }
        except Exception as e:
            return {"fund_code": fund_code, "status": "error", "message": str(e)}

    def batch_download(self, fund_codes: list[str]) -> dict[str, Any]:
        """批量下载 (FUND-DATA-007)"""
        results = {}
        success = 0
        for code in fund_codes:
            try:
                nav = self._dm.get_fund_nav(code)
                results[code] = {"status": "success", "records": len(nav)}
                success += 1
            except Exception as e:
                results[code] = {"status": "error", "message": str(e)}

        return {
            "total": len(fund_codes),
            "success": success,
            "failed": len(fund_codes) - success,
            "details": results,
        }

    def run_expectations(self, fund_code: str, nav_data: pd.DataFrame) -> QualityReport:
        """运行期望检查套件."""
        results: list[ExpectationResult] = []

        # E1: 数据非空检查
        if nav_data is None or nav_data.empty:
            results.append(ExpectationResult("数据非空", False, "数据为空", "error"))
            return QualityReport(
                fund_code=fund_code, score=0, level="poor", results=results, blocked=True
            )
        results.append(ExpectationResult("数据非空", True))

        # E2: 最少数据量检查 (30个交易日)
        is_valid, msg = validate_data_min_rows(nav_data, 30)
        results.append(
            ExpectationResult(
                "最少数据量(30行)", is_valid, msg, "error" if not is_valid else "info"
            )
        )

        # E3: 必要列存在检查
        required_cols = ["nav_date", "unit_nav"]
        missing = [c for c in required_cols if c not in nav_data.columns]
        results.append(
            ExpectationResult(
                "必要列完整",
                len(missing) == 0,
                f"缺失列: {missing}" if missing else "",
                "error" if missing else "info",
            )
        )

        # E4: unit_nav 非空检查
        if "unit_nav" in nav_data.columns:
            null_count = nav_data["unit_nav"].isna().sum()
            null_ratio = null_count / len(nav_data)
            passed = null_ratio < 0.05
            results.append(
                ExpectationResult(
                    "unit_nav非空率>95%",
                    passed,
                    f"空值率: {null_ratio:.1%}",
                    "error" if not passed else "info",
                )
            )

        # E5: unit_nav 合理范围检查
        if "unit_nav" in nav_data.columns:
            invalid_count = 0
            for val in nav_data["unit_nav"].dropna():
                is_valid, _ = validate_nav_value(val)
                if not is_valid:
                    invalid_count += 1
            passed = invalid_count == 0
            results.append(
                ExpectationResult(
                    "unit_nav合理范围",
                    passed,
                    f"异常值: {invalid_count}",
                    "warning" if not passed else "info",
                )
            )

        # E6: daily_return 合理范围检查
        if "daily_return" in nav_data.columns:
            extreme_count = 0
            for val in nav_data["daily_return"].dropna():
                is_valid, _ = validate_daily_return(val)
                if not is_valid:
                    extreme_count += 1
            passed = extreme_count <= len(nav_data) * 0.01  # 允许1%极端值
            results.append(
                ExpectationResult(
                    "daily_return合理范围",
                    passed,
                    f"极端值: {extreme_count} ({extreme_count / len(nav_data):.1%})",
                    "warning" if not passed else "info",
                )
            )

        # E7: 日期唯一性检查 (无重复日期)
        if "nav_date" in nav_data.columns:
            dup_count = nav_data["nav_date"].duplicated().sum()
            results.append(
                ExpectationResult(
                    "日期唯一性",
                    dup_count == 0,
                    f"重复日期: {dup_count}",
                    "warning" if dup_count > 0 else "info",
                )
            )

        # E8: 时效性检查
        timeliness = self.check_timeliness(nav_data)
        is_current = timeliness["status"] in ("current", "recent")
        results.append(
            ExpectationResult(
                "数据时效性",
                is_current,
                f"最后更新: {timeliness.get('latest_date', 'N/A')}, 状态: {timeliness['status']}",
                "warning" if not is_current else "info",
            )
        )

        # Calculate score
        weights = {"error": 15, "warning": 5, "info": 0}
        total_penalty = sum(weights.get(r.severity, 0) if not r.passed else 0 for r in results)
        score = max(0, 100 - total_penalty)

        # Determine level
        error_count = sum(1 for r in results if not r.passed and r.severity == "error")
        if score >= 90:
            level = "good"
        elif score >= 70:
            level = "warning"
        else:
            level = "poor"

        # 只有当评分低于阈值或有严重错误时才阻止
        blocked = score < 60 or error_count >= 3

        return QualityReport(
            fund_code=fund_code,
            score=score,
            level=level,
            results=results,
            blocked=blocked,
        )

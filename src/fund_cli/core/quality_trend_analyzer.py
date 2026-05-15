"""
数据质量趋势分析器.

基于审计日志分析数据质量趋势，支持异常检测。
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class QualityTrend:
    """质量趋势."""

    fund_code: str
    date: datetime
    quality_score: float
    quality_level: str
    error_count: int
    warning_count: int
    trend: str = "stable"  # improving, deteriorating, stable


class QualityTrendAnalyzer:
    """
    质量趋势分析器.

    分析数据质量的历史趋势，检测异常和回归。
    """

    def __init__(self, audit_log_dir: str = "~/.fund_cli/audit"):
        """
        初始化趋势分析器.

        Args:
            audit_log_dir: 审计日志目录
        """
        self._audit_log_dir = Path(audit_log_dir).expanduser()

    def load_quality_logs(
        self,
        fund_code: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> pd.DataFrame:
        """
        加载质量检查日志.

        Args:
            fund_code: 基金代码过滤
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            质量日志DataFrame
        """
        logs = []

        # 遍历审计日志文件
        for log_file in self._audit_log_dir.glob("audit_*.jsonl"):
            try:
                with open(log_file, encoding='utf-8') as f:
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            if record.get("type") == "quality_check":
                                # 日期过滤
                                record_date = datetime.fromisoformat(record["timestamp"])
                                if start_date and record_date < start_date:
                                    continue
                                if end_date and record_date > end_date:
                                    continue

                                # 基金代码过滤
                                if fund_code and record.get("fund_code") != fund_code:
                                    continue

                                logs.append({
                                    "timestamp": record_date,
                                    "fund_code": record.get("fund_code"),
                                    "quality_score": record.get("quality_score"),
                                    "quality_level": record.get("quality_level"),
                                    "blocked": record.get("blocked"),
                                    "details": record.get("details", {}),
                                })
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                logger.error(f"读取日志文件失败 {log_file}: {e}")

        if not logs:
            return pd.DataFrame()

        df = pd.DataFrame(logs)
        df = df.sort_values("timestamp")
        return df

    def analyze_trend(
        self,
        fund_code: str,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        分析单个基金的质量趋势.

        Args:
            fund_code: 基金代码
            days: 分析天数

        Returns:
            趋势分析结果
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = self.load_quality_logs(fund_code=fund_code, start_date=start_date, end_date=end_date)

        if df.empty:
            return {
                "fund_code": fund_code,
                "has_data": False,
                "message": "无质量检查数据",
            }

        # 计算趋势
        scores = df["quality_score"].tolist()
        avg_score = sum(scores) / len(scores)

        # 简单线性趋势
        if len(scores) >= 2:
            first_half = scores[:len(scores)//2]
            second_half = scores[len(scores)//2:]
            first_avg = sum(first_half) / len(first_half)
            second_avg = sum(second_half) / len(second_half)

            if second_avg > first_avg + 5:
                trend = "improving"
            elif second_avg < first_avg - 5:
                trend = "deteriorating"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # 检测异常值
        blocked_count = df[df["blocked"]].shape[0]
        warning_count = df[df["quality_level"] == "warning"].shape[0]

        return {
            "fund_code": fund_code,
            "has_data": True,
            "period_days": days,
            "check_count": len(df),
            "avg_score": round(avg_score, 2),
            "min_score": round(min(scores), 2),
            "max_score": round(max(scores), 2),
            "trend": trend,
            "blocked_count": blocked_count,
            "warning_count": warning_count,
            "latest_score": round(scores[-1], 2) if scores else None,
            "recommendation": self._generate_recommendation(trend, avg_score, blocked_count),
        }

    def _generate_recommendation(
        self,
        trend: str,
        avg_score: float,
        blocked_count: int,
    ) -> str:
        """生成建议."""
        if blocked_count > 0:
            return "数据质量问题严重，建议立即检查数据源"
        if trend == "deteriorating":
            return "数据质量呈下降趋势，建议关注"
        if avg_score < 70:
            return "数据质量评分较低，建议优化"
        if trend == "improving":
            return "数据质量持续改善"
        return "数据质量稳定"

    def detect_anomalies(
        self,
        fund_code: str | None = None,
        days: int = 7,
        score_threshold: float = 60.0,
    ) -> list[dict[str, Any]]:
        """
        检测质量异常.

        Args:
            fund_code: 基金代码过滤
            days: 检测天数
            score_threshold: 分数阈值

        Returns:
            异常列表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = self.load_quality_logs(fund_code=fund_code, start_date=start_date, end_date=end_date)

        if df.empty:
            return []

        anomalies = []

        # 检测低分异常
        low_scores = df[df["quality_score"] < score_threshold]
        for _, row in low_scores.iterrows():
            anomalies.append({
                "type": "low_score",
                "fund_code": row["fund_code"],
                "timestamp": row["timestamp"].isoformat(),
                "quality_score": row["quality_score"],
                "severity": "critical" if row["quality_score"] < 40 else "warning",
            })

        # 检测被拦截的记录
        blocked = df[df["blocked"]]
        for _, row in blocked.iterrows():
            anomalies.append({
                "type": "blocked",
                "fund_code": row["fund_code"],
                "timestamp": row["timestamp"].isoformat(),
                "severity": "critical",
            })

        return anomalies

    def get_summary_report(self, days: int = 30) -> dict[str, Any]:
        """
        获取汇总报告.

        Args:
            days: 报告天数

        Returns:
            汇总报告
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        df = self.load_quality_logs(start_date=start_date, end_date=end_date)

        if df.empty:
            return {"has_data": False, "message": "无质量检查数据"}

        total_checks = len(df)
        unique_funds = df["fund_code"].nunique()
        avg_score = df["quality_score"].mean()
        blocked_count = df[df["blocked"]].shape[0]

        # 按基金统计
        fund_stats = []
        for fund_code in df["fund_code"].unique():
            fund_df = df[df["fund_code"] == fund_code]
            fund_stats.append({
                "fund_code": fund_code,
                "check_count": len(fund_df),
                "avg_score": round(fund_df["quality_score"].mean(), 2),
                "blocked_count": fund_df[fund_df["blocked"]].shape[0],
            })

        # 排序：问题最多的在前
        fund_stats.sort(key=lambda x: x["blocked_count"], reverse=True)

        return {
            "has_data": True,
            "period_days": days,
            "total_checks": total_checks,
            "unique_funds": unique_funds,
            "overall_avg_score": round(avg_score, 2),
            "blocked_count": blocked_count,
            "fund_stats": fund_stats[:10],  # 前10个基金
        }


# 全局趋势分析器实例
_analyzer: QualityTrendAnalyzer | None = None


def get_quality_trend_analyzer() -> QualityTrendAnalyzer:
    """获取全局趋势分析器实例."""
    global _analyzer
    if _analyzer is None:
        _analyzer = QualityTrendAnalyzer()
    return _analyzer

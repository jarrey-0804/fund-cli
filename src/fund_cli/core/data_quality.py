"""数据质量检查器"""

from datetime import timedelta
from typing import Any

import pandas as pd


class DataQualityChecker:
    """
    数据质量检查器

    功能：
    - 数据质量检查 (FUND-DATA-005)
    - 增量更新 (FUND-DATA-006)
    - 批量下载 (FUND-DATA-007)
    """

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import DataManager

        self._dm = data_manager or DataManager()

    def check(self, fund_code: str) -> dict[str, Any]:
        """执行完整数据质量检查"""
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
        """完整性检查 (FUND-DATA-005)"""
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
        """准确性检查（异常值检测）"""
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
        """时效性检查"""
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

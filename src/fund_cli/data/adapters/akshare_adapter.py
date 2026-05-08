"""
AKShare 数据源适配器

基于 AKShare 开源库实现数据获取，支持基金信息、净值、筛选等功能。
"""

from datetime import date, datetime
from typing import Any

import pandas as pd

from fund_cli.data.base import (
    DataNotFoundError,
    DataSourceAdapter,
    DataSourceError,
)
from fund_cli.data.cache import DataCache


class AKShareAdapter(DataSourceAdapter):
    """
    AKShare 数据源适配器

    使用 AKShare 开源库获取基金数据，特点：
    - 免费使用，无需Token
    - 数据覆盖全面
    - 支持实时数据
    """

    def __init__(self, cache: DataCache | None = None):
        """
        初始化 AKShare 适配器

        Args:
            cache: 缓存管理器，可选
        """
        super().__init__("akshare")
        self._cache = cache
        self._ak = None

    def _get_akshare(self):
        """延迟加载 AKShare"""
        if self._ak is None:
            try:
                import akshare as ak

                self._ak = ak
            except ImportError as e:
                raise DataSourceError("AKShare 未安装，请运行: pip install akshare") from e
        return self._ak

    def is_available(self) -> bool:
        """检查 AKShare 是否可用"""
        try:
            self._get_akshare()
            return True
        except Exception:
            return False

    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金基础信息

        Args:
            fund_code: 基金代码

        Returns:
            基金信息字典
        """
        # 检查缓存
        if self._cache:
            cached = self._cache.get_fund_info(fund_code)
            if cached:
                return cached

        ak = self._get_akshare()

        try:
            # 获取基金基本信息
            df = ak.fund_individual_basic_info_xq(symbol=fund_code)

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 不存在")

            # 解析数据
            info_dict = dict(zip(df["item"], df["value"], strict=False))

            result = {
                "code": fund_code,
                "name": info_dict.get("基金简称", info_dict.get("基金全称", "")),
                "type": info_dict.get("基金类型", "未知"),
                "establish_date": self._parse_date(info_dict.get("成立日期")),
                "manager": info_dict.get("基金经理", ""),
                "company": info_dict.get("基金管理人", ""),
                "scale": self._parse_scale(info_dict.get("基金规模")),
            }

            # 缓存结果
            if self._cache:
                self._cache.set_fund_info(fund_code, result)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金信息失败: {e}") from e

    def get_fund_nav(
        self,
        fund_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金净值数据

        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            净值数据 DataFrame
        """
        # 格式化日期
        start_str = start_date.strftime("%Y%m%d") if start_date else "19900101"
        end_str = end_date.strftime("%Y%m%d") if end_date else datetime.now().strftime("%Y%m%d")

        # 检查缓存
        if self._cache:
            cached = self._cache.get_fund_nav(fund_code, start_str, end_str)
            if cached is not None:
                return cached

        ak = self._get_akshare()

        try:
            # 获取开放式基金净值数据
            df = ak.fund_open_fund_info_em(fund=fund_code, indicator="单位净值走势")

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 净值数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "净值日期": "nav_date",
                    "单位净值": "unit_nav",
                    "日增长率": "daily_return",
                }
            )

            # 处理日期
            df["nav_date"] = pd.to_datetime(df["nav_date"])

            # 筛选日期范围
            if start_date:
                df = df[df["nav_date"] >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df["nav_date"] <= pd.Timestamp(end_date)]

            # 添加基金代码
            df["fund_code"] = fund_code

            # 计算累计净值（如果没有）
            if "accumulated_nav" not in df.columns:
                df["accumulated_nav"] = df["unit_nav"]

            # 选择输出列
            result_df = df[
                ["fund_code", "nav_date", "unit_nav", "accumulated_nav", "daily_return"]
            ].copy()
            result_df = result_df.sort_values("nav_date").reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set_fund_nav(fund_code, start_str, end_str, result_df)

            return result_df

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金净值失败: {e}") from e

    def search_funds(
        self,
        fund_type: str | None = None,
        company: str | None = None,
        min_scale: float | None = None,
        max_scale: float | None = None,
        keyword: str | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        搜索/筛选基金

        Args:
            fund_type: 基金类型
            company: 基金公司
            min_scale: 最小规模
            max_scale: 最大规模
            keyword: 关键词
            limit: 返回数量限制

        Returns:
            基金列表 DataFrame
        """
        ak = self._get_akshare()

        try:
            # 获取全部开放式基金列表
            df = ak.fund_open_fund_daily_em()

            # 筛选条件
            if fund_type:
                df = df[df["基金类型"].str.contains(fund_type, na=False)]

            if company:
                df = df[df["基金公司"].str.contains(company, na=False)]

            if keyword:
                mask = df["基金代码"].str.contains(keyword, na=False) | df["基金简称"].str.contains(
                    keyword, na=False
                )
                df = df[mask]

            # 规模筛选
            if min_scale is not None:
                df = df[df["基金规模"] >= min_scale]
            if max_scale is not None:
                df = df[df["基金规模"] <= max_scale]

            # 限制返回数量
            df = df.head(limit)

            # 标准化列名
            df = df.rename(
                columns={
                    "基金代码": "code",
                    "基金简称": "name",
                    "基金类型": "type",
                    "基金规模": "scale",
                    "基金公司": "company",
                }
            )

            return df.reset_index(drop=True)

        except Exception as e:
            raise DataSourceError(f"搜索基金失败: {e}") from e

    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """
        获取基金列表

        Args:
            fund_type: 基金类型筛选

        Returns:
            基金列表 DataFrame
        """
        return self.search_funds(fund_type=fund_type)

    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基准指数数据

        Args:
            benchmark_code: 基准指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            基准数据 DataFrame
        """
        ak = self._get_akshare()

        try:
            # 获取指数数据
            df = ak.stock_zh_index_daily(symbol=f"sh{benchmark_code}")

            if df.empty:
                raise DataNotFoundError(f"指数 {benchmark_code} 不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "date": "nav_date",
                    "close": "unit_nav",
                }
            )

            # 处理日期
            df["nav_date"] = pd.to_datetime(df["nav_date"])

            # 筛选日期范围
            if start_date:
                df = df[df["nav_date"] >= pd.Timestamp(start_date)]
            if end_date:
                df = df[df["nav_date"] <= pd.Timestamp(end_date)]

            # 计算收益率
            df["daily_return"] = df["unit_nav"].pct_change() * 100
            df["fund_code"] = benchmark_code
            df["accumulated_nav"] = df["unit_nav"]

            result_df = df[
                ["fund_code", "nav_date", "unit_nav", "accumulated_nav", "daily_return"]
            ].copy()
            return result_df.sort_values("nav_date").reset_index(drop=True)

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基准数据失败: {e}") from e

    def get_fund_holdings(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """获取基金持仓数据"""
        cache_key = f"holdings:{fund_code}:{report_date or 'latest'}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_portfolio_hold_em(symbol=fund_code, date=report_date)
            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 持仓数据不存在")
            df = df.rename(
                columns={
                    "季度": "report_date",
                    "股票代码": "stock_code",
                    "股票名称": "stock_name",
                    "占净值比例": "weight",
                    "持股数": "holdings_count",
                    "持仓市值": "market_value",
                }
            )
            if "fund_code" not in df.columns:
                df["fund_code"] = fund_code
            result = df.sort_values("weight", ascending=False).reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)
            return result
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取持仓数据失败: {e}") from e

    def get_fund_manager(self, fund_code: str) -> dict[str, Any]:
        """获取基金经理信息"""
        info = self.get_fund_info(fund_code)
        return {
            "name": info.get("manager", ""),
            "fund_code": fund_code,
            "fund_name": info.get("name", ""),
            "company": info.get("company", ""),
        }

    def get_fund_fee(self, fund_code: str) -> dict[str, Any]:
        """获取基金费率信息"""
        ak = self._get_akshare()
        try:
            df = ak.fund_individual_detail_info_xq(symbol=fund_code)
            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 费率信息不存在")
            info_dict = dict(zip(df["item"], df["value"], strict=False))
            return {
                "management_fee": info_dict.get("管理费率", ""),
                "custody_fee": info_dict.get("托管费率", ""),
                "purchase_fee": info_dict.get("申购费率", ""),
                "redeem_fee": info_dict.get("赎回费率", ""),
            }
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取费率信息失败: {e}") from e

    def get_fund_rating(self, fund_code: str) -> int | None:
        """获取基金评级"""
        ak = self._get_akshare()
        try:
            df = ak.fund_individual_detail_info_xq(symbol=fund_code)
            if df.empty:
                return None
            info_dict = dict(zip(df["item"], df["value"], strict=False))
            rating_str = info_dict.get("基金评级", "")
            if not rating_str:
                return None
            import re

            match = re.search(r"(\d+)", str(rating_str))
            return int(match.group(1)) if match else None
        except Exception:
            return None

    def batch_get_fund_nav(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """批量获取基金净值数据"""
        results = {}
        for code in fund_codes:
            try:
                results[code] = self.get_fund_nav(code, start_date, end_date)
            except Exception:
                results[code] = pd.DataFrame()
        return results

    @staticmethod
    def _parse_date(date_str: str | None) -> date | None:
        """解析日期字符串"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_scale(scale_str: str | None) -> float | None:
        """解析规模字符串"""
        if not scale_str:
            return None
        try:
            # 移除单位并转换为浮点数
            scale_str = str(scale_str).replace("亿份", "").replace("亿元", "").strip()
            return float(scale_str)
        except (ValueError, TypeError):
            return None

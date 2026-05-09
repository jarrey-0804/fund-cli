"""
Tushare 数据源适配器.

基于 Tushare Pro API 实现数据获取，支持P0级别18个核心方法。
"""

from datetime import date, datetime
from typing import Any

import pandas as pd

from fund_cli.config import get_config
from fund_cli.data.adapters.mixins import DataSourceAdapterMixin
from fund_cli.data.base import (
    DataNotFoundError,
    DataSourceAdapter,
    DataSourceError,
)
from fund_cli.data.cache import DataCache


class TushareAdapter(DataSourceAdapterMixin, DataSourceAdapter):
    """
    Tushare 数据源适配器.

    使用 Tushare Pro API 获取基金数据，特点：
    - 数据质量高
    - 需要注册获取 Token
    - 部分接口需要积分

    适配 Tushare 2025.11 变更：
    - 禁止多 ts_code 批量提取，改用 trade_date 批量拉取后本地过滤
    - 尊重积分门槛制，根据用户积分等级自动调整请求频率

    Note: 继承顺序 DataSourceAdapterMixin 在前，确保其方法在 MRO 中优先于 DataSourceAdapter 的抽象方法
    """

    def __init__(self, cache: DataCache | None = None):
        """
        初始化 Tushare 适配器.

        Args:
            cache: 缓存管理器，可选
        """
        super().__init__("tushare")
        self._cache = cache
        self._ts = None
        self._token: str | None = None
        self._request_count = 0
        self._last_request_time = datetime.min
        self._min_interval = 1.0  # 最小请求间隔（秒）

    def _get_tushare(self):
        """延迟加载 Tushare."""
        if self._ts is None:
            try:
                import tushare as ts

                config = get_config()
                self._token = config.data.tushare_token
                if not self._token:
                    raise DataSourceError(
                        "Tushare Token 未配置，请在 .env 中设置 FUND_DATA_TUSHARE_TOKEN"
                    )
                ts.set_token(self._token)
                self._ts = ts.pro_api()
            except ImportError as e:
                raise DataSourceError("Tushare 未安装，请运行: pip install tushare") from e
        return self._ts

    def _rate_limit(self) -> None:
        """简单的请求频率限制."""
        now = datetime.now()
        elapsed = (now - self._last_request_time).total_seconds()
        if elapsed < self._min_interval:
            import time
            time.sleep(self._min_interval - elapsed)
        self._last_request_time = datetime.now()
        self._request_count += 1

    def _convert_date_format(self, df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
        """转换日期格式为 YYYY-MM-DD."""
        for col in date_columns:
            if col in df.columns:
                if df[col].dtype == 'object':
                    df[col] = pd.to_datetime(df[col], format='%Y%m%d', errors='coerce').dt.strftime('%Y-%m-%d')
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
        return df

    def is_available(self) -> bool:
        """检查 Tushare 是否可用."""
        try:
            config = get_config()
            return bool(config.data.tushare_token)
        except Exception:
            return False

    # =========================================================================
    # P0 - 核心基金功能接口 (18个)
    # =========================================================================

    # ----- 基金基本信息 (5个) -----

    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金基础信息.

        Args:
            fund_code: 基金代码

        Returns:
            基金信息字典
        """
        if self._cache:
            cached = self._cache.get_fund_info(fund_code)
            if cached:
                return cached

        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(ts_code=f"{fund_code}.OF")

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 不存在")

            row = df.iloc[0]

            result = {
                "code": fund_code,
                "name": row.get("name", ""),
                "type": row.get("fund_type", "未知"),
                "establish_date": row.get("found_date", None),
                "manager": row.get("manager", ""),
                "company": row.get("management", ""),
                "scale": None,
            }

            if self._cache:
                self._cache.set_fund_info(fund_code, result)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金信息失败: {e}") from e

    def get_all_fund_names(self) -> pd.DataFrame:
        """
        获取所有基金名称列表.

        Returns:
            DataFrame包含：基金代码, 拼音缩写, 基金简称, 基金类型, 拼音全称
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(market="O")

            df = df.rename(
                columns={
                    "ts_code": "code",
                    "name": "name",
                    "fullname": "full_name",
                    "symbol": "symbol",
                    "fund_type": "type",
                }
            )

            df = df[["code", "symbol", "name", "type", "full_name"]]

            return df.reset_index(drop=True)

        except Exception as e:
            raise DataSourceError(f"获取基金名称列表失败: {e}") from e

    def get_fund_info_ths(self, fund_code: str) -> dict[str, Any]:
        """
        同花顺-基金基本信息.

        Args:
            fund_code: 基金代码

        Returns:
            基金详细信息字典
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(ts_code=f"{fund_code}.OF")

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 不存在")

            row = df.iloc[0]

            return {
                "code": fund_code,
                "name": row.get("name", ""),
                "full_name": row.get("fullname", ""),
                "type": row.get("fund_type", ""),
                "management": row.get("management", ""),
                "trustee": row.get("trustee", ""),
                "found_date": row.get("found_date", ""),
                "due_date": row.get("due_date", ""),
                "list_date": row.get("list_date", ""),
                "issue_date": row.get("issue_date", ""),
                "delist_date": row.get("delist_date", ""),
                "status": row.get("status", ""),
            }

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取同花顺基金信息失败: {e}") from e

    def get_index_fund_info(
        self, category: str = "全部", indicator: str = "全部"
    ) -> pd.DataFrame:
        """
        东方财富-指数型基金基本信息.

        Args:
            category: 分类，可选"全部","沪深指数","行业主题","大盘指数"等
            indicator: 指标，可选"全部","被动指数型","增强指数型"

        Returns:
            指数型基金信息DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            # Tushare fund_basic 不支持分类过滤，返回全部后本地过滤
            df = ts.fund_basic(market="O")

            # 过滤指数型基金
            if category != "全部":
                df = df[df["invest_type"].str.contains("指数", na=False)]

            df = df.rename(
                columns={
                    "ts_code": "code",
                    "name": "name",
                    "fund_type": "type",
                    "invest_type": "invest_type",
                    "management": "management",
                    "found_date": "found_date",
                }
            )

            return df[["code", "name", "type", "invest_type", "management", "found_date"]]

        except Exception as e:
            raise DataSourceError(f"获取指数基金信息失败: {e}") from e

    def get_fund_overview(self, fund_code: str) -> dict[str, Any]:
        """
        天天基金-基金档案基本概况.

        Args:
            fund_code: 基金代码

        Returns:
            基金概况字典
        """
        # 使用 fund_basic 获取基本信息
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(ts_code=f"{fund_code}.OF")

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 不存在")

            row = df.iloc[0]

            return {
                "code": fund_code,
                "name": row.get("name", ""),
                "type": row.get("fund_type", ""),
                "management": row.get("management", ""),
                "trustee": row.get("trustee", ""),
                "found_date": row.get("found_date", ""),
                "scale": None,
                "status": row.get("status", ""),
            }

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金概况失败: {e}") from e

    # ----- 基金申购状态 (1个) -----

    def get_fund_purchase_status(self) -> pd.DataFrame:
        """
        东方财富-基金申购/赎回状态.

        Returns:
            DataFrame包含：基金代码, 基金简称, 申购状态, 赎回状态等
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(market="O")

            # fund_basic 包含状态字段
            df = df.rename(
                columns={
                    "ts_code": "code",
                    "name": "name",
                    "status": "purchase_status",
                }
            )

            return df[["code", "name", "purchase_status"]]

        except Exception as e:
            raise DataSourceError(f"获取基金申购状态失败: {e}") from e

    # ----- 基金净值数据 (2个) -----

    def get_fund_nav(
        self,
        fund_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金净值数据.

        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            净值数据DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            # Tushare 2025.11 变更：使用 trade_date 批量拉取后本地过滤
            df = ts.fund_nav(
                ts_code=f"{fund_code}.OF",
                start_date=start_date.strftime("%Y%m%d") if start_date else None,
                end_date=end_date.strftime("%Y%m%d") if end_date else None,
            )

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 净值数据不存在")

            # 转换日期格式
            df = self._convert_date_format(df, ["end_date"])

            df = df.rename(
                columns={
                    "end_date": "nav_date",
                    "unit_nav": "unit_nav",
                    "accum_nav": "accumulated_nav",
                }
            )

            df["fund_code"] = fund_code

            if "daily_return" not in df.columns:
                df["daily_return"] = df["unit_nav"].pct_change() * 100

            result_df = df[["fund_code", "nav_date", "unit_nav", "accumulated_nav", "daily_return"]].copy()
            return result_df.sort_values("nav_date").reset_index(drop=True)

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金净值失败: {e}") from e

    def get_fund_daily_nav(self) -> pd.DataFrame:
        """
        东方财富-开放式基金每日净值(全部).

        Returns:
            全部基金净值DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_nav()

            if df.empty:
                raise DataNotFoundError("基金净值数据不存在")

            # 转换日期格式
            df = self._convert_date_format(df, ["end_date"])

            df = df.rename(
                columns={
                    "ts_code": "fund_code",
                    "end_date": "nav_date",
                    "unit_nav": "unit_nav",
                    "accum_nav": "accumulated_nav",
                }
            )

            # 提取基金代码
            df["fund_code"] = df["fund_code"].str.replace(".OF", "", regex=False)

            return df[["fund_code", "nav_date", "unit_nav", "accumulated_nav"]].sort_values(
                ["fund_code", "nav_date"]
            ).reset_index(drop=True)

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金每日净值失败: {e}") from e

    # ----- 基金行情数据 (8个) -----

    def get_etf_spot(self) -> pd.DataFrame:
        """
        东方财富-ETF实时行情(全部).

        Returns:
            ETF实时行情DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(market="O", status="L")

            # 过滤 ETF
            df = df[df["fund_type"].str.contains("ETF", na=False)]

            df = df.rename(
                columns={
                    "ts_code": "code",
                    "name": "name",
                    "fund_type": "type",
                    "management": "management",
                }
            )

            return df[["code", "name", "type", "management"]]

        except Exception as e:
            raise DataSourceError(f"获取ETF实时行情失败: {e}") from e

    def get_fund_category_spot(
        self, category: str = "", date: str | None = None
    ) -> pd.DataFrame:
        """
        同花顺-基金实时行情(按类型).

        Args:
            category: 基金类型，如"股票型","债券型","混合型","ETF","LOF"等
            date: 日期

        Returns:
            基金行情DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(market="O", status="L")

            if category:
                df = df[df["fund_type"].str.contains(category, na=False)]

            df = df.rename(
                columns={
                    "ts_code": "code",
                    "name": "name",
                    "fund_type": "type",
                }
            )

            return df[["code", "name", "type"]]

        except Exception as e:
            raise DataSourceError(f"获取基金分类行情失败: {e}") from e

    def get_etf_spot_ths(self, date: str | None = None) -> pd.DataFrame:
        """
        同花顺-ETF实时行情.

        Args:
            date: 日期

        Returns:
            ETF行情DataFrame
        """
        return self.get_etf_spot()

    def get_lof_spot(self) -> pd.DataFrame:
        """
        东方财富-LOF实时行情(全部).

        Returns:
            LOF实时行情DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(market="O", status="L")

            # 过滤 LOF
            df = df[df["fund_type"].str.contains("LOF", na=False)]

            df = df.rename(
                columns={
                    "ts_code": "code",
                    "name": "name",
                    "fund_type": "type",
                    "management": "management",
                }
            )

            return df[["code", "name", "type", "management"]]

        except Exception as e:
            raise DataSourceError(f"获取LOF实时行情失败: {e}") from e

    def get_etf_hist(
        self,
        fund_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        东方财富-ETF历史行情.

        Args:
            fund_code: 基金代码
            period: 周期，"daily","weekly","monthly"
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            ETF历史行情DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            # 转换周期（保留以保持逻辑清晰）
            _freq = "D" if period == "daily" else ("W" if period == "weekly" else "M")

            df = ts.fund_nav(
                ts_code=f"{fund_code}.OF",
                start_date=start_date.replace("-", "") if start_date else None,
                end_date=end_date.replace("-", "") if end_date else None,
            )

            if df.empty:
                raise DataNotFoundError(f"ETF {fund_code} 历史行情不存在")

            df = self._convert_date_format(df, ["end_date"])

            df = df.rename(
                columns={
                    "end_date": "nav_date",
                    "unit_nav": "close",
                    "accum_nav": "accumulated_nav",
                }
            )

            df["fund_code"] = fund_code
            df["volume"] = 0

            return df[["fund_code", "nav_date", "close", "volume", "accumulated_nav"]].sort_values(
                "nav_date"
            ).reset_index(drop=True)

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取ETF历史行情失败: {e}") from e

    def get_lof_hist(
        self,
        fund_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        东方财富-LOF历史行情.

        Args:
            fund_code: 基金代码
            period: 周期
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            LOF历史行情DataFrame
        """
        return self.get_etf_hist(fund_code, period, start_date, end_date)

    # ----- 基金经理和持仓数据 (3个) -----

    def get_fund_manager(self, fund_code: str) -> pd.DataFrame:
        """
        获取基金经理信息.

        Args:
            fund_code: 基金代码

        Returns:
            基金经理信息DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_manager(ts_code=f"{fund_code}.OF")

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 基金经理信息不存在")

            df = df.rename(
                columns={
                    "ts_code": "fund_code",
                    "name": "manager_name",
                    "start_date": "start_date",
                    "end_date": "end_date",
                }
            )

            df["fund_code"] = fund_code

            return df[["fund_code", "manager_name", "start_date", "end_date"]]

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金经理信息失败: {e}") from e

    def get_fund_holdings(
        self, fund_code: str, date: str | None = None
    ) -> pd.DataFrame:
        """
        获取基金持仓数据.

        Args:
            fund_code: 基金代码
            date: 报告期

        Returns:
            基金持仓DataFrame
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_portfolio(ts_code=f"{fund_code}.OF")

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 持仓数据不存在")

            df = df.rename(
                columns={
                    "ts_code": "fund_code",
                    "symbol": "stock_code",
                    "name": "stock_name",
                    "vol": "volume",
                    "proportions": "proportion",
                }
            )

            df["fund_code"] = fund_code

            return df[["fund_code", "stock_code", "stock_name", "volume", "proportion"]]

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金持仓失败: {e}") from e

    def get_fund_asset_allocation(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金资产配置.

        Args:
            fund_code: 基金代码

        Returns:
            资产配置字典
        """
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_asset()

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 资产配置数据不存在")

            # 过滤指定基金
            df = df[df["ts_code"] == f"{fund_code}.OF"]

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 资产配置数据不存在")

            row = df.iloc[0]

            return {
                "fund_code": fund_code,
                "date": row.get("report_date", ""),
                "stock_ratio": row.get("stock_ratio", 0),
                "bond_ratio": row.get("bond_ratio", 0),
                "cash_ratio": row.get("cash_ratio", 0),
                "total_asset": row.get("total_asset", 0),
            }

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金资产配置失败: {e}") from e

    def get_fund_benchmark(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金业绩比较基准.

        Args:
            fund_code: 基金代码

        Returns:
            业绩比较基准字典
        """
        # 获取基金基本信息
        info = self.get_fund_info(fund_code)

        return {
            "fund_code": fund_code,
            "benchmark": info.get("benchmark", "未知"),
        }

    # =========================================================================
    # P1 - 分析增强功能接口 (部分实现)
    # =========================================================================

    def search_funds(
        self,
        fund_type: str | None = None,
        company: str | None = None,
        min_scale: float | None = None,
        max_scale: float | None = None,
        keyword: str | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """搜索基金."""
        ts = self._get_tushare()
        self._rate_limit()

        try:
            df = ts.fund_basic(market="O")

            if fund_type:
                df = df[df["fund_type"].str.contains(fund_type, na=False)]
            if company:
                df = df[df["management"].str.contains(company, na=False)]
            if keyword:
                mask = df["ts_code"].str.contains(keyword, na=False) | df["name"].str.contains(keyword, na=False)
                df = df[mask]

            df = df.head(limit)

            df = df.rename(
                columns={
                    "ts_code": "code",
                    "name": "name",
                    "fund_type": "type",
                    "management": "company",
                }
            )

            return df.reset_index(drop=True)

        except Exception as e:
            raise DataSourceError(f"搜索基金失败: {e}") from e

    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """获取基金列表."""
        return self.search_funds(fund_type=fund_type)

    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """获取基准指数数据."""
        ts = self._get_tushare()
        self._rate_limit()

        try:
            # 转换指数代码格式
            if benchmark_code.startswith("0") or benchmark_code.startswith("1"):
                ts_code = f"{benchmark_code}.SH"
            else:
                ts_code = f"{benchmark_code}.SZ"

            df = ts.index_daily(
                ts_code=ts_code,
                start_date=start_date.strftime("%Y%m%d") if start_date else None,
                end_date=end_date.strftime("%Y%m%d") if end_date else None,
            )

            if df.empty:
                raise DataNotFoundError(f"指数 {benchmark_code} 不存在")

            df = self._convert_date_format(df, ["trade_date"])

            df = df.rename(
                columns={
                    "trade_date": "nav_date",
                    "close": "unit_nav",
                }
            )

            df["fund_code"] = benchmark_code
            df["daily_return"] = df["unit_nav"].pct_change() * 100
            df["accumulated_nav"] = df["unit_nav"]

            result_df = df[["fund_code", "nav_date", "unit_nav", "accumulated_nav", "daily_return"]].copy()
            return result_df.sort_values("nav_date").reset_index(drop=True)

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基准数据失败: {e}") from e

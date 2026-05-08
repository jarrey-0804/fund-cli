"""
Tushare 数据源适配器

基于 Tushare Pro API 实现数据获取。
"""

from typing import Any

import pandas as pd

from fund_cli.config import get_config
from fund_cli.data.base import (
    DataNotFoundError,
    DataSourceAdapter,
    DataSourceError,
)
from fund_cli.data.cache import DataCache


class TushareAdapter(DataSourceAdapter):
    """
    Tushare 数据源适配器

    使用 Tushare Pro API 获取基金数据，特点：
    - 数据质量高
    - 需要注册获取 Token
    - 部分接口需要积分
    """

    def __init__(self, cache: DataCache | None = None):
        """
        初始化 Tushare 适配器

        Args:
            cache: 缓存管理器，可选
        """
        super().__init__("tushare")
        self._cache = cache
        self._ts = None
        self._token: str | None = None

    def _get_tushare(self):
        """延迟加载 Tushare"""
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

    def is_available(self) -> bool:
        """检查 Tushare 是否可用"""
        try:
            config = get_config()
            return bool(config.data.tushare_token)
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
        if self._cache:
            cached = self._cache.get_fund_info(fund_code)
            if cached:
                return cached

        ts = self._get_tushare()

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

    def get_fund_nav(
        self,
        fund_code: str,
        start_date: Any | None = None,
        end_date: Any | None = None,
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
        ts = self._get_tushare()

        try:
            df = ts.fund_nav(
                ts_code=f"{fund_code}.OF",
                start_date=start_date.strftime("%Y%m%d") if start_date else None,
                end_date=end_date.strftime("%Y%m%d") if end_date else None,
            )

            if df.empty:
                raise DataNotFoundError(f"基金 {fund_code} 净值数据不存在")

            df = df.rename(
                columns={
                    "end_date": "nav_date",
                    "unit_nav": "unit_nav",
                    "accum_nav": "accumulated_nav",
                }
            )

            df["nav_date"] = pd.to_datetime(df["nav_date"])
            df["fund_code"] = fund_code

            if "daily_return" not in df.columns:
                df["daily_return"] = df["unit_nav"].pct_change() * 100

            result_df = df[
                ["fund_code", "nav_date", "unit_nav", "accumulated_nav", "daily_return"]
            ].copy()
            return result_df.sort_values("nav_date").reset_index(drop=True)

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
        """搜索基金"""
        ts = self._get_tushare()

        try:
            df = ts.fund_basic(market="O")

            if fund_type:
                df = df[df["fund_type"].str.contains(fund_type, na=False)]
            if company:
                df = df[df["management"].str.contains(company, na=False)]
            if keyword:
                mask = df["ts_code"].str.contains(keyword, na=False) | df["name"].str.contains(
                    keyword, na=False
                )
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
        """获取基金列表"""
        return self.search_funds(fund_type=fund_type)

    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: Any | None = None,
        end_date: Any | None = None,
    ) -> pd.DataFrame:
        """获取基准指数数据"""
        ts = self._get_tushare()

        try:
            ts_code = (
                f"{benchmark_code}.SH" if benchmark_code.startswith("0") else f"{benchmark_code}.SZ"
            )

            df = ts.index_daily(
                ts_code=ts_code,
                start_date=start_date.strftime("%Y%m%d") if start_date else None,
                end_date=end_date.strftime("%Y%m%d") if end_date else None,
            )

            if df.empty:
                raise DataNotFoundError(f"指数 {benchmark_code} 不存在")

            df = df.rename(
                columns={
                    "trade_date": "nav_date",
                    "close": "unit_nav",
                }
            )

            df["nav_date"] = pd.to_datetime(df["nav_date"])
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

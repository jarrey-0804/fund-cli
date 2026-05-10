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

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化DataFrame列名"""
        # 常见列名映射
        column_mapping = {
            "日期": "date",
            "时间": "date",
            "股票代码": "code",
            "代码": "code",
            "股票名称": "name",
            "名称": "name",
            "收盘价": "close",
            "开盘价": "open",
            "最高价": "high",
            "最低价": "low",
            "成交量": "volume",
            "成交额": "amount",
            "涨跌幅": "change_pct",
            "市盈率": "pe",
            "市净率": "pb",
            "股息率": "dividend_yield",
            "ROE": "roe",
            "总市值": "total_mv",
            "流通市值": "circ_mv",
            "主力净流入": "main_net_inflow",
            "小单净流入": "small_net_inflow",
            "中单净流入": "medium_net_inflow",
            "大单净流入": "large_net_inflow",
            "超大单净流入": "xlarge_net_inflow",
            "净流入": "net_inflow",
            "当日净流入": "net_inflow",
        }
        # 只重命名存在的列
        rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
        if rename_dict:
            df = df.rename(columns=rename_dict)
        return df

    # ==================== P0 级别接口实现 ====================

    def get_all_fund_names(self) -> pd.DataFrame:
        """
        获取所有基金名称列表

        Returns:
            基金名称列表 DataFrame
            列: code, pinyin_abbr, name, type, pinyin_full
        """
        cache_key = "fund_all_names"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_name_em()
            if df.empty:
                raise DataNotFoundError("无法获取基金名称列表")

            # 标准化列名
            df = df.rename(
                columns={
                    "基金代码": "code",
                    "拼音缩写": "pinyin_abbr",
                    "基金简称": "name",
                    "基金类型": "type",
                    "拼音全称": "pinyin_full",
                }
            )

            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)  # 缓存1天

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金名称列表失败: {e}") from e

    def get_fund_info_ths(self, code: str) -> dict[str, Any]:
        """
        获取同花顺基金基本信息

        Args:
            code: 基金代码

        Returns:
            基金基本信息字典
        """
        cache_key = f"fund_info_ths:{code}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)  # type: ignore[return-value]

        ak = self._get_akshare()
        try:
            df = ak.fund_info_ths(symbol=code)
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 不存在")

            # 转换为字典
            info_dict = dict(zip(df["字段"], df["值"], strict=False))

            result = {
                "code": code,
                "name": info_dict.get("基金简称", ""),
                "full_name": info_dict.get("基金全称", ""),
                "type": info_dict.get("基金类型", ""),
                "investment_type": info_dict.get("投资类型", ""),
                "manager": info_dict.get("基金经理", ""),
                "establish_date": self._parse_date(info_dict.get("成立日期")),
                "establish_scale": info_dict.get("成立规模", ""),
                "management_fee": info_dict.get("管理费", ""),
                "share_scale": info_dict.get("份额规模", ""),
                "custody_fee": info_dict.get("托管费", ""),
                "management_company": info_dict.get("基金管理人", ""),
                "custodian": info_dict.get("基金托管人", ""),
                "subscription_fee": info_dict.get("认购费", ""),
                "purchase_fee": info_dict.get("申购费", ""),
                "redemption_fee": info_dict.get("赎回费", ""),
                "benchmark": info_dict.get("业绩比较基准", ""),
            }

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取同花顺基金信息失败: {e}") from e

    def get_index_fund_info(
        self,
        category: str = "全部",
        indicator: str = "全部",
    ) -> pd.DataFrame:
        """
        获取指数型基金基本信息

        Args:
            category: 分类，可选 {"全部","沪深指数","行业主题","大盘指数","中盘指数","小盘指数","股票指数","债券指数"}
            indicator: 类型，可选 {"全部","被动指数型","增强指数型"}

        Returns:
            指数型基金信息 DataFrame
        """
        cache_key = f"index_fund_info:{category}:{indicator}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_info_index_em(symbol=category, indicator=indicator)
            if df.empty:
                raise DataNotFoundError("无法获取指数型基金信息")

            # 标准化列名
            df = df.rename(
                columns={
                    "基金代码": "code",
                    "基金名称": "name",
                    "单位净值": "unit_nav",
                    "日期": "nav_date",
                    "日增长率": "daily_return",
                    "近1周": "return_1w",
                    "近1月": "return_1m",
                    "近3月": "return_3m",
                    "近6月": "return_6m",
                    "近1年": "return_1y",
                    "近2年": "return_2y",
                    "近3年": "return_3y",
                    "今年来": "return_ytd",
                    "成立来": "return_since_inception",
                    "手续费": "fee",
                    "起购金额": "min_purchase",
                    "跟踪标的": "tracking_target",
                    "跟踪方式": "tracking_method",
                }
            )

            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)  # 缓存1小时

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取指数型基金信息失败: {e}") from e

    def get_fund_overview(self, code: str) -> dict[str, Any]:
        """
        获取基金档案基本概况

        Args:
            code: 基金代码

        Returns:
            基金概况字典
        """
        cache_key = f"fund_overview:{code}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)  # type: ignore[return-value]

        ak = self._get_akshare()
        try:
            df = ak.fund_overview_em(symbol=code)
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 概况不存在")

            # 转换为字典
            result = dict(zip(df["Key"], df["Value"], strict=False))
            result["code"] = code

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金概况失败: {e}") from e

    def get_fund_purchase_status(self) -> pd.DataFrame:
        """
        获取基金申购/赎回状态

        Returns:
            基金申购赎回状态 DataFrame
        """
        cache_key = "fund_purchase_status"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_purchase_em()
            if df.empty:
                raise DataNotFoundError("无法获取基金申购赎回状态")

            # 标准化列名
            df = df.rename(
                columns={
                    "基金代码": "code",
                    "基金简称": "name",
                    "基金类型": "type",
                    "最新净值/万份收益": "latest_nav",
                    "报告时间": "report_time",
                    "申购状态": "purchase_status",
                    "赎回状态": "redemption_status",
                    "下一开放日": "next_open_day",
                    "购买起点": "min_purchase",
                    "日累计限定金额": "daily_limit",
                    "手续费": "fee",
                }
            )

            result = df.reset_index(drop=True)

            # 缓存结果（短期缓存，因为状态可能变化）
            if self._cache:
                self._cache.set(cache_key, result, ttl=1800)  # 缓存30分钟

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金申购赎回状态失败: {e}") from e

    def get_fund_daily_nav(self) -> pd.DataFrame:
        """
        获取开放式基金每日净值(全部)

        Returns:
            每日净值 DataFrame
        """
        cache_key = "fund_daily_nav"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_open_fund_daily_em()
            if df.empty:
                raise DataNotFoundError("无法获取基金每日净值")

            # 标准化列名
            df = df.rename(
                columns={
                    "基金代码": "code",
                    "基金简称": "name",
                    "当日单位净值": "unit_nav",
                    "当日累计净值": "accumulated_nav",
                    "前日单位净值": "prev_unit_nav",
                    "前日累计净值": "prev_accumulated_nav",
                    "日增长值": "daily_change",
                    "日增长率": "daily_return",
                    "申购状态": "purchase_status",
                    "赎回状态": "redemption_status",
                    "手续费": "fee",
                }
            )

            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)  # 缓存1小时

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金每日净值失败: {e}") from e

    def get_etf_spot(self) -> pd.DataFrame:
        """
        获取ETF实时行情

        Returns:
            ETF实时行情 DataFrame
        """
        cache_key = "etf_spot"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_etf_spot_em()
            if df.empty:
                raise DataNotFoundError("无法获取ETF实时行情")

            # 标准化列名（转换为snake_case）
            column_mapping = {
                "代码": "code",
                "名称": "name",
                "最新价": "latest_price",
                "IOPV实时估值": "iopv",
                "基金折价率": "discount_rate",
                "涨跌额": "change_amount",
                "涨跌幅": "change_pct",
                "成交量": "volume",
                "成交额": "turnover",
                "开盘价": "open",
                "最高价": "high",
                "最低价": "low",
                "昨收": "prev_close",
                "换手率": "turnover_rate",
                "量比": "volume_ratio",
                "委比": "order_ratio",
                "外盘": "outer_volume",
                "内盘": "inner_volume",
                "主力净流入-净额": "main_net_inflow",
                "主力净流入-净占比": "main_net_inflow_pct",
                "超大单净流入-净额": "super_large_net_inflow",
                "超大单净流入-净占比": "super_large_net_inflow_pct",
                "大单净流入-净额": "large_net_inflow",
                "大单净流入-净占比": "large_net_inflow_pct",
                "中单净流入-净额": "medium_net_inflow",
                "中单净流入-净占比": "medium_net_inflow_pct",
                "小单净流入-净额": "small_net_inflow",
                "小单净流入-净占比": "small_net_inflow_pct",
                "现手": "current_hand",
                "买一": "bid1",
                "卖一": "ask1",
                "最新份额": "latest_shares",
                "流通市值": "circulating_market_cap",
                "总市值": "total_market_cap",
                "数据日期": "data_date",
                "更新时间": "update_time",
            }

            df = df.rename(columns=column_mapping)
            result = df.reset_index(drop=True)

            # 缓存结果（短期缓存）
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)  # 缓存5分钟

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取ETF实时行情失败: {e}") from e

    def get_fund_category_spot(
        self,
        category: str = "",
        date: str | None = None,
    ) -> pd.DataFrame:
        """
        获取同花顺基金实时行情(按类型)

        Args:
            category: 基金类型，可选 {"股票型","债券型","混合型","ETF","LOF","QDII","保本型","指数型",""}
            date: 日期，格式 YYYYMMDD，默认为今天

        Returns:
            基金实时行情 DataFrame
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        cache_key = f"fund_category_spot:{category}:{date}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_etf_category_ths(symbol=category, date=date)
            if df.empty:
                raise DataNotFoundError(f"无法获取 {category} 类型基金实时行情")

            # 标准化列名
            df = df.rename(
                columns={
                    "基金代码": "code",
                    "基金名称": "name",
                    "当前单位净值": "current_unit_nav",
                    "当前累计净值": "current_accumulated_nav",
                    "前一日单位净值": "prev_unit_nav",
                    "前一日累计净值": "prev_accumulated_nav",
                    "增长值": "change_value",
                    "增长率": "change_rate",
                    "赎回状态": "redemption_status",
                    "申购状态": "purchase_status",
                    "最新交易日": "latest_trade_date",
                    "最新单位净值": "latest_unit_nav",
                    "最新累计净值": "latest_accumulated_nav",
                    "基金类型": "type",
                    "查询日期": "query_date",
                }
            )

            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=1800)  # 缓存30分钟

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金分类实时行情失败: {e}") from e

    def get_etf_spot_ths(self, date: str | None = None) -> pd.DataFrame:
        """
        获取同花顺ETF实时行情

        Args:
            date: 日期，格式 YYYYMMDD，默认为今天

        Returns:
            ETF实时行情 DataFrame
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        cache_key = f"etf_spot_ths:{date}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_etf_spot_ths(date=date)
            if df.empty:
                raise DataNotFoundError("无法获取同花顺ETF实时行情")

            # 标准化列名
            df = df.rename(
                columns={
                    "基金代码": "code",
                    "基金名称": "name",
                    "当前单位净值": "current_unit_nav",
                    "当前累计净值": "current_accumulated_nav",
                    "前一日单位净值": "prev_unit_nav",
                    "前一日累计净值": "prev_accumulated_nav",
                    "增长值": "change_value",
                    "增长率": "change_rate",
                    "赎回状态": "redemption_status",
                    "申购状态": "purchase_status",
                    "最新交易日": "latest_trade_date",
                    "最新单位净值": "latest_unit_nav",
                    "最新累计净值": "latest_accumulated_nav",
                    "基金类型": "type",
                    "查询日期": "query_date",
                }
            )

            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=1800)  # 缓存30分钟

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取同花顺ETF实时行情失败: {e}") from e

    def get_lof_spot(self) -> pd.DataFrame:
        """
        获取LOF实时行情

        Returns:
            LOF实时行情 DataFrame
        """
        cache_key = "lof_spot"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_lof_spot_em()
            if df.empty:
                raise DataNotFoundError("无法获取LOF实时行情")

            # 标准化列名
            df = df.rename(
                columns={
                    "代码": "code",
                    "名称": "name",
                    "最新价": "latest_price",
                    "涨跌额": "change_amount",
                    "涨跌幅": "change_pct",
                    "成交量": "volume",
                    "成交额": "turnover",
                    "开盘价": "open",
                    "最高价": "high",
                    "最低价": "low",
                    "昨收": "prev_close",
                    "换手率": "turnover_rate",
                    "流通市值": "circulating_market_cap",
                    "总市值": "total_market_cap",
                }
            )

            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)  # 缓存5分钟

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取LOF实时行情失败: {e}") from e

    def get_etf_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        获取ETF历史行情

        Args:
            code: ETF代码
            period: 周期，可选 {"daily","weekly","monthly"}
            start: 开始日期，格式 YYYYMMDD
            end: 结束日期，格式 YYYYMMDD

        Returns:
            ETF历史行情 DataFrame
        """
        if end is None:
            end = datetime.now().strftime("%Y%m%d")
        if start is None:
            # 默认获取1年数据
            from datetime import timedelta

            start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        cache_key = f"etf_hist:{code}:{period}:{start}:{end}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_etf_hist_em(
                symbol=code,
                period=period,
                start_date=start,
                end_date=end,
            )
            if df.empty:
                raise DataNotFoundError(f"ETF {code} 历史行情不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                    "振幅": "amplitude",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change_amount",
                    "换手率": "turnover_rate",
                }
            )

            df["code"] = code
            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)  # 缓存1天

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取ETF历史行情失败: {e}") from e

    def get_lof_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        获取LOF历史行情

        Args:
            code: LOF代码
            period: 周期，可选 {"daily","weekly","monthly"}
            start: 开始日期，格式 YYYYMMDD
            end: 结束日期，格式 YYYYMMDD

        Returns:
            LOF历史行情 DataFrame
        """
        if end is None:
            end = datetime.now().strftime("%Y%m%d")
        if start is None:
            from datetime import timedelta

            start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        cache_key = f"lof_hist:{code}:{period}:{start}:{end}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_lof_hist_em(
                symbol=code,
                period=period,
                start_date=start,
                end_date=end,
            )
            if df.empty:
                raise DataNotFoundError(f"LOF {code} 历史行情不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                    "振幅": "amplitude",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change_amount",
                    "换手率": "turnover_rate",
                }
            )

            df["code"] = code
            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取LOF历史行情失败: {e}") from e

    def get_etf_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        获取ETF分时行情

        Args:
            code: ETF代码
            period: 分钟周期，可选 {"1","5","15","30","60"}
            start: 开始日期，格式 YYYYMMDD
            end: 结束日期，格式 YYYYMMDD

        Returns:
            ETF分时行情 DataFrame
        """
        if end is None:
            end = datetime.now().strftime("%Y%m%d")
        if start is None:
            start = datetime.now().strftime("%Y%m%d")

        cache_key = f"etf_minute:{code}:{period}:{start}:{end}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_etf_hist_min_em(
                symbol=code,
                period=period,
                start_date=start,
                end_date=end,
            )
            if df.empty:
                raise DataNotFoundError(f"ETF {code} 分时行情不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "时间": "time",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                    "均价": "avg_price",
                }
            )

            df["code"] = code
            result = df.reset_index(drop=True)

            # 缓存结果（短期缓存）
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)  # 缓存5分钟

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取ETF分时行情失败: {e}") from e

    def get_lof_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        获取LOF分时行情

        Args:
            code: LOF代码
            period: 分钟周期，可选 {"1","5","15","30","60"}
            start: 开始日期，格式 YYYYMMDD
            end: 结束日期，格式 YYYYMMDD

        Returns:
            LOF分时行情 DataFrame
        """
        if end is None:
            end = datetime.now().strftime("%Y%m%d")
        if start is None:
            start = datetime.now().strftime("%Y%m%d")

        cache_key = f"lof_minute:{code}:{period}:{start}:{end}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_lof_hist_min_em(
                symbol=code,
                period=period,
                start_date=start,
                end_date=end,
            )
            if df.empty:
                raise DataNotFoundError(f"LOF {code} 分时行情不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "时间": "time",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "turnover",
                    "均价": "avg_price",
                }
            )

            df["code"] = code
            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取LOF分时行情失败: {e}") from e

    def get_fund_bond_holdings(
        self,
        code: str,
        year: int | None = None,  # type: ignore[override]
    ) -> pd.DataFrame:
        """
        获取基金债券持仓

        Args:
            code: 基金代码
            year: 年份，如 2024，默认为当前年份

        Returns:
            债券持仓 DataFrame
        """
        if year is None:
            year = datetime.now().year

        cache_key = f"fund_bond_holdings:{code}:{year}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_portfolio_bond_hold_em(symbol=code, date=str(year))
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 债券持仓数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "序号": "seq",
                    "债券代码": "bond_code",
                    "债券名称": "bond_name",
                    "占净值比例": "weight",
                    "持仓市值(万元)": "market_value",
                    "季度": "quarter",
                }
            )

            df["fund_code"] = code
            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金债券持仓失败: {e}") from e

    def get_fund_industry_allocation(
        self,
        code: str,
        year: int | None = None,  # type: ignore[override]
    ) -> pd.DataFrame:
        """
        获取基金行业配置

        Args:
            code: 基金代码
            year: 年份，如 2024，默认为当前年份

        Returns:
            行业配置 DataFrame
        """
        if year is None:
            year = datetime.now().year

        cache_key = f"fund_industry_allocation:{code}:{year}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_portfolio_industry_allocation_em(symbol=code, date=str(year))
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 行业配置数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "序号": "seq",
                    "行业类别": "industry",
                    "占净值比例": "weight",
                    "市值": "market_value",
                    "截止时间": "report_date",
                }
            )

            df["fund_code"] = code
            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金行业配置失败: {e}") from e

    def get_fund_portfolio_change(
        self,
        code: str,
        indicator: str = "累计买入",
        year: int | None = None,  # type: ignore[override]
    ) -> pd.DataFrame:
        """
        获取基金重大变动(累计买入/卖出)

        Args:
            code: 基金代码
            indicator: 指标类型，可选 {"累计买入","累计卖出"}
            year: 年份，如 2024，默认为当前年份

        Returns:
            重大变动 DataFrame
        """
        if year is None:
            year = datetime.now().year

        cache_key = f"fund_portfolio_change:{code}:{indicator}:{year}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_portfolio_change_em(
                symbol=code,
                indicator=indicator,
                date=str(year),
            )
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 重大变动数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "序号": "seq",
                    "股票代码": "stock_code",
                    "股票名称": "stock_name",
                    "本期累计买入/卖出金额": "amount",
                    "占期初基金资产净值比例": "weight",
                    "季度": "quarter",
                }
            )

            df["fund_code"] = code
            df["indicator"] = indicator
            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金重大变动失败: {e}") from e

    def get_all_fund_managers(self) -> pd.DataFrame:
        """
        获取基金经理大全

        Returns:
            基金经理列表 DataFrame
        """
        cache_key = "fund_all_managers"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.fund_manager_em()
            if df.empty:
                raise DataNotFoundError("无法获取基金经理数据")

            # 标准化列名
            df = df.rename(
                columns={
                    "序号": "seq",
                    "姓名": "name",
                    "所属公司": "company",
                    "现任基金代码": "current_fund_codes",
                    "现任基金": "current_funds",
                    "累计从业时间": "total_experience",
                    "现任基金资产总规模": "total_scale",
                    "现任基金最佳回报": "best_return",
                }
            )

            result = df.reset_index(drop=True)

            # 缓存结果
            if self._cache:
                self._cache.set(cache_key, result, ttl=86400)  # 缓存1天

            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金经理大全失败: {e}") from e

    # ==================== P2 辅助分析接口 ====================

    # -------------------- 宏观经济数据(22个) --------------------

    def get_macro_leverage_ratio(self) -> pd.DataFrame:
        """
        获取中国宏观杠杆率数据

        Returns:
            宏观杠杆率 DataFrame
        """
        cache_key = "macro:leverage_ratio"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_cnbs()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取宏观杠杆率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取宏观杠杆率失败: {e}") from e

    def get_enterprise_price_index(self) -> pd.DataFrame:
        """
        获取企业商品价格指数

        Returns:
            企业商品价格指数 DataFrame
        """
        cache_key = "macro:enterprise_price_index"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_qyspjg()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取企业商品价格指数数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取企业商品价格指数失败: {e}") from e

    def get_fdi_data(self) -> pd.DataFrame:
        """
        获取外商直接投资数据

        Returns:
            FDI数据 DataFrame
        """
        cache_key = "macro:fdi_data"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_fdi()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取外商直接投资数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取FDI数据失败: {e}") from e

    def get_lpr_data(self) -> pd.DataFrame:
        """
        获取LPR品种数据

        Returns:
            LPR数据 DataFrame
        """
        cache_key = "macro:lpr_data"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_lpr()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取LPR数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取LPR数据失败: {e}") from e

    def get_urban_unemployment(self) -> pd.DataFrame:
        """
        获取城镇调查失业率

        Returns:
            失业率数据 DataFrame
        """
        cache_key = "macro:urban_unemployment"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_urban_unemployment()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取城镇失业率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取城镇失业率失败: {e}") from e

    def get_social_financing(self) -> pd.DataFrame:
        """
        获取社会融资规模增量统计

        Returns:
            社融数据 DataFrame
        """
        cache_key = "macro:social_financing"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_shrzgm()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取社会融资规模数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取社会融资规模失败: {e}") from e

    def get_gdp_yearly(self) -> pd.DataFrame:
        """
        获取中国GDP年率数据

        Returns:
            GDP年率 DataFrame
        """
        cache_key = "macro:gdp_yearly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_gdp_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取GDP年率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取GDP年率失败: {e}") from e

    def get_gdp_quarterly(self) -> pd.DataFrame:
        """
        获取中国GDP季度数据

        Returns:
            GDP季度数据 DataFrame
        """
        cache_key = "macro:gdp_quarterly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_gdp_quarterly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取GDP季度数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取GDP季度数据失败: {e}") from e

    def get_cpi_yearly(self) -> pd.DataFrame:
        """
        获取中国CPI年率数据

        Returns:
            CPI年率 DataFrame
        """
        cache_key = "macro:cpi_yearly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_cpi_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取CPI年率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取CPI年率失败: {e}") from e

    def get_cpi_monthly(self) -> pd.DataFrame:
        """
        获取中国CPI月率数据

        Returns:
            CPI月率 DataFrame
        """
        cache_key = "macro:cpi_monthly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_cpi_monthly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取CPI月率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取CPI月率失败: {e}") from e

    def get_ppi_yearly(self) -> pd.DataFrame:
        """
        获取中国PPI年率数据

        Returns:
            PPI年率 DataFrame
        """
        cache_key = "macro:ppi_yearly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_ppi_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取PPI年率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取PPI年率失败: {e}") from e

    def get_ppi_monthly(self) -> pd.DataFrame:
        """
        获取中国PPI月率数据

        Returns:
            PPI月率 DataFrame
        """
        cache_key = "macro:ppi_monthly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_ppi_monthly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取PPI月率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取PPI月率失败: {e}") from e

    def get_exports_yearly(self) -> pd.DataFrame:
        """
        获取出口年率数据

        Returns:
            出口年率 DataFrame
        """
        cache_key = "macro:exports_yearly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_exports_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取出口年率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取出口年率失败: {e}") from e

    def get_imports_yearly(self) -> pd.DataFrame:
        """
        获取进口年率数据

        Returns:
            进口年率 DataFrame
        """
        cache_key = "macro:imports_yearly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_imports_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取进口年率数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取进口年率失败: {e}") from e

    def get_trade_balance(self) -> pd.DataFrame:
        """
        获取贸易帐数据

        Returns:
            贸易帐 DataFrame
        """
        cache_key = "macro:trade_balance"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_trade_balance()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取贸易帐数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取贸易帐失败: {e}") from e

    def get_industrial_production(self) -> pd.DataFrame:
        """
        获取工业增加值增长数据

        Returns:
            工业增加值 DataFrame
        """
        cache_key = "macro:industrial_production"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_industrial_production_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取工业增加值数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取工业增加值失败: {e}") from e

    def get_pmi_official(self) -> pd.DataFrame:
        """
        获取官方制造业PMI数据

        Returns:
            官方PMI DataFrame
        """
        cache_key = "macro:pmi_official"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_pmi_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取官方PMI数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取官方PMI失败: {e}") from e

    def get_pmi_caixin(self) -> pd.DataFrame:
        """
        获取财新制造业PMI数据

        Returns:
            财新PMI DataFrame
        """
        cache_key = "macro:pmi_caixin"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_cx_pmi_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取财新PMI数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取财新PMI失败: {e}") from e

    def get_services_pmi(self) -> pd.DataFrame:
        """
        获取财新服务业PMI数据

        Returns:
            服务业PMI DataFrame
        """
        cache_key = "macro:services_pmi"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_cx_services_pmi()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取服务业PMI数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取服务业PMI失败: {e}") from e

    def get_non_manufacturing_pmi(self) -> pd.DataFrame:
        """
        获取官方非制造业PMI数据

        Returns:
            非制造业PMI DataFrame
        """
        cache_key = "macro:non_manufacturing_pmi"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_non_man_pmi()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取非制造业PMI数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取非制造业PMI失败: {e}") from e

    def get_m2_yearly(self) -> pd.DataFrame:
        """
        获取M2货币供应年率数据

        Returns:
            M2数据 DataFrame
        """
        cache_key = "macro:m2_yearly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_m2_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取M2货币供应数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取M2数据失败: {e}") from e

    def get_new_loan(self) -> pd.DataFrame:
        """
        获取新增人民币贷款数据

        Returns:
            新增贷款 DataFrame
        """
        cache_key = "macro:new_loan"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_new_loan()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取新增贷款数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取新增贷款失败: {e}") from e

    def get_retail_sales_yearly(self) -> pd.DataFrame:
        """
        获取社会消费品零售总额年率数据

        Returns:
            零售销售 DataFrame
        """
        cache_key = "macro:retail_sales_yearly"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_retail_sales_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取零售销售数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取零售销售失败: {e}") from e

    def get_fixed_asset_investment(self) -> pd.DataFrame:
        """
        获取固定资产投资年率数据

        Returns:
            固定资产投资 DataFrame
        """
        cache_key = "macro:fixed_asset_investment"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_fixed_asset_investment_yearly()

            if df is None or df.empty:
                raise DataNotFoundError("无法获取固定资产投资数据")

            # 列名标准化
            df = self._standardize_columns(df)

            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)

            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取固定资产投资失败: {e}") from e

    # -------------------- 利率数据(8个) --------------------

    def get_china_interest_rate(self) -> pd.DataFrame:
        """
        获取中国央行利率决议数据

        Returns:
            中国利率 DataFrame
        """
        cache_key = "interest_rate:china"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_bank_china_interest_rate()
            if df.empty:
                raise DataNotFoundError("中国央行利率数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "利率": "rate",
                    "利率类型": "rate_type",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取中国利率失败: {e}") from e

    def get_usa_interest_rate(self) -> pd.DataFrame:
        """
        获取美联储利率决议数据

        Returns:
            美国利率 DataFrame
        """
        cache_key = "interest_rate:usa"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_bank_usa_interest_rate()
            if df.empty:
                raise DataNotFoundError("美联储利率数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "利率": "rate",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取美国利率失败: {e}") from e

    def get_euro_interest_rate(self) -> pd.DataFrame:
        """
        获取欧洲央行利率决议数据

        Returns:
            欧元区利率 DataFrame
        """
        cache_key = "interest_rate:euro"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_bank_euro_interest_rate()
            if df.empty:
                raise DataNotFoundError("欧洲央行利率数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "利率": "rate",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取欧元区利率失败: {e}") from e

    def get_japan_interest_rate(self) -> pd.DataFrame:
        """
        获取日本央行利率决议数据

        Returns:
            日本利率 DataFrame
        """
        cache_key = "interest_rate:japan"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_bank_japan_interest_rate()
            if df.empty:
                raise DataNotFoundError("日本央行利率数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "利率": "rate",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取日本利率失败: {e}") from e

    def get_uk_interest_rate(self) -> pd.DataFrame:
        """
        获取英国央行利率决议数据

        Returns:
            英国利率 DataFrame
        """
        cache_key = "interest_rate:uk"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_bank_uk_interest_rate()
            if df.empty:
                raise DataNotFoundError("英国央行利率数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "利率": "rate",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取英国利率失败: {e}") from e

    def get_shibor(self) -> pd.DataFrame:
        """
        获取SHIBOR利率数据

        Returns:
            SHIBOR DataFrame
        """
        cache_key = "interest_rate:shibor"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_shibor()
            if df.empty:
                raise DataNotFoundError("SHIBOR利率数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "O/N": "overnight",
                    "1W": "week_1",
                    "2W": "week_2",
                    "1M": "month_1",
                    "3M": "month_3",
                    "6M": "month_6",
                    "9M": "month_9",
                    "1Y": "year_1",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取SHIBOR失败: {e}") from e

    def get_shibor_lpr(self) -> pd.DataFrame:
        """
        获取SHIBOR-LPR数据

        Returns:
            SHIBOR-LPR DataFrame
        """
        cache_key = "interest_rate:shibor_lpr"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_shibor_lpr()
            if df.empty:
                raise DataNotFoundError("SHIBOR-LPR数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "LPR1Y": "lpr_1y",
                    "LPR5Y": "lpr_5y",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取SHIBOR-LPR失败: {e}") from e

    def get_hibor(self) -> pd.DataFrame:
        """
        获取HIBOR利率数据

        Returns:
            HIBOR DataFrame
        """
        cache_key = "interest_rate:hibor"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.macro_china_hibor()
            if df.empty:
                raise DataNotFoundError("HIBOR利率数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "O/N": "overnight",
                    "1W": "week_1",
                    "2W": "week_2",
                    "1M": "month_1",
                    "3M": "month_3",
                    "6M": "month_6",
                    "9M": "month_9",
                    "1Y": "year_1",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=3600)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取HIBOR失败: {e}") from e

    # -------------------- 行业板块(5个) --------------------

    def get_industry_boards(self) -> pd.DataFrame:
        """
        获取行业板块名称列表

        Returns:
            行业板块列表 DataFrame
        """
        cache_key = "industry_boards:list"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_board_industry_name_em()
            if df.empty:
                raise DataNotFoundError("行业板块数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "板块名称": "name",
                    "板块代码": "code",
                    "最新价": "price",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change",
                    "成交量": "volume",
                    "成交额": "amount",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取行业板块列表失败: {e}") from e

    def get_industry_board_hist(
        self,
        code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        获取行业板块历史行情

        Args:
            code: 板块代码
            period: 周期 (daily/weekly/monthly)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            行业板块历史数据 DataFrame
        """
        cache_key = f"industry_board_hist:{code}:{period}:{start_date}:{end_date}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_board_industry_hist_em(
                symbol=code, period=period, start_date=start_date, end_date=end_date
            )
            if df.empty:
                raise DataNotFoundError(f"行业板块 {code} 历史数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change",
                    "换手率": "turnover",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取行业板块历史数据失败: {e}") from e

    def get_concept_boards(self) -> pd.DataFrame:
        """
        获取概念板块名称列表

        Returns:
            概念板块列表 DataFrame
        """
        cache_key = "concept_boards:list"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_board_concept_name_em()
            if df.empty:
                raise DataNotFoundError("概念板块数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "板块名称": "name",
                    "板块代码": "code",
                    "最新价": "price",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change",
                    "成交量": "volume",
                    "成交额": "amount",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取概念板块列表失败: {e}") from e

    def get_concept_board_hist(
        self,
        code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        获取概念板块历史行情

        Args:
            code: 板块代码
            period: 周期 (daily/weekly/monthly)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            概念板块历史数据 DataFrame
        """
        cache_key = f"concept_board_hist:{code}:{period}:{start_date}:{end_date}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_board_concept_hist_em(
                symbol=code, period=period, start_date=start_date, end_date=end_date
            )
            if df.empty:
                raise DataNotFoundError(f"概念板块 {code} 历史数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change",
                    "换手率": "turnover",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取概念板块历史数据失败: {e}") from e

    def get_sector_fund_flow(self, period: str = "今日") -> pd.DataFrame:
        """
        获取板块资金流向

        Args:
            period: 统计周期 ("今日","5日","10日")

        Returns:
            板块资金流向 DataFrame
        """
        cache_key = f"sector_fund_flow:{period}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_sector_spot(indicator=period)
            if df.empty:
                raise DataNotFoundError(f"板块资金流向数据不存在 (周期: {period})")

            # 标准化列名
            df = df.rename(
                columns={
                    "名称": "name",
                    "今日涨跌幅": "change_pct",
                    "今日主力净流入": "main_inflow",
                    "今日小单净流入": "small_inflow",
                    "今日中单净流入": "medium_inflow",
                    "今日大单净流入": "large_inflow",
                    "今日超大单净流入": "xlarge_inflow",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取板块资金流向失败: {e}") from e

    # -------------------- 债券数据(7个) --------------------

    def get_china_us_bond_yield(self) -> pd.DataFrame:
        """
        获取中美国债收益率数据

        Returns:
            中美国债收益率 DataFrame
        """
        cache_key = "bond_yield:china_us"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.bond_zh_us_rate()
            if df.empty:
                raise DataNotFoundError("中美国债收益率数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "中国国债收益率2Y": "china_2y",
                    "中国国债收益率5Y": "china_5y",
                    "中国国债收益率10Y": "china_10y",
                    "中国国债收益率30Y": "china_30y",
                    "美国国债收益率2Y": "usa_2y",
                    "美国国债收益率5Y": "usa_5y",
                    "美国国债收益率10Y": "usa_10y",
                    "美国国债收益率30Y": "usa_30y",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取中美国债收益率失败: {e}") from e

    def get_bond_yield_curve(
        self,
        bond_type: str = "国债",
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        获取收盘收益率曲线历史数据

        Args:
            bond_type: 债券类型 ("国债","国开债","农发债","进出口行债")
            period: 周期
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            收益率曲线 DataFrame
        """
        cache_key = f"bond_yield_curve:{bond_type}:{period}:{start_date}:{end_date}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.bond_china_close_return(
                symbol=bond_type, period=period, start_date=start_date, end_date=end_date
            )
            if df.empty:
                raise DataNotFoundError(f"债券收益率曲线数据不存在 (类型: {bond_type})")

            # 标准化列名
            df = df.rename(
                columns={
                    "date": "date",
                    "1y": "yield_1y",
                    "2y": "yield_2y",
                    "3y": "yield_3y",
                    "5y": "yield_5y",
                    "7y": "yield_7y",
                    "10y": "yield_10y",
                    "30y": "yield_30y",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取债券收益率曲线失败: {e}") from e

    def get_bond_spot_quote(self) -> pd.DataFrame:
        """
        获取现券市场做市报价

        Returns:
            现券报价 DataFrame
        """
        cache_key = "bond_spot_quote:list"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.bond_spot_quote()
            if df.empty:
                raise DataNotFoundError("现券报价数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "债券简称": "name",
                    "债券代码": "code",
                    "买入价": "bid_price",
                    "卖出价": "ask_price",
                    "到期收益率": "yield",
                    "剩余期限": "remaining_term",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取现券报价失败: {e}") from e

    def get_convertible_bonds(self) -> pd.DataFrame:
        """
        获取可转债数据一览表

        Returns:
            可转债列表 DataFrame
        """
        cache_key = "convertible_bonds:list"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.bond_cb_info_jsl()
            if df.empty:
                raise DataNotFoundError("可转债数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "债券代码": "code",
                    "债券简称": "name",
                    "现价": "price",
                    "涨跌幅": "change_pct",
                    "正股代码": "stock_code",
                    "正股名称": "stock_name",
                    "正股价": "stock_price",
                    "转股价": "convert_price",
                    "转股价值": "convert_value",
                    "溢价率": "premium_rate",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取可转债列表失败: {e}") from e

    def get_convertible_bond_detail(self, code: str) -> pd.DataFrame:
        """
        获取可转债详情数据

        Args:
            code: 可转债代码

        Returns:
            可转债详情 DataFrame
        """
        cache_key = f"convertible_bond_detail:{code}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.bond_cb_detail_jsl(symbol=code)
            if df.empty:
                raise DataNotFoundError(f"可转债 {code} 详情数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "项目": "item",
                    "值": "value",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取可转债详情失败: {e}") from e

    def get_bond_spot(self, code: str) -> pd.DataFrame:
        """
        获取沪深债券实时行情

        Args:
            code: 债券代码

        Returns:
            债券实时行情 DataFrame
        """
        cache_key = f"bond_spot:{code}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.bond_zh_hs_cov_spot(symbol=code)
            if df.empty:
                raise DataNotFoundError(f"债券 {code} 实时行情不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "债券代码": "code",
                    "债券简称": "name",
                    "最新价": "price",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change",
                    "成交量": "volume",
                    "成交额": "amount",
                    "最高": "high",
                    "最低": "low",
                    "今开": "open",
                    "昨收": "prev_close",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取债券实时行情失败: {e}") from e

    def get_bond_hist(
        self,
        code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        获取沪深债券历史行情

        Args:
            code: 债券代码
            period: 周期 (daily/weekly/monthly)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)

        Returns:
            债券历史数据 DataFrame
        """
        cache_key = f"bond_hist:{code}:{period}:{start_date}:{end_date}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.bond_zh_hs_cov_hist(
                symbol=code, period=period, start_date=start_date, end_date=end_date
            )
            if df.empty:
                raise DataNotFoundError(f"债券 {code} 历史数据不存在")

            # 标准化列名
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                    "成交额": "amount",
                    "振幅": "amplitude",
                    "涨跌幅": "change_pct",
                    "涨跌额": "change",
                }
            )

            result = df.reset_index(drop=True)
            if self._cache:
                self._cache.set(cache_key, result, ttl=300)
            return result

        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取债券历史数据失败: {e}") from e

    # -------------------- 估值指标(5个) --------------------

    def get_a_share_valuation(self) -> pd.DataFrame:
        """获取A股等权重与中位数市盈率/市净率"""
        cache_key = "a_share_valuation"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_a_pe_and_pb()
            if df is None or df.empty:
                raise DataNotFoundError("无法获取A股估值数据")
            df = self._standardize_columns(df)
            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)
            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取A股估值失败: {e}") from e

    def get_stock_valuation_lg(self, code: str) -> pd.DataFrame:
        """获取个股估值数据(乐咕乐股)"""
        cache_key = f"stock_valuation_lg:{code}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_a_indicator_lg(symbol=code)
            if df is None or df.empty:
                raise DataNotFoundError(f"无法获取个股估值数据: {code}")
            df = self._standardize_columns(df)
            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)
            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取个股估值失败: {e}") from e

    def get_index_valuation(self, code: str, indicator: str = "pe") -> pd.DataFrame:
        """获取指数估值历史数据(乐咕乐股)"""
        cache_key = f"index_valuation:{code}:{indicator}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.index_value_hist_funddb(symbol=code, indicator=indicator)
            if df is None or df.empty:
                raise DataNotFoundError(f"无法获取指数估值数据: {code}")
            df = self._standardize_columns(df)
            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)
            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取指数估值失败: {e}") from e

    def get_market_pe_lg(self, code: str) -> pd.DataFrame:
        """获取指数市盈率数据(乐咕乐股)"""
        cache_key = f"market_pe_lg:{code}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_market_pe_lg(symbol=code)
            if df is None or df.empty:
                raise DataNotFoundError(f"无法获取市场PE数据: {code}")
            df = self._standardize_columns(df)
            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)
            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取市场PE失败: {e}") from e

    def get_market_pb_lg(self, code: str) -> pd.DataFrame:
        """获取指数市净率数据(乐咕乐股)"""
        cache_key = f"market_pb_lg:{code}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_market_pb_lg(symbol=code)
            if df is None or df.empty:
                raise DataNotFoundError(f"无法获取市场PB数据: {code}")
            df = self._standardize_columns(df)
            if self._cache:
                self._cache.set(cache_key, df, ttl=86400)
            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取市场PB失败: {e}") from e

    # -------------------- 资金流向(3个) --------------------

    def get_market_fund_flow(self) -> pd.DataFrame:
        """获取大盘资金流向数据"""
        cache_key = "market_fund_flow"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_market_fund_flow()
            if df is None or df.empty:
                raise DataNotFoundError("无法获取大盘资金流向数据")
            df = self._standardize_columns(df)
            if self._cache:
                self._cache.set(cache_key, df, ttl=60)
            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取大盘资金流向失败: {e}") from e

    def get_stock_fund_flow(self, code: str, market: str = "sh") -> pd.DataFrame:
        """获取个股资金流向数据"""
        cache_key = f"stock_fund_flow:{code}:{market}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_individual_fund_flow(stock=code, market=market)
            if df is None or df.empty:
                raise DataNotFoundError(f"无法获取个股资金流向数据: {code}")
            df = self._standardize_columns(df)
            if self._cache:
                self._cache.set(cache_key, df, ttl=60)
            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取个股资金流向失败: {e}") from e

    def get_north_fund_flow(self, market: str = "北向资金") -> pd.DataFrame:
        """获取北向资金流向数据"""
        cache_key = f"north_fund_flow:{market}"
        if self._cache and self._cache.exists(cache_key):
            return self._cache.get(cache_key)

        ak = self._get_akshare()
        try:
            df = ak.stock_hsgt_north_net_flow_in_em(symbol=market)
            if df is None or df.empty:
                raise DataNotFoundError(f"无法获取北向资金流向数据: {market}")
            df = self._standardize_columns(df)
            if self._cache:
                self._cache.set(cache_key, df, ttl=60)
            return df
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取北向资金流向失败: {e}") from e

    # ==================== P1 接口实现 ====================

    # ---------- 基金公司/规模 (5个) ----------

    def get_fund_company_aum(self) -> pd.DataFrame:
        """
        基金公司管理规模排名

        Returns:
            基金公司规模排名 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_aum_em()
            if df.empty:
                raise DataNotFoundError("基金公司规模数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金公司规模排名失败: {e}") from e

    def get_fund_aum_trend(self) -> pd.DataFrame:
        """
        基金市场管理规模走势

        Returns:
            规模走势 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_aum_trend_em()
            if df.empty:
                raise DataNotFoundError("基金规模走势数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金规模走势失败: {e}") from e

    def get_fund_company_aum_history(self, year: int | None = None) -> pd.DataFrame:
        """
        基金公司历年管理规模

        Args:
            year: 年份，如 2023

        Returns:
            历年规模数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_aum_hist_em(year=year)
            if df.empty:
                raise DataNotFoundError(f"{year}年基金公司规模数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金公司历年规模失败: {e}") from e

    def get_fund_scale_change(self) -> pd.DataFrame:
        """
        规模变动(全市场汇总)

        Returns:
            规模变动数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_scale_change_em()
            if df.empty:
                raise DataNotFoundError("基金规模变动数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金规模变动失败: {e}") from e

    def get_fund_holder_structure(self) -> pd.DataFrame:
        """
        持有人结构

        Returns:
            持有人结构数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_hold_structure_em()
            if df.empty:
                raise DataNotFoundError("基金持有人结构数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金持有人结构失败: {e}") from e

    # ---------- 基金评级 (4个) ----------

    def get_fund_ratings(self) -> pd.DataFrame:
        """
        基金评级总汇

        Returns:
            基金评级汇总 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_rating_all()
            if df.empty:
                raise DataNotFoundError("基金评级数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金评级总汇失败: {e}") from e

    def get_fund_rating_sh(self, date: str | None = None) -> pd.DataFrame:
        """
        上海证券评级

        Args:
            date: 日期，格式 YYYYMMDD

        Returns:
            上海证券评级数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_rating_sh(date=date)
            if df.empty:
                raise DataNotFoundError(f"上海证券评级数据不存在 (日期: {date})")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取上海证券评级失败: {e}") from e

    def get_fund_rating_zs(self, date: str | None = None) -> pd.DataFrame:
        """
        招商证券评级

        Args:
            date: 日期，格式 YYYYMMDD

        Returns:
            招商证券评级数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_rating_zs(date=date)
            if df.empty:
                raise DataNotFoundError(f"招商证券评级数据不存在 (日期: {date})")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取招商证券评级失败: {e}") from e

    def get_fund_rating_ja(self, date: str | None = None) -> pd.DataFrame:
        """
        济安金信评级

        Args:
            date: 日期，格式 YYYYMMDD

        Returns:
            济安金信评级数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_rating_ja(date=date)
            if df.empty:
                raise DataNotFoundError(f"济安金信评级数据不存在 (日期: {date})")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取济安金信评级失败: {e}") from e

    # ---------- 基金分红/拆分 (3个) ----------

    def get_fund_dividends(
        self,
        year: int | None = None,
        fund_type: str | None = None,
        page: int = -1,
    ) -> pd.DataFrame:
        """
        基金分红

        Args:
            year: 年份
            fund_type: 基金类型
            page: 页码，-1表示全部

        Returns:
            基金分红数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_fh_em(year=year, typ=fund_type, page=page)
            if df.empty:
                raise DataNotFoundError("基金分红数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金分红数据失败: {e}") from e

    def get_fund_splits(
        self,
        year: int | None = None,
        fund_type: str | None = None,
        page: int = -1,
    ) -> pd.DataFrame:
        """
        基金拆分

        Args:
            year: 年份
            fund_type: 基金类型
            page: 页码，-1表示全部

        Returns:
            基金拆分数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_cf_em(year=year, typ=fund_type, page=page)
            if df.empty:
                raise DataNotFoundError("基金拆分数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金拆分数据失败: {e}") from e

    def get_fund_dividend_rank(self) -> pd.DataFrame:
        """
        累计分红排行

        Returns:
            累计分红排行 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_fh_rank_em()
            if df.empty:
                raise DataNotFoundError("基金累计分红排行数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金累计分红排行失败: {e}") from e

    # ---------- 基金排行 (5个) ----------

    def get_fund_rank_by_type(self, fund_type: str = "全部") -> pd.DataFrame:
        """
        开放式基金排行

        Args:
            fund_type: 基金类型，可选：全部/股票型/混合型/债券型/指数型/QDII/LOF/FOF

        Returns:
            基金排行 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_open_fund_rank_em(symbol=fund_type)
            if df.empty:
                raise DataNotFoundError(f"{fund_type}类型基金排行数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金排行失败: {e}") from e

    def get_exchange_fund_rank(self) -> pd.DataFrame:
        """
        场内交易基金排行

        Returns:
            场内基金排行 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_exchange_rank_em()
            if df.empty:
                raise DataNotFoundError("场内交易基金排行数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取场内基金排行失败: {e}") from e

    def get_money_fund_rank(self) -> pd.DataFrame:
        """
        货币型基金排行

        Returns:
            货币基金排行 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_money_rank_em()
            if df.empty:
                raise DataNotFoundError("货币型基金排行数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取货币基金排行失败: {e}") from e

    def get_lcx_fund_rank(self) -> pd.DataFrame:
        """
        理财基金排行

        Returns:
            理财基金排行 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_lcx_rank_em()
            if df.empty:
                raise DataNotFoundError("理财基金排行数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取理财基金排行失败: {e}") from e

    def get_hk_fund_rank(self) -> pd.DataFrame:
        """
        香港基金排行

        Returns:
            香港基金排行 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_hk_rank_em()
            if df.empty:
                raise DataNotFoundError("香港基金排行数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取香港基金排行失败: {e}") from e

    # ---------- 基金业绩/分析 (3个) ----------

    def get_fund_achievement(self, code: str) -> pd.DataFrame:
        """
        基金业绩(年度+阶段)

        Args:
            code: 基金代码

        Returns:
            基金业绩数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_individual_achievement_xq(symbol=code)
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 业绩数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金业绩失败: {e}") from e

    def get_fund_risk_analysis(self, code: str) -> pd.DataFrame:
        """
        基金数据分析(夏普/回撤)

        Args:
            code: 基金代码

        Returns:
            基金风险分析数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_individual_analysis_xq(symbol=code)
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 风险分析数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金风险分析失败: {e}") from e

    def get_fund_profit_probability(self, code: str) -> pd.DataFrame:
        """
        盈利概率

        Args:
            code: 基金代码

        Returns:
            盈利概率数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_individual_profit_probability_xq(symbol=code)
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 盈利概率数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金盈利概率失败: {e}") from e

    # ---------- 资产配置 (1个) ----------

    def get_fund_asset_allocation(self, code: str, date: str | None = None) -> pd.DataFrame:
        """
        基金资产配置

        Args:
            code: 基金代码
            date: 财报日期，格式 YYYYMMDD

        Returns:
            资产配置数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.fund_individual_detail_hold_xq(symbol=code, date=date)
            if df.empty:
                raise DataNotFoundError(f"基金 {code} 资产配置数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取基金资产配置失败: {e}") from e

    # ---------- 市场指数扩展 (6个) ----------

    def get_index_spot_em(self, category: str = "沪深重要指数") -> pd.DataFrame:
        """
        东财指数实时行情

        Args:
            category: 指数类别，可选：沪深重要指数/上证系列指数/深证系列指数/中证系列指数

        Returns:
            指数实时行情 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.stock_zh_index_spot_em(symbol=category)
            if df.empty:
                raise DataNotFoundError(f"{category}指数实时行情数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取东财指数实时行情失败: {e}") from e

    def get_index_spot_sina(self) -> pd.DataFrame:
        """
        新浪指数实时行情

        Returns:
            指数实时行情 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.stock_zh_index_spot_sina()
            if df.empty:
                raise DataNotFoundError("新浪指数实时行情数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取新浪指数实时行情失败: {e}") from e

    def get_index_daily_tx(
        self, code: str, start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """
        腾讯指数历史

        Args:
            code: 指数代码，如 "sh000001"
            start: 开始日期，格式 YYYYMMDD
            end: 结束日期，格式 YYYYMMDD

        Returns:
            指数历史数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.stock_zh_index_daily_tx(symbol=code, start_date=start, end_date=end)
            if df.empty:
                raise DataNotFoundError(f"指数 {code} 历史数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取腾讯指数历史失败: {e}") from e

    def get_index_daily_em(
        self, code: str, start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """
        东财指数历史

        Args:
            code: 指数代码，如 "sz399552"
            start: 开始日期，格式 YYYYMMDD
            end: 结束日期，格式 YYYYMMDD

        Returns:
            指数历史数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.stock_zh_index_daily_em(symbol=code, start_date=start, end_date=end)
            if df.empty:
                raise DataNotFoundError(f"指数 {code} 历史数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取东财指数历史失败: {e}") from e

    def get_index_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        指数通用历史

        Args:
            code: 指数代码
            period: 周期，可选：daily/weekly/monthly
            start: 开始日期，格式 YYYYMMDD
            end: 结束日期，格式 YYYYMMDD

        Returns:
            指数历史数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.index_zh_a_hist(symbol=code, period=period, start_date=start, end_date=end)
            if df.empty:
                raise DataNotFoundError(f"指数 {code} 历史数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取指数通用历史失败: {e}") from e

    def get_index_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        指数分时

        Args:
            code: 指数代码
            period: 周期，可选：1/5/15/30/60
            start: 开始日期，格式 YYYYMMDD
            end: 结束日期，格式 YYYYMMDD

        Returns:
            指数分时数据 DataFrame
        """
        ak = self._get_akshare()
        try:
            df = ak.index_zh_a_hist_min_em(
                symbol=code, period=period, start_date=start, end_date=end
            )
            if df.empty:
                raise DataNotFoundError(f"指数 {code} 分时数据不存在")
            return df.reset_index(drop=True)
        except DataNotFoundError:
            raise
        except Exception as e:
            raise DataSourceError(f"获取指数分时数据失败: {e}") from e

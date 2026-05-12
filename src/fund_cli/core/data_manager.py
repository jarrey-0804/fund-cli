"""
数据管理器

统一管理数据源，提供数据访问接口。
"""

import logging
from datetime import date
from typing import Any

import pandas as pd

from fund_cli.config import get_config
from fund_cli.core.data_gateway import DataSourceGateway
from fund_cli.data.adapters.akshare_adapter import AKShareAdapter
from fund_cli.data.base import DataSourceAdapter, DataSourceError
from fund_cli.data.cache import DataCache
from fund_cli.data.normalizer import DataNormalizer

logger = logging.getLogger(__name__)


class DataManager:
    """
    数据管理器

    统一管理多个数据源，提供：
    - 自动数据源选择
    - 数据缓存
    - 统一的数据访问接口
    - 多数据源注册和切换
    """

    def __init__(
        self,
        cache: DataCache | None = None,
        primary_source: str | None = None,
    ):
        """
        初始化数据管理器

        Args:
            cache: 缓存管理器
            primary_source: 主数据源名称，默认使用配置中的设置
        """
        self.config = get_config()
        self._cache = cache or DataCache(
            cache_dir=self.config.data.cache_dir,
            default_ttl=self.config.data.cache_ttl,
        )
        self._primary_source = primary_source or self.config.data.primary_source
        self._adapters: dict[str, DataSourceAdapter] = {}
        self._gateway = DataSourceGateway()

        # 初始化数据源
        self._init_adapters()

    def _init_adapters(self) -> None:
        """
        初始化数据源适配器

        根据配置自动检测并注册可用的数据源适配器：
        - AKShare（默认数据源，零配置）
        - Tushare（需要 FUND_DATA_TUSHARE_TOKEN）
        - Wind（需要 WindPy 库且 wind_enabled=True）
        """
        # AKShare（默认数据源，零配置）
        if self.config.data.akshare_enabled:
            try:
                self._adapters["akshare"] = AKShareAdapter(cache=self._cache)
                self._gateway.register_adapter("akshare", self._adapters["akshare"])
                logger.info("已注册 AKShareAdapter")
            except Exception as e:
                logger.error("注册 AKShareAdapter 失败: %s", e)

        # Tushare（需要 Token）
        if self.config.data.tushare_token:
            try:
                from fund_cli.data.adapters.tushare_adapter import TushareAdapter

                self._adapters["tushare"] = TushareAdapter(cache=self._cache)
                self._gateway.register_adapter("tushare", self._adapters["tushare"])
                logger.info("已注册 TushareAdapter")
            except ImportError:
                logger.warning("Tushare 未安装，跳过注册")
            except Exception as e:
                logger.error("注册 TushareAdapter 失败: %s", e)
        else:
            logger.info("Tushare Token 未配置，跳过注册")

        # Wind（需要 wind_enabled=True）
        if self.config.data.wind_enabled:
            try:
                from fund_cli.data.adapters.wind_adapter import WindAdapter

                wind_adapter = WindAdapter(cache=self._cache)
                if wind_adapter.is_available():
                    self._adapters["wind"] = wind_adapter
                    self._gateway.register_adapter("wind", wind_adapter)
                    logger.info("已注册 WindAdapter")
                else:
                    logger.warning("Wind 不可用，跳过注册")
            except ImportError:
                logger.warning("WindPy 未安装，跳过注册")
            except Exception as e:
                logger.error("注册 WindAdapter 失败: %s", e)

        # 设置主数据源
        if self._primary_source not in self._adapters:
            # 如果配置的主数据源不可用，选择第一个可用的
            if self._adapters:
                old_primary = self._primary_source
                self._primary_source = list(self._adapters.keys())[0]
                logger.warning("主数据源 %s 不可用，切换到 %s", old_primary, self._primary_source)

        logger.info(
            "当前可用数据源: %s, 主数据源: %s", list(self._adapters.keys()), self._primary_source
        )

    def register_adapter(self, name: str, adapter: DataSourceAdapter) -> None:
        """
        注册新的数据源适配器

        Args:
            name: 适配器名称
            adapter: 适配器实例
        """
        self._adapters[name] = adapter
        self._gateway.register_adapter(name, adapter)
        logger.info("已注册适配器: %s", name)

    @property
    def available_sources(self) -> list[str]:
        """获取可用数据源列表"""
        return list(self._adapters.keys())

    @property
    def source_priority(self) -> list[str]:
        """获取数据源优先级列表"""
        return self.config.data.source_priority_list

    @property
    def gateway(self) -> DataSourceGateway:
        """获取数据源网关实例"""
        return self._gateway

    def get_adapter(self, source: str | None = None) -> DataSourceAdapter:
        """
        获取数据源适配器

        Args:
            source: 数据源名称，默认使用主数据源

        Returns:
            数据源适配器实例

        Raises:
            DataSourceError: 数据源不可用
        """
        source_name = source or self._primary_source

        if source_name not in self._adapters:
            raise DataSourceError(f"数据源 {source_name} 未配置或不可用")

        adapter = self._adapters[source_name]

        if not adapter.is_available():
            raise DataSourceError(f"数据源 {source_name} 不可用")

        return adapter

    @property
    def _adapter(self) -> DataSourceAdapter:
        """获取主数据源适配器（便捷属性）"""
        return self.get_adapter()

    def _call_gateway(
        self, method_name: str, *args: Any, normalize: bool = False, **kwargs: Any
    ) -> Any:
        """通过网关调用数据源方法，可选标准化."""
        result = self._gateway.call(method_name, *args, **kwargs)
        if normalize:
            try:
                if isinstance(result, pd.DataFrame) and not result.empty:
                    result = DataNormalizer.normalize_nav_data(result)
                elif isinstance(result, dict):
                    result = DataNormalizer.normalize_fund_info(result)
            except (ValueError, KeyError, TypeError):
                logger.debug("标准化跳过: %s 返回数据格式不兼容", method_name)
        return result

    # ========== 基础基金数据接口 ==========

    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金基础信息

        Args:
            fund_code: 基金代码

        Returns:
            基金信息字典
        """
        return self._call_gateway("get_fund_info", fund_code, normalize=True)

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
        return self._call_gateway("get_fund_nav", fund_code, start_date, end_date, normalize=True)

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
        搜索基金

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
        return self._adapter.search_funds(
            fund_type=fund_type,
            company=company,
            min_scale=min_scale,
            max_scale=max_scale,
            keyword=keyword,
            limit=limit,
        )

    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """
        获取基金列表

        Args:
            fund_type: 基金类型筛选

        Returns:
            基金列表 DataFrame
        """
        return self._adapter.get_fund_list(fund_type)

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
        return self._call_gateway(
            "get_benchmark_nav", benchmark_code, start_date, end_date, normalize=True
        )

    def get_fund_holdings(
        self,
        fund_code: str,
        report_date: date | None = None,
        top_n: int | None = None,
    ) -> pd.DataFrame:
        """
        获取基金持仓数据
        
        Args:
            fund_code: 基金代码
            report_date: 报告期
            top_n: 返回前N大持仓（可选）
        
        Returns:
            持仓数据 DataFrame
        """
        result = self._call_gateway("get_fund_holdings", fund_code, report_date, normalize=True)
        if top_n is not None and isinstance(result, pd.DataFrame) and not result.empty:
            return result.head(top_n)
        return result

    def get_fund_manager(self, fund_code: str) -> dict[str, Any]:
        """获取基金经理信息"""
        return self._call_gateway("get_fund_manager", fund_code, normalize=True)

    def get_fund_industry_allocation(
        self,
        fund_code: str,
        year: int | None = None,
    ) -> pd.DataFrame:
        """
        获取基金行业配置
        
        Args:
            fund_code: 基金代码
            year: 年份（默认最新）
        
        Returns:
            行业配置 DataFrame
        """
        return self._call_gateway("get_fund_industry_allocation", fund_code, year, normalize=True)

    def get_fund_fee(self, fund_code: str) -> dict[str, Any]:
        """获取基金费率信息"""
        return self._adapter.get_fund_fee(fund_code)

    def get_fund_rating(self, fund_code: str) -> int | None:
        """获取基金评级"""
        return self._adapter.get_fund_rating(fund_code)

    def batch_get_fund_nav(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """批量获取基金净值"""
        return self._adapter.batch_get_fund_nav(fund_codes, start_date, end_date)

    # ========== P0 级别接口 (18个) ==========

    def get_all_fund_names(self) -> pd.DataFrame:
        """获取所有基金名称列表"""
        return self._adapter.get_all_fund_names()

    def get_fund_info_ths(self, code: str) -> dict[str, Any]:
        """获取同花顺基金基本信息"""
        return self._adapter.get_fund_info_ths(code)

    def get_index_fund_info(
        self,
        category: str = "全部",
        indicator: str = "全部",
    ) -> pd.DataFrame:
        """获取指数型基金基本信息"""
        return self._adapter.get_index_fund_info(category, indicator)

    def get_fund_overview(self, code: str) -> dict[str, Any]:
        """获取基金档案基本概况"""
        return self._adapter.get_fund_overview(code)

    def get_fund_purchase_status(self) -> pd.DataFrame:
        """获取基金申购/赎回状态"""
        return self._adapter.get_fund_purchase_status()

    def get_fund_daily_nav(self) -> pd.DataFrame:
        """获取开放式基金每日净值(全部)"""
        return self._adapter.get_fund_daily_nav()

    def get_etf_spot(self) -> pd.DataFrame:
        """获取ETF实时行情"""
        return self._adapter.get_etf_spot()

    def get_fund_category_spot(
        self,
        category: str = "",
        date: str | None = None,
    ) -> pd.DataFrame:
        """获取同花顺基金实时行情(按类型)"""
        return self._adapter.get_fund_category_spot(category, date)

    def get_etf_spot_ths(self, date: str | None = None) -> pd.DataFrame:
        """获取同花顺ETF实时行情"""
        return self._adapter.get_etf_spot_ths(date)

    def get_lof_spot(self) -> pd.DataFrame:
        """获取LOF实时行情"""
        return self._adapter.get_lof_spot()

    def get_etf_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """获取ETF历史行情"""
        return self._adapter.get_etf_hist(code, period, start, end)

    def get_lof_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """获取LOF历史行情"""
        return self._adapter.get_lof_hist(code, period, start, end)

    def get_etf_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """获取ETF分时行情"""
        return self._adapter.get_etf_minute(code, period, start, end)

    def get_lof_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """获取LOF分时行情"""
        return self._adapter.get_lof_minute(code, period, start, end)

    def get_fund_bond_holdings(
        self,
        code: str,
        year: int | None = None,
    ) -> pd.DataFrame:
        """获取基金债券持仓"""
        return self._adapter.get_fund_bond_holdings(code, year)

    def get_fund_industry_allocation(
        self,
        code: str,
        year: int | None = None,
    ) -> pd.DataFrame:
        """获取基金行业配置"""
        return self._adapter.get_fund_industry_allocation(code, year)

    def get_fund_portfolio_change(
        self,
        code: str,
        indicator: str = "累计买入",
        year: int | None = None,
    ) -> pd.DataFrame:
        """获取基金重大变动(累计买入/卖出)"""
        return self._adapter.get_fund_portfolio_change(code, indicator, year)

    def get_all_fund_managers(self) -> pd.DataFrame:
        """获取基金经理大全"""
        return self._adapter.get_all_fund_managers()

    # ========== P1 级别接口 (25个) ==========

    # ---------- 基金公司/规模 (5个) ----------

    def get_fund_company_aum(self) -> pd.DataFrame:
        """基金公司管理规模排名"""
        return self._adapter.get_fund_company_aum()

    def get_fund_aum_trend(self) -> pd.DataFrame:
        """基金市场管理规模走势"""
        return self._adapter.get_fund_aum_trend()

    def get_fund_company_aum_history(self, year: int | None = None) -> pd.DataFrame:
        """基金公司历年管理规模"""
        return self._adapter.get_fund_company_aum_history(year)

    def get_fund_scale_change(self) -> pd.DataFrame:
        """规模变动(全市场汇总)"""
        return self._adapter.get_fund_scale_change()

    def get_fund_holder_structure(self) -> pd.DataFrame:
        """持有人结构"""
        return self._adapter.get_fund_holder_structure()

    # ---------- 基金评级 (4个) ----------

    def get_fund_ratings(self) -> pd.DataFrame:
        """基金评级总汇"""
        return self._adapter.get_fund_ratings()

    def get_fund_rating_sh(self, date: str | None = None) -> pd.DataFrame:
        """上海证券评级"""
        return self._adapter.get_fund_rating_sh(date)

    def get_fund_rating_zs(self, date: str | None = None) -> pd.DataFrame:
        """招商证券评级"""
        return self._adapter.get_fund_rating_zs(date)

    def get_fund_rating_ja(self, date: str | None = None) -> pd.DataFrame:
        """济安金信评级"""
        return self._adapter.get_fund_rating_ja(date)

    # ---------- 基金分红/拆分 (3个) ----------

    def get_fund_dividends(
        self,
        year: int | None = None,
        fund_type: str = "",  # type: ignore[assignment]
        page: int = -1,
    ) -> pd.DataFrame:
        """基金分红"""
        return self._adapter.get_fund_dividends(year, fund_type, page)

    def get_fund_splits(
        self,
        year: int | None = None,
        fund_type: str = "",  # type: ignore[assignment]
        page: int = -1,
    ) -> pd.DataFrame:
        """基金拆分"""
        return self._adapter.get_fund_splits(year, fund_type, page)

    def get_fund_dividend_rank(self) -> pd.DataFrame:
        """累计分红排行"""
        return self._adapter.get_fund_dividend_rank()

    # ---------- 基金排行 (5个) ----------

    def get_fund_rank_by_type(self, fund_type: str = "全部") -> pd.DataFrame:
        """开放式基金排行"""
        return self._adapter.get_fund_rank_by_type(fund_type)

    def get_exchange_fund_rank(self) -> pd.DataFrame:
        """场内交易基金排行"""
        return self._adapter.get_exchange_fund_rank()

    def get_money_fund_rank(self) -> pd.DataFrame:
        """货币型基金排行"""
        return self._adapter.get_money_fund_rank()

    def get_lcx_fund_rank(self) -> pd.DataFrame:
        """理财基金排行"""
        return self._adapter.get_lcx_fund_rank()

    def get_hk_fund_rank(self) -> pd.DataFrame:
        """香港基金排行"""
        return self._adapter.get_hk_fund_rank()

    # ---------- 基金业绩/分析 (3个) ----------

    def get_fund_achievement(self, code: str) -> pd.DataFrame:
        """基金业绩(年度+阶段)"""
        return self._adapter.get_fund_achievement(code)

    def get_fund_risk_analysis(self, code: str) -> pd.DataFrame:
        """基金数据分析(夏普/回撤)"""
        return self._adapter.get_fund_risk_analysis(code)

    def get_fund_profit_probability(self, code: str) -> pd.DataFrame:
        """盈利概率"""
        return self._adapter.get_fund_profit_probability(code)

    # ---------- 资产配置 (1个) ----------

    def get_fund_asset_allocation(self, code: str, date: str | None = None) -> pd.DataFrame:
        """基金资产配置"""
        return self._adapter.get_fund_asset_allocation(code, date)

    # ---------- 市场指数扩展 (6个) ----------

    def get_index_spot_em(self, category: str = "沪深重要指数") -> pd.DataFrame:
        """东财指数实时行情"""
        return self._adapter.get_index_spot_em(category)

    def get_index_spot_sina(self) -> pd.DataFrame:
        """新浪指数实时行情"""
        return self._adapter.get_index_spot_sina()

    def get_index_daily_tx(
        self, code: str, start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """腾讯指数历史"""
        return self._adapter.get_index_daily_tx(code, start, end)

    def get_index_daily_em(
        self, code: str, start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """东财指数历史"""
        return self._adapter.get_index_daily_em(code, start, end)

    def get_index_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """指数通用历史"""
        return self._adapter.get_index_hist(code, period, start, end)

    def get_index_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """指数分时"""
        return self._adapter.get_index_minute(code, period, start, end)

    # ========== P2 级别接口 (57个) ==========

    # ---------- 宏观经济数据 (22个) ----------

    def get_macro_leverage_ratio(self) -> pd.DataFrame:
        """获取中国宏观杠杆率数据"""
        return self._adapter.get_macro_leverage_ratio()

    def get_enterprise_price_index(self) -> pd.DataFrame:
        """获取企业商品价格指数"""
        return self._adapter.get_enterprise_price_index()

    def get_fdi_data(self) -> pd.DataFrame:
        """获取外商直接投资数据"""
        return self._adapter.get_fdi_data()

    def get_lpr_data(self) -> pd.DataFrame:
        """获取LPR品种数据"""
        return self._adapter.get_lpr_data()

    def get_urban_unemployment(self) -> pd.DataFrame:
        """获取城镇调查失业率"""
        return self._adapter.get_urban_unemployment()

    def get_social_financing(self) -> pd.DataFrame:
        """获取社会融资规模增量统计"""
        return self._adapter.get_social_financing()

    def get_gdp_yearly(self) -> pd.DataFrame:
        """获取中国GDP年率数据"""
        return self._adapter.get_gdp_yearly()

    def get_gdp_quarterly(self) -> pd.DataFrame:
        """获取中国GDP季度数据"""
        return self._adapter.get_gdp_quarterly()

    def get_cpi_yearly(self) -> pd.DataFrame:
        """获取中国CPI年率数据"""
        return self._adapter.get_cpi_yearly()

    def get_cpi_monthly(self) -> pd.DataFrame:
        """获取中国CPI月率数据"""
        return self._adapter.get_cpi_monthly()

    def get_ppi_yearly(self) -> pd.DataFrame:
        """获取中国PPI年率数据"""
        return self._adapter.get_ppi_yearly()

    def get_ppi_monthly(self) -> pd.DataFrame:
        """获取中国PPI月率数据"""
        return self._adapter.get_ppi_monthly()

    def get_exports_yearly(self) -> pd.DataFrame:
        """获取出口年率数据"""
        return self._adapter.get_exports_yearly()

    def get_imports_yearly(self) -> pd.DataFrame:
        """获取进口年率数据"""
        return self._adapter.get_imports_yearly()

    def get_trade_balance(self) -> pd.DataFrame:
        """获取贸易帐数据"""
        return self._adapter.get_trade_balance()

    def get_industrial_production(self) -> pd.DataFrame:
        """获取工业增加值增长数据"""
        return self._adapter.get_industrial_production()

    def get_pmi_official(self) -> pd.DataFrame:
        """获取官方制造业PMI数据"""
        return self._adapter.get_pmi_official()

    def get_pmi_caixin(self) -> pd.DataFrame:
        """获取财新制造业PMI数据"""
        return self._adapter.get_pmi_caixin()

    def get_services_pmi(self) -> pd.DataFrame:
        """获取财新服务业PMI数据"""
        return self._adapter.get_services_pmi()

    def get_non_manufacturing_pmi(self) -> pd.DataFrame:
        """获取官方非制造业PMI数据"""
        return self._adapter.get_non_manufacturing_pmi()

    def get_m2_yearly(self) -> pd.DataFrame:
        """获取M2货币供应年率数据"""
        return self._adapter.get_m2_yearly()

    def get_new_loan(self) -> pd.DataFrame:
        """获取新增人民币贷款数据"""
        return self._adapter.get_new_loan()

    def get_retail_sales_yearly(self) -> pd.DataFrame:
        """获取社会消费品零售总额年率数据"""
        return self._adapter.get_retail_sales_yearly()

    def get_fixed_asset_investment(self) -> pd.DataFrame:
        """获取固定资产投资年率数据"""
        return self._adapter.get_fixed_asset_investment()

    # ---------- 利率数据 (8个) ----------

    def get_china_interest_rate(self) -> pd.DataFrame:
        """获取中国央行利率决议数据"""
        return self._adapter.get_china_interest_rate()

    def get_usa_interest_rate(self) -> pd.DataFrame:
        """获取美联储利率决议数据"""
        return self._adapter.get_usa_interest_rate()

    def get_euro_interest_rate(self) -> pd.DataFrame:
        """获取欧洲央行利率决议数据"""
        return self._adapter.get_euro_interest_rate()

    def get_japan_interest_rate(self) -> pd.DataFrame:
        """获取日本央行利率决议数据"""
        return self._adapter.get_japan_interest_rate()

    def get_uk_interest_rate(self) -> pd.DataFrame:
        """获取英国央行利率决议数据"""
        return self._adapter.get_uk_interest_rate()

    def get_shibor(self) -> pd.DataFrame:
        """获取SHIBOR利率数据"""
        return self._adapter.get_shibor()

    def get_shibor_lpr(self) -> pd.DataFrame:
        """获取SHIBOR-LPR数据"""
        return self._adapter.get_shibor_lpr()

    def get_hibor(self) -> pd.DataFrame:
        """获取HIBOR利率数据"""
        return self._adapter.get_hibor()

    # ---------- 行业板块 (5个) ----------

    def get_industry_boards(self) -> pd.DataFrame:
        """获取行业板块名称列表"""
        return self._adapter.get_industry_boards()

    def get_industry_board_hist(
        self,
        code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """获取行业板块历史行情"""
        return self._adapter.get_industry_board_hist(code, period, start_date, end_date)

    def get_concept_boards(self) -> pd.DataFrame:
        """获取概念板块名称列表"""
        return self._adapter.get_concept_boards()

    def get_concept_board_hist(
        self,
        code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """获取概念板块历史行情"""
        return self._adapter.get_concept_board_hist(code, period, start_date, end_date)

    def get_sector_fund_flow(self, period: str = "今日") -> pd.DataFrame:
        """获取板块资金流向"""
        return self._adapter.get_sector_fund_flow(period)

    # ---------- 债券数据 (7个) ----------

    def get_china_us_bond_yield(self) -> pd.DataFrame:
        """获取中美国债收益率数据"""
        return self._adapter.get_china_us_bond_yield()

    def get_bond_yield_curve(
        self,
        bond_type: str = "国债",
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """获取收盘收益率曲线历史数据"""
        return self._adapter.get_bond_yield_curve(bond_type, period, start_date, end_date)

    def get_bond_spot_quote(self) -> pd.DataFrame:
        """获取现券市场做市报价"""
        return self._adapter.get_bond_spot_quote()

    def get_convertible_bonds(self) -> pd.DataFrame:
        """获取可转债数据一览表"""
        return self._adapter.get_convertible_bonds()

    def get_convertible_bond_detail(self, code: str) -> pd.DataFrame:
        """获取可转债详情数据"""
        return self._adapter.get_convertible_bond_detail(code)

    def get_bond_spot(self, code: str) -> pd.DataFrame:
        """获取沪深债券实时行情"""
        return self._adapter.get_bond_spot(code)

    def get_bond_hist(
        self,
        code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """获取沪深债券历史行情"""
        return self._adapter.get_bond_hist(code, period, start_date, end_date)

    # ---------- 估值指标 (5个) ----------

    def get_a_share_valuation(self) -> pd.DataFrame:
        """获取A股等权重与中位数市盈率/市净率"""
        return self._adapter.get_a_share_valuation()

    def get_stock_valuation_lg(self, code: str) -> pd.DataFrame:
        """获取个股估值数据(乐咕乐股)"""
        return self._adapter.get_stock_valuation_lg(code)

    def get_index_valuation(self, code: str, indicator: str = "pe") -> pd.DataFrame:
        """获取指数估值历史数据(乐咕乐股)"""
        return self._adapter.get_index_valuation(code, indicator)

    def get_market_pe_lg(self, code: str) -> pd.DataFrame:
        """获取指数市盈率数据(乐咕乐股)"""
        return self._adapter.get_market_pe_lg(code)

    def get_market_pb_lg(self, code: str) -> pd.DataFrame:
        """获取指数市净率数据(乐咕乐股)"""
        return self._adapter.get_market_pb_lg(code)

    # ---------- 资金流向 (3个) ----------

    def get_market_fund_flow(self) -> pd.DataFrame:
        """获取大盘资金流向数据"""
        return self._adapter.get_market_fund_flow()

    def get_stock_fund_flow(self, code: str, market: str = "sh") -> pd.DataFrame:
        """获取个股资金流向数据"""
        return self._adapter.get_stock_fund_flow(code, market)

    def get_north_fund_flow(self, market: str = "北向资金") -> pd.DataFrame:
        """获取北向资金流向数据"""
        return self._adapter.get_north_fund_flow(market)

    # ========== 缓存管理 ==========

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        return self._cache.get_stats()

    def __repr__(self) -> str:
        sources = list(self._adapters.keys())
        return f"DataManager(sources={sources}, primary={self._primary_source})"


# 全局数据管理器实例
_data_manager: DataManager | None = None


def get_data_manager() -> DataManager:
    """获取数据管理器实例（单例）"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager

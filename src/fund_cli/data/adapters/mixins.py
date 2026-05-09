"""
数据源适配器混合类.

提供所有抽象方法的默认占位实现，便于快速创建新的适配器。
"""

from datetime import date
from typing import Any

import pandas as pd

from fund_cli.data.base import DataSourceError


class DataSourceAdapterMixin:
    """
    数据源适配器混合类.

    提供所有抽象方法的占位实现，子类可以选择性地覆盖需要的方法。
    注意：这些是占位实现，返回空数据或抛出NotImplementedError。
    """

    # ----- P0 - 核心基金功能接口占位实现 -----

    def get_fund_info_ths(self, fund_code: str) -> dict[str, Any]:
        """同花顺-基金基本信息."""
        raise DataSourceError(f"{self.name} 不支持 同花顺基金信息 接口")

    def get_index_fund_info(
        self, category: str = "全部", indicator: str = "全部"
    ) -> pd.DataFrame:
        """东方财富-指数型基金基本信息."""
        raise DataSourceError(f"{self.name} 不支持 指数基金信息 接口")

    def get_fund_overview(self, fund_code: str) -> dict[str, Any]:
        """天天基金-基金档案基本概况."""
        raise DataSourceError(f"{self.name} 不支持 基金概况 接口")

    def get_fund_purchase_status(self) -> pd.DataFrame:
        """东方财富-基金申购/赎回状态."""
        raise DataSourceError(f"{self.name} 不支持 申购状态 接口")

    def get_fund_daily_nav(self) -> pd.DataFrame:
        """东方财富-开放式基金每日净值(全部)."""
        raise DataSourceError(f"{self.name} 不支持 每日净值 接口")

    def get_fund_category_spot(
        self, category: str = "", date: str | None = None
    ) -> pd.DataFrame:
        """同花顺-基金实时行情(按类型)."""
        raise DataSourceError(f"{self.name} 不支持 分类行情 接口")

    def get_etf_spot_ths(self, date: str | None = None) -> pd.DataFrame:
        """同花顺-ETF实时行情."""
        raise DataSourceError(f"{self.name} 不支持 同花顺ETF 接口")

    def get_etf_hist(
        self,
        fund_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """东方财富-ETF历史行情."""
        raise DataSourceError(f"{self.name} 不支持 ETF历史 接口")

    def get_lof_hist(
        self,
        fund_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """东方财富-LOF历史行情."""
        raise DataSourceError(f"{self.name} 不支持 LOF历史 接口")

    def search_funds(
        self,
        fund_type: str | None = None,
        company: str | None = None,
        min_scale: float | None = None,
        max_scale: float | None = None,
        keyword: str | None = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """搜索/筛选基金."""
        raise DataSourceError(f"{self.name} 不支持 基金搜索 接口")

    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """获取基金列表."""
        raise DataSourceError(f"{self.name} 不支持 基金列表 接口")

    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """获取基准指数净值数据."""
        raise DataSourceError(f"{self.name} 不支持 基准净值 接口")

    def get_fund_holdings(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """获取基金持仓数据."""
        raise DataSourceError(f"{self.name} 不支持 基金持仓 接口")

    def get_fund_bond_holdings(
        self, fund_code: str, year: int | None = None
    ) -> pd.DataFrame:
        """天天基金-基金债券持仓."""
        raise DataSourceError(f"{self.name} 不支持 基金债券持仓 接口")

    def get_fund_industry_allocation(
        self, fund_code: str, year: int | None = None
    ) -> pd.DataFrame:
        """天天基金-行业配置."""
        raise DataSourceError(f"{self.name} 不支持 行业配置 接口")

    def get_fund_portfolio_change(
        self, fund_code: str, indicator: str = "累计买入", year: int | None = None
    ) -> pd.DataFrame:
        """天天基金-重大变动(累计买入/卖出)."""
        raise DataSourceError(f"{self.name} 不支持 持仓变动 接口")

    def get_all_fund_managers(self) -> pd.DataFrame:
        """天天基金-基金经理大全."""
        raise DataSourceError(f"{self.name} 不支持 基金经理大全 接口")

    def get_etf_minute(
        self,
        fund_code: str,
        period: str = "1",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """东方财富-ETF分时行情."""
        raise DataSourceError(f"{self.name} 不支持 ETF分时 接口")

    def get_lof_minute(
        self,
        fund_code: str,
        period: str = "1",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """东方财富-LOF分时行情."""
        raise DataSourceError(f"{self.name} 不支持 LOF分时 接口")

    # ----- P1 - 分析增强功能接口占位实现 -----

    def get_fund_company_aum(self) -> pd.DataFrame:
        """东方财富-基金公司管理规模排名."""
        raise DataSourceError(f"{self.name} 不支持 基金公司规模 接口")

    def get_fund_aum_trend(self) -> pd.DataFrame:
        """东方财富-基金市场管理规模走势."""
        raise DataSourceError(f"{self.name} 不支持 规模走势 接口")

    def get_fund_company_aum_history(self, year: int | None = None) -> pd.DataFrame:
        """东方财富-基金公司历年管理规模排行."""
        raise DataSourceError(f"{self.name} 不支持 规模历史 接口")

    def get_fund_scale_change(self) -> pd.DataFrame:
        """天天基金-规模变动(全市场汇总)."""
        raise DataSourceError(f"{self.name} 不支持 规模变动 接口")

    def get_fund_holder_structure(self) -> pd.DataFrame:
        """天天基金-持有人结构(全市场汇总)."""
        raise DataSourceError(f"{self.name} 不支持 持有人结构 接口")

    def get_fund_ratings(self) -> pd.DataFrame:
        """天天基金-基金评级总汇."""
        raise DataSourceError(f"{self.name} 不支持 基金评级总汇 接口")

    def get_fund_rating_sh(self, date: str | None = None) -> pd.DataFrame:
        """天天基金-上海证券评级."""
        raise DataSourceError(f"{self.name} 不支持 上海证券评级 接口")

    def get_fund_rating_zs(self, date: str | None = None) -> pd.DataFrame:
        """天天基金-招商证券评级."""
        raise DataSourceError(f"{self.name} 不支持 招商证券评级 接口")

    def get_fund_rating_ja(self, date: str | None = None) -> pd.DataFrame:
        """天天基金-济安金信评级."""
        raise DataSourceError(f"{self.name} 不支持 济安金信评级 接口")

    def get_fund_dividends(
        self,
        year: int | None = None,
        fund_type: str = "",
        page: int = -1,
    ) -> pd.DataFrame:
        """天天基金-基金分红."""
        raise DataSourceError(f"{self.name} 不支持 基金分红 接口")

    def get_fund_splits(
        self,
        year: int | None = None,
        fund_type: str = "",
        page: int = -1,
    ) -> pd.DataFrame:
        """天天基金-基金拆分."""
        raise DataSourceError(f"{self.name} 不支持 基金拆分 接口")

    def get_fund_dividend_rank(self) -> pd.DataFrame:
        """天天基金-基金累计分红排行."""
        raise DataSourceError(f"{self.name} 不支持 分红排行 接口")

    def get_fund_rank_by_type(self, fund_type: str = "全部") -> pd.DataFrame:
        """东方财富-开放式基金排行."""
        raise DataSourceError(f"{self.name} 不支持 基金排行 接口")

    def get_exchange_fund_rank(self) -> pd.DataFrame:
        """东方财富-场内交易基金排行."""
        raise DataSourceError(f"{self.name} 不支持 场内基金排行 接口")

    def get_money_fund_rank(self) -> pd.DataFrame:
        """东方财富-货币型基金排行."""
        raise DataSourceError(f"{self.name} 不支持 货币基金排行 接口")

    def get_lcx_fund_rank(self) -> pd.DataFrame:
        """东方财富-理财基金排行."""
        raise DataSourceError(f"{self.name} 不支持 理财基金排行 接口")

    def get_hk_fund_rank(self) -> pd.DataFrame:
        """东方财富-香港基金排行."""
        raise DataSourceError(f"{self.name} 不支持 香港基金排行 接口")

    def get_fund_achievement(self, fund_code: str) -> pd.DataFrame:
        """雪球-基金业绩(年度+阶段)."""
        raise DataSourceError(f"{self.name} 不支持 基金业绩 接口")

    def get_fund_risk_analysis(self, fund_code: str) -> pd.DataFrame:
        """雪球-基金数据分析(夏普/回撤等)."""
        raise DataSourceError(f"{self.name} 不支持 风险分析 接口")

    def get_fund_profit_probability(self, fund_code: str) -> pd.DataFrame:
        """雪球-基金盈利概率."""
        raise DataSourceError(f"{self.name} 不支持 盈利概率 接口")

    def get_fund_asset_allocation(
        self, fund_code: str, date: str | None = None
    ) -> pd.DataFrame:
        """雪球-基金资产配置."""
        raise DataSourceError(f"{self.name} 不支持 资产配置 接口")

    def get_index_spot_em(self, category: str = "沪深重要指数") -> pd.DataFrame:
        """东财-沪深京指数实时行情."""
        raise DataSourceError(f"{self.name} 不支持 东财指数实时 接口")

    def get_index_spot_sina(self) -> pd.DataFrame:
        """新浪-中国股票指数实时行情."""
        raise DataSourceError(f"{self.name} 不支持 新浪指数实时 接口")

    def get_index_daily_tx(
        self, code: str, start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """腾讯-指数历史行情."""
        raise DataSourceError(f"{self.name} 不支持 腾讯指数历史 接口")

    def get_index_daily_em(
        self, code: str, start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """东财-指数历史行情."""
        raise DataSourceError(f"{self.name} 不支持 东财指数历史 接口")

    def get_index_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """东财-指数通用历史行情."""
        raise DataSourceError(f"{self.name} 不支持 指数历史 接口")

    def get_index_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """东财-指数分时行情."""
        raise DataSourceError(f"{self.name} 不支持 指数分时 接口")

    # ----- P2 - 辅助分析功能接口占位实现 -----

    def get_macro_leverage_ratio(self) -> pd.DataFrame:
        """中国宏观杠杆率."""
        raise DataSourceError(f"{self.name} 不支持 宏观杠杆率 接口")

    def get_enterprise_price_index(self) -> pd.DataFrame:
        """企业商品价格指数."""
        raise DataSourceError(f"{self.name} 不支持 企业价格指数 接口")

    def get_fdi_data(self) -> pd.DataFrame:
        """外商直接投资数据."""
        raise DataSourceError(f"{self.name} 不支持 FDI数据 接口")

    def get_lpr_data(self) -> pd.DataFrame:
        """LPR品种数据."""
        raise DataSourceError(f"{self.name} 不支持 LPR数据 接口")

    def get_urban_unemployment(self) -> pd.DataFrame:
        """城镇调查失业率."""
        raise DataSourceError(f"{self.name} 不支持 城镇失业率 接口")

    def get_social_financing(self) -> pd.DataFrame:
        """社会融资规模增量."""
        raise DataSourceError(f"{self.name} 不支持 社会融资 接口")

    def get_gdp_yearly(self) -> pd.DataFrame:
        """中国GDP年率."""
        raise DataSourceError(f"{self.name} 不支持 GDP年率 接口")

    def get_gdp_quarterly(self) -> pd.DataFrame:
        """中国GDP季度数据."""
        raise DataSourceError(f"{self.name} 不支持 GDP季度 接口")

    def get_cpi_yearly(self) -> pd.DataFrame:
        """中国CPI年率."""
        raise DataSourceError(f"{self.name} 不支持 CPI年率 接口")

    def get_cpi_monthly(self) -> pd.DataFrame:
        """中国CPI月率."""
        raise DataSourceError(f"{self.name} 不支持 CPI月率 接口")

    def get_ppi_yearly(self) -> pd.DataFrame:
        """中国PPI年率."""
        raise DataSourceError(f"{self.name} 不支持 PPI年率 接口")

    def get_ppi_monthly(self) -> pd.DataFrame:
        """中国PPI月率."""
        raise DataSourceError(f"{self.name} 不支持 PPI月率 接口")

    def get_exports_yearly(self) -> pd.DataFrame:
        """出口年率."""
        raise DataSourceError(f"{self.name} 不支持 出口年率 接口")

    def get_imports_yearly(self) -> pd.DataFrame:
        """进口年率."""
        raise DataSourceError(f"{self.name} 不支持 进口年率 接口")

    def get_trade_balance(self) -> pd.DataFrame:
        """贸易帐."""
        raise DataSourceError(f"{self.name} 不支持 贸易帐 接口")

    def get_industrial_production(self) -> pd.DataFrame:
        """工业增加值增长."""
        raise DataSourceError(f"{self.name} 不支持 工业生产 接口")

    def get_pmi_official(self) -> pd.DataFrame:
        """官方制造业PMI."""
        raise DataSourceError(f"{self.name} 不支持 官方PMI 接口")

    def get_pmi_caixin(self) -> pd.DataFrame:
        """财新制造业PMI."""
        raise DataSourceError(f"{self.name} 不支持 财新PMI 接口")

    def get_services_pmi(self) -> pd.DataFrame:
        """财新服务业PMI."""
        raise DataSourceError(f"{self.name} 不支持 服务业PMI 接口")

    def get_non_manufacturing_pmi(self) -> pd.DataFrame:
        """官方非制造业PMI."""
        raise DataSourceError(f"{self.name} 不支持 非制造业PMI 接口")

    def get_m2_yearly(self) -> pd.DataFrame:
        """M2货币供应年率."""
        raise DataSourceError(f"{self.name} 不支持 M2数据 接口")

    def get_new_loan(self) -> pd.DataFrame:
        """新增人民币贷款."""
        raise DataSourceError(f"{self.name} 不支持 新增贷款 接口")

    def get_china_interest_rate(self) -> pd.DataFrame:
        """中国央行利率决议."""
        raise DataSourceError(f"{self.name} 不支持 中国利率 接口")

    def get_usa_interest_rate(self) -> pd.DataFrame:
        """美联储利率决议."""
        raise DataSourceError(f"{self.name} 不支持 美国利率 接口")

    def get_euro_interest_rate(self) -> pd.DataFrame:
        """欧洲央行利率决议."""
        raise DataSourceError(f"{self.name} 不支持 欧洲利率 接口")

    def get_japan_interest_rate(self) -> pd.DataFrame:
        """日本央行利率决议."""
        raise DataSourceError(f"{self.name} 不支持 日本利率 接口")

    def get_uk_interest_rate(self) -> pd.DataFrame:
        """英国央行利率决议."""
        raise DataSourceError(f"{self.name} 不支持 英国利率 接口")

    def get_shibor(self) -> pd.DataFrame:
        """SHIBOR利率."""
        raise DataSourceError(f"{self.name} 不支持 SHIBOR 接口")

    def get_shibor_lpr(self) -> pd.DataFrame:
        """SHIBOR-LPR."""
        raise DataSourceError(f"{self.name} 不支持 SHIBOR-LPR 接口")

    def get_hibor(self) -> pd.DataFrame:
        """人民币香港银行同业拆息."""
        raise DataSourceError(f"{self.name} 不支持 HIBOR 接口")

    def get_industry_boards(self) -> pd.DataFrame:
        """行业板块列表."""
        raise DataSourceError(f"{self.name} 不支持 行业板块列表 接口")

    def get_industry_board_hist(
        self, code: str, period: str = "daily", start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """行业板块历史行情."""
        raise DataSourceError(f"{self.name} 不支持 行业板块历史 接口")

    def get_concept_boards(self) -> pd.DataFrame:
        """概念板块列表."""
        raise DataSourceError(f"{self.name} 不支持 概念板块列表 接口")

    def get_concept_board_hist(
        self, code: str, period: str = "daily", start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """概念板块历史行情."""
        raise DataSourceError(f"{self.name} 不支持 概念板块历史 接口")

    def get_sector_fund_flow(self, period: str = "今日") -> pd.DataFrame:
        """板块资金流向."""
        raise DataSourceError(f"{self.name} 不支持 板块资金流向 接口")

    def get_china_us_bond_yield(self) -> pd.DataFrame:
        """中美国债收益率."""
        raise DataSourceError(f"{self.name} 不支持 中美国债收益率 接口")

    def get_bond_yield_curve(
        self,
        bond_type: str = "国债",
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """收盘收益率曲线."""
        raise DataSourceError(f"{self.name} 不支持 债券收益率曲线 接口")

    def get_bond_spot_quote(self) -> pd.DataFrame:
        """现券市场做市报价."""
        raise DataSourceError(f"{self.name} 不支持 债券报价 接口")

    def get_convertible_bonds(self) -> pd.DataFrame:
        """可转债数据一览."""
        raise DataSourceError(f"{self.name} 不支持 可转债列表 接口")

    def get_convertible_bond_detail(self, code: str) -> dict[str, Any]:
        """可转债详情."""
        raise DataSourceError(f"{self.name} 不支持 可转债详情 接口")

    def get_bond_spot(self, code: str) -> pd.DataFrame:
        """沪深债券实时行情."""
        raise DataSourceError(f"{self.name} 不支持 债券实时 接口")

    def get_bond_hist(
        self, code: str, period: str = "daily", start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """沪深债券历史行情."""
        raise DataSourceError(f"{self.name} 不支持 债券历史 接口")

    def get_a_share_valuation(self) -> pd.DataFrame:
        """A股等权重与中位数PE/PB."""
        raise DataSourceError(f"{self.name} 不支持 A股估值 接口")

    def get_stock_valuation_lg(self, code: str) -> pd.DataFrame:
        """个股估值-乐咕乐股."""
        raise DataSourceError(f"{self.name} 不支持 个股估值 接口")

    def get_index_valuation(
        self, code: str, indicator: str = "pe"
    ) -> pd.DataFrame:
        """指数估值-乐咕乐股."""
        raise DataSourceError(f"{self.name} 不支持 指数估值 接口")

    def get_market_pe_lg(self, code: str) -> pd.DataFrame:
        """指数市盈率-乐咕乐股."""
        raise DataSourceError(f"{self.name} 不支持 市场PE 接口")

    def get_market_pb_lg(self, code: str) -> pd.DataFrame:
        """指数市净率-乐咕乐股."""
        raise DataSourceError(f"{self.name} 不支持 市场PB 接口")

    def get_market_fund_flow(self) -> pd.DataFrame:
        """大盘资金流向."""
        raise DataSourceError(f"{self.name} 不支持 市场资金流向 接口")

    def get_stock_fund_flow(self, code: str, market: str = "sh") -> pd.DataFrame:
        """个股资金流向."""
        raise DataSourceError(f"{self.name} 不支持 个股资金流向 接口")

    def get_north_fund_flow(self, market: str = "北向资金") -> pd.DataFrame:
        """沪深港通资金流向."""
        raise DataSourceError(f"{self.name} 不支持 北向资金 接口")

    def get_retail_sales_yearly(self) -> pd.DataFrame:
        """社会消费品零售总额."""
        raise DataSourceError(f"{self.name} 不支持 零售销售 接口")

    def get_fixed_asset_investment(self) -> pd.DataFrame:
        """固定资产投资."""
        raise DataSourceError(f"{self.name} 不支持 固定资产投资 接口")

    def get_fund_manager(self, fund_code: str) -> dict[str, Any]:
        """获取基金经理信息."""
        raise DataSourceError(f"{self.name} 不支持 基金经理 接口")

    def get_fund_rating(self, fund_code: str) -> int | None:
        """获取基金评级."""
        raise DataSourceError(f"{self.name} 不支持 基金评级 接口")

    def batch_get_fund_nav(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """批量获取基金净值数据."""
        raise DataSourceError(f"{self.name} 不支持 批量净值 接口")

    def get_fund_fee(self, fund_code: str) -> dict[str, Any]:
        """获取基金费率信息."""
        raise DataSourceError(f"{self.name} 不支持 基金费率 接口")

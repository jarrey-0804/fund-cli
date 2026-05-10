"""
数据源适配器基类

定义数据源适配器的标准接口，支持多数据源扩展。
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import pandas as pd


class DataSourceAdapter(ABC):
    """
    数据源适配器基类

    所有数据源适配器必须继承此类并实现所有抽象方法。
    """

    def __init__(self, name: str):
        """
        初始化数据源适配器

        Args:
            name: 数据源名称
        """
        self._name = name

    @property
    def name(self) -> str:
        """数据源名称"""
        return self._name

    @abstractmethod
    def is_available(self) -> bool:
        """
        检查数据源是否可用

        Returns:
            数据源是否可用
        """
        pass

    # =========================================================================
    # P0 - 核心基金功能接口 (18个)
    # =========================================================================

    # ----- 基金基本信息 (5个，含1个已有) -----
    @abstractmethod
    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金基础信息

        Args:
            fund_code: 基金代码（6位数字）

        Returns:
            基金基础信息字典

        Raises:
            DataNotFoundError: 基金不存在
            DataSourceError: 数据源错误
        """
        pass

    @abstractmethod
    def get_all_fund_names(self) -> pd.DataFrame:
        """
        获取所有基金名称列表

        Returns:
            DataFrame包含：基金代码, 拼音缩写, 基金简称, 基金类型, 拼音全称
        """
        pass

    @abstractmethod
    def get_fund_info_ths(self, fund_code: str) -> dict[str, Any]:
        """
        同花顺-基金基本信息

        Args:
            fund_code: 基金代码

        Returns:
            基金详细信息字典
        """
        pass

    @abstractmethod
    def get_index_fund_info(self, category: str = "全部", indicator: str = "全部") -> pd.DataFrame:
        """
        东方财富-指数型基金基本信息

        Args:
            category: 分类，可选"全部","沪深指数","行业主题","大盘指数"等
            indicator: 指标，可选"全部","被动指数型","增强指数型"

        Returns:
            指数型基金信息DataFrame
        """
        pass

    @abstractmethod
    def get_fund_overview(self, fund_code: str) -> dict[str, Any]:
        """
        天天基金-基金档案基本概况

        Args:
            fund_code: 基金代码

        Returns:
            基金概况字典
        """
        pass

    # ----- 基金申购状态 (1个) -----
    @abstractmethod
    def get_fund_purchase_status(self) -> pd.DataFrame:
        """
        东方财富-基金申购/赎回状态

        Returns:
            DataFrame包含：基金代码, 基金简称, 申购状态, 赎回状态等
        """
        pass

    # ----- 基金净值数据 (2个，含1个已有) -----
    @abstractmethod
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
            净值数据DataFrame
        """
        pass

    @abstractmethod
    def get_fund_daily_nav(self) -> pd.DataFrame:
        """
        东方财富-开放式基金每日净值(全部)

        Returns:
            全部基金净值DataFrame
        """
        pass

    # ----- 基金行情数据 (8个) -----
    @abstractmethod
    def get_etf_spot(self) -> pd.DataFrame:
        """
        东方财富-ETF实时行情(全部)

        Returns:
            ETF实时行情DataFrame
        """
        pass

    @abstractmethod
    def get_fund_category_spot(self, category: str = "", date: str | None = None) -> pd.DataFrame:
        """
        同花顺-基金实时行情(按类型)

        Args:
            category: 基金类型，如"股票型","债券型","混合型","ETF","LOF"等
            date: 日期

        Returns:
            基金行情DataFrame
        """
        pass

    @abstractmethod
    def get_etf_spot_ths(self, date: str | None = None) -> pd.DataFrame:
        """
        同花顺-ETF实时行情

        Args:
            date: 日期

        Returns:
            ETF行情DataFrame
        """
        pass

    @abstractmethod
    def get_lof_spot(self) -> pd.DataFrame:
        """
        东方财富-LOF实时行情(全部)

        Returns:
            LOF实时行情DataFrame
        """
        pass

    @abstractmethod
    def get_etf_hist(
        self,
        fund_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        东方财富-ETF历史行情

        Args:
            fund_code: 基金代码
            period: 周期，"daily","weekly","monthly"
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            ETF历史行情DataFrame
        """
        pass

    @abstractmethod
    def get_lof_hist(
        self,
        fund_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        东方财富-LOF历史行情

        Args:
            fund_code: 基金代码
            period: 周期
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            LOF历史行情DataFrame
        """
        pass

    @abstractmethod
    def get_etf_minute(
        self,
        fund_code: str,
        period: str = "1",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        东方财富-ETF分时行情

        Args:
            fund_code: 基金代码
            period: 分钟周期，"1","5","15","30","60"
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            ETF分时行情DataFrame
        """
        pass

    @abstractmethod
    def get_lof_minute(
        self,
        fund_code: str,
        period: str = "1",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """
        东方财富-LOF分时行情

        Args:
            fund_code: 基金代码
            period: 分钟周期
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            LOF分时行情DataFrame
        """
        pass

    # ----- 基金持仓数据 (4个，含1个已有) -----
    @abstractmethod
    def get_fund_holdings(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金持仓数据

        Args:
            fund_code: 基金代码
            report_date: 报告日期

        Returns:
            持仓数据DataFrame
        """
        pass

    @abstractmethod
    def get_fund_bond_holdings(self, fund_code: str, year: int | None = None) -> pd.DataFrame:
        """
        天天基金-基金债券持仓

        Args:
            fund_code: 基金代码
            year: 年份

        Returns:
            债券持仓DataFrame
        """
        pass

    @abstractmethod
    def get_fund_industry_allocation(self, fund_code: str, year: int | None = None) -> pd.DataFrame:
        """
        天天基金-行业配置

        Args:
            fund_code: 基金代码
            year: 年份

        Returns:
            行业配置DataFrame
        """
        pass

    @abstractmethod
    def get_fund_portfolio_change(
        self, fund_code: str, indicator: str = "累计买入", year: int | None = None
    ) -> pd.DataFrame:
        """
        天天基金-重大变动(累计买入/卖出)

        Args:
            fund_code: 基金代码
            indicator: "累计买入"或"累计卖出"
            year: 年份

        Returns:
            持仓变动DataFrame
        """
        pass

    # ----- 基金经理 (1个) -----
    @abstractmethod
    def get_all_fund_managers(self) -> pd.DataFrame:
        """
        天天基金-基金经理大全

        Returns:
            基金经理信息DataFrame
        """
        pass

    # ----- 搜索/列表功能 (已有) -----
    @abstractmethod
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
            min_scale: 最小规模（亿元）
            max_scale: 最大规模（亿元）
            keyword: 关键词搜索
            limit: 返回数量限制

        Returns:
            基金列表DataFrame
        """
        pass

    @abstractmethod
    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """
        获取基金列表

        Args:
            fund_type: 基金类型筛选

        Returns:
            基金列表DataFrame
        """
        pass

    # ----- 基准指数 (已有) -----
    @abstractmethod
    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基准指数净值数据

        Args:
            benchmark_code: 基准指数代码
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            基准净值数据DataFrame
        """
        pass

    # ----- 费率 (已有) -----
    @abstractmethod
    def get_fund_fee(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金费率信息

        Args:
            fund_code: 基金代码

        Returns:
            费率信息字典
        """
        pass

    # =========================================================================
    # P1 - 分析增强功能接口 (25个)
    # =========================================================================

    # ----- 基金公司/规模 (5个) -----
    @abstractmethod
    def get_fund_company_aum(self) -> pd.DataFrame:
        """
        东方财富-基金公司管理规模排名

        Returns:
            基金公司规模排名DataFrame
        """
        pass

    @abstractmethod
    def get_fund_aum_trend(self) -> pd.DataFrame:
        """
        东方财富-基金市场管理规模走势

        Returns:
            规模走势DataFrame
        """
        pass

    @abstractmethod
    def get_fund_company_aum_history(self, year: int | None = None) -> pd.DataFrame:
        """
        东方财富-基金公司历年管理规模排行

        Args:
            year: 年份

        Returns:
            历年规模排行DataFrame
        """
        pass

    @abstractmethod
    def get_fund_scale_change(self) -> pd.DataFrame:
        """
        天天基金-规模变动(全市场汇总)

        Returns:
            规模变动DataFrame
        """
        pass

    @abstractmethod
    def get_fund_holder_structure(self) -> pd.DataFrame:
        """
        天天基金-持有人结构(全市场汇总)

        Returns:
            持有人结构DataFrame
        """
        pass

    # ----- 基金评级 (4个) -----
    @abstractmethod
    def get_fund_ratings(self) -> pd.DataFrame:
        """
        天天基金-基金评级总汇

        Returns:
            基金评级DataFrame
        """
        pass

    @abstractmethod
    def get_fund_rating_sh(self, date: str | None = None) -> pd.DataFrame:
        """
        天天基金-上海证券评级

        Args:
            date: 日期(YYYYMMDD)

        Returns:
            上海证券评级DataFrame
        """
        pass

    @abstractmethod
    def get_fund_rating_zs(self, date: str | None = None) -> pd.DataFrame:
        """
        天天基金-招商证券评级

        Args:
            date: 日期(YYYYMMDD)

        Returns:
            招商证券评级DataFrame
        """
        pass

    @abstractmethod
    def get_fund_rating_ja(self, date: str | None = None) -> pd.DataFrame:
        """
        天天基金-济安金信评级

        Args:
            date: 日期(YYYYMMDD)

        Returns:
            济安金信评级DataFrame
        """
        pass

    # ----- 基金分红/拆分 (3个) -----
    @abstractmethod
    def get_fund_dividends(
        self,
        year: int | None = None,
        fund_type: str = "",
        page: int = -1,
    ) -> pd.DataFrame:
        """
        天天基金-基金分红

        Args:
            year: 年份
            fund_type: 基金类型
            page: 页码，-1为全部

        Returns:
            分红数据DataFrame
        """
        pass

    @abstractmethod
    def get_fund_splits(
        self,
        year: int | None = None,
        fund_type: str = "",
        page: int = -1,
    ) -> pd.DataFrame:
        """
        天天基金-基金拆分

        Args:
            year: 年份
            fund_type: 基金类型
            page: 页码

        Returns:
            拆分数据DataFrame
        """
        pass

    @abstractmethod
    def get_fund_dividend_rank(self) -> pd.DataFrame:
        """
        天天基金-基金累计分红排行

        Returns:
            分红排行DataFrame
        """
        pass

    # ----- 基金排行 (5个) -----
    @abstractmethod
    def get_fund_rank_by_type(self, fund_type: str = "全部") -> pd.DataFrame:
        """
        东方财富-开放式基金排行

        Args:
            fund_type: 基金类型，"全部","股票型","混合型","债券型"等

        Returns:
            基金排行DataFrame
        """
        pass

    @abstractmethod
    def get_exchange_fund_rank(self) -> pd.DataFrame:
        """
        东方财富-场内交易基金排行

        Returns:
            场内基金排行DataFrame
        """
        pass

    @abstractmethod
    def get_money_fund_rank(self) -> pd.DataFrame:
        """
        东方财富-货币型基金排行

        Returns:
            货币基金排行DataFrame
        """
        pass

    @abstractmethod
    def get_lcx_fund_rank(self) -> pd.DataFrame:
        """
        东方财富-理财基金排行

        Returns:
            理财基金排行DataFrame
        """
        pass

    @abstractmethod
    def get_hk_fund_rank(self) -> pd.DataFrame:
        """
        东方财富-香港基金排行

        Returns:
            香港基金排行DataFrame
        """
        pass

    # ----- 基金业绩/分析 (3个) -----
    @abstractmethod
    def get_fund_achievement(self, fund_code: str) -> pd.DataFrame:
        """
        雪球-基金业绩(年度+阶段)

        Args:
            fund_code: 基金代码

        Returns:
            业绩数据DataFrame
        """
        pass

    @abstractmethod
    def get_fund_risk_analysis(self, fund_code: str) -> pd.DataFrame:
        """
        雪球-基金数据分析(夏普/回撤等)

        Args:
            fund_code: 基金代码

        Returns:
            风险分析DataFrame
        """
        pass

    @abstractmethod
    def get_fund_profit_probability(self, fund_code: str) -> pd.DataFrame:
        """
        雪球-基金盈利概率

        Args:
            fund_code: 基金代码

        Returns:
            盈利概率DataFrame
        """
        pass

    # ----- 基金资产配置 (1个) -----
    @abstractmethod
    def get_fund_asset_allocation(self, fund_code: str, date: str | None = None) -> pd.DataFrame:
        """
        雪球-基金资产配置

        Args:
            fund_code: 基金代码
            date: 财报日期(YYYYMMDD)

        Returns:
            资产配置DataFrame
        """
        pass

    # ----- 市场指数扩展 (6个) -----
    @abstractmethod
    def get_index_spot_em(self, category: str = "沪深重要指数") -> pd.DataFrame:
        """
        东财-沪深京指数实时行情

        Args:
            category: 指数分类

        Returns:
            指数行情DataFrame
        """
        pass

    @abstractmethod
    def get_index_spot_sina(self) -> pd.DataFrame:
        """
        新浪-中国股票指数实时行情

        Returns:
            指数行情DataFrame
        """
        pass

    @abstractmethod
    def get_index_daily_tx(
        self, code: str, start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """
        腾讯-指数历史行情

        Args:
            code: 指数代码
            start: 开始日期
            end: 结束日期

        Returns:
            指数历史DataFrame
        """
        pass

    @abstractmethod
    def get_index_daily_em(
        self, code: str, start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """
        东财-指数历史行情

        Args:
            code: 指数代码
            start: 开始日期
            end: 结束日期

        Returns:
            指数历史DataFrame
        """
        pass

    @abstractmethod
    def get_index_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        东财-指数通用历史行情

        Args:
            code: 指数代码
            period: 周期
            start: 开始日期
            end: 结束日期

        Returns:
            指数历史DataFrame
        """
        pass

    @abstractmethod
    def get_index_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        东财-指数分时行情

        Args:
            code: 指数代码
            period: 分钟周期
            start: 开始日期
            end: 结束日期

        Returns:
            指数分时DataFrame
        """
        pass

    # =========================================================================
    # P2 - 辅助分析功能接口 (57个)
    # =========================================================================

    # ----- 宏观经济数据 (22个) -----
    @abstractmethod
    def get_macro_leverage_ratio(self) -> pd.DataFrame:
        """中国宏观杠杆率"""
        pass

    @abstractmethod
    def get_enterprise_price_index(self) -> pd.DataFrame:
        """企业商品价格指数"""
        pass

    @abstractmethod
    def get_fdi_data(self) -> pd.DataFrame:
        """外商直接投资数据"""
        pass

    @abstractmethod
    def get_lpr_data(self) -> pd.DataFrame:
        """LPR品种数据"""
        pass

    @abstractmethod
    def get_urban_unemployment(self) -> pd.DataFrame:
        """城镇调查失业率"""
        pass

    @abstractmethod
    def get_social_financing(self) -> pd.DataFrame:
        """社会融资规模增量"""
        pass

    @abstractmethod
    def get_gdp_yearly(self) -> pd.DataFrame:
        """中国GDP年率"""
        pass

    @abstractmethod
    def get_gdp_quarterly(self) -> pd.DataFrame:
        """中国GDP季度数据"""
        pass

    @abstractmethod
    def get_cpi_yearly(self) -> pd.DataFrame:
        """中国CPI年率"""
        pass

    @abstractmethod
    def get_cpi_monthly(self) -> pd.DataFrame:
        """中国CPI月率"""
        pass

    @abstractmethod
    def get_ppi_yearly(self) -> pd.DataFrame:
        """中国PPI年率"""
        pass

    @abstractmethod
    def get_ppi_monthly(self) -> pd.DataFrame:
        """中国PPI月率"""
        pass

    @abstractmethod
    def get_exports_yearly(self) -> pd.DataFrame:
        """出口年率"""
        pass

    @abstractmethod
    def get_imports_yearly(self) -> pd.DataFrame:
        """进口年率"""
        pass

    @abstractmethod
    def get_trade_balance(self) -> pd.DataFrame:
        """贸易帐"""
        pass

    @abstractmethod
    def get_industrial_production(self) -> pd.DataFrame:
        """工业增加值增长"""
        pass

    @abstractmethod
    def get_pmi_official(self) -> pd.DataFrame:
        """官方制造业PMI"""
        pass

    @abstractmethod
    def get_pmi_caixin(self) -> pd.DataFrame:
        """财新制造业PMI"""
        pass

    @abstractmethod
    def get_services_pmi(self) -> pd.DataFrame:
        """财新服务业PMI"""
        pass

    @abstractmethod
    def get_non_manufacturing_pmi(self) -> pd.DataFrame:
        """官方非制造业PMI"""
        pass

    @abstractmethod
    def get_m2_yearly(self) -> pd.DataFrame:
        """M2货币供应年率"""
        pass

    @abstractmethod
    def get_new_loan(self) -> pd.DataFrame:
        """新增人民币贷款"""
        pass

    # ----- 利率数据 (8个) -----
    @abstractmethod
    def get_china_interest_rate(self) -> pd.DataFrame:
        """中国央行利率决议"""
        pass

    @abstractmethod
    def get_usa_interest_rate(self) -> pd.DataFrame:
        """美联储利率决议"""
        pass

    @abstractmethod
    def get_euro_interest_rate(self) -> pd.DataFrame:
        """欧洲央行利率决议"""
        pass

    @abstractmethod
    def get_japan_interest_rate(self) -> pd.DataFrame:
        """日本央行利率决议"""
        pass

    @abstractmethod
    def get_uk_interest_rate(self) -> pd.DataFrame:
        """英国央行利率决议"""
        pass

    @abstractmethod
    def get_shibor(self) -> pd.DataFrame:
        """SHIBOR利率"""
        pass

    @abstractmethod
    def get_shibor_lpr(self) -> pd.DataFrame:
        """SHIBOR-LPR"""
        pass

    @abstractmethod
    def get_hibor(self) -> pd.DataFrame:
        """人民币香港银行同业拆息"""
        pass

    # ----- 行业板块数据 (5个) -----
    @abstractmethod
    def get_industry_boards(self) -> pd.DataFrame:
        """行业板块列表"""
        pass

    @abstractmethod
    def get_industry_board_hist(
        self, code: str, period: str = "daily", start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """行业板块历史行情"""
        pass

    @abstractmethod
    def get_concept_boards(self) -> pd.DataFrame:
        """概念板块列表"""
        pass

    @abstractmethod
    def get_concept_board_hist(
        self, code: str, period: str = "daily", start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """概念板块历史行情"""
        pass

    @abstractmethod
    def get_sector_fund_flow(self, period: str = "今日") -> pd.DataFrame:
        """板块资金流向"""
        pass

    # ----- 债券数据 (7个) -----
    @abstractmethod
    def get_china_us_bond_yield(self) -> pd.DataFrame:
        """中美国债收益率"""
        pass

    @abstractmethod
    def get_bond_yield_curve(
        self,
        bond_type: str = "国债",
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """收盘收益率曲线"""
        pass

    @abstractmethod
    def get_bond_spot_quote(self) -> pd.DataFrame:
        """现券市场做市报价"""
        pass

    @abstractmethod
    def get_convertible_bonds(self) -> pd.DataFrame:
        """可转债数据一览"""
        pass

    @abstractmethod
    def get_convertible_bond_detail(self, code: str) -> dict[str, Any]:
        """可转债详情"""
        pass

    @abstractmethod
    def get_bond_spot(self, code: str) -> pd.DataFrame:
        """沪深债券实时行情"""
        pass

    @abstractmethod
    def get_bond_hist(
        self, code: str, period: str = "daily", start: str | None = None, end: str | None = None
    ) -> pd.DataFrame:
        """沪深债券历史行情"""
        pass

    # ----- 估值指标 (5个) -----
    @abstractmethod
    def get_a_share_valuation(self) -> pd.DataFrame:
        """A股等权重与中位数PE/PB"""
        pass

    @abstractmethod
    def get_stock_valuation_lg(self, code: str) -> pd.DataFrame:
        """个股估值-乐咕乐股"""
        pass

    @abstractmethod
    def get_index_valuation(self, code: str, indicator: str = "pe") -> pd.DataFrame:
        """指数估值-乐咕乐股"""
        pass

    @abstractmethod
    def get_market_pe_lg(self, code: str) -> pd.DataFrame:
        """指数市盈率-乐咕乐股"""
        pass

    @abstractmethod
    def get_market_pb_lg(self, code: str) -> pd.DataFrame:
        """指数市净率-乐咕乐股"""
        pass

    # ----- 资金流向 (3个) -----
    @abstractmethod
    def get_market_fund_flow(self) -> pd.DataFrame:
        """大盘资金流向"""
        pass

    @abstractmethod
    def get_stock_fund_flow(self, code: str, market: str = "sh") -> pd.DataFrame:
        """个股资金流向"""
        pass

    @abstractmethod
    def get_north_fund_flow(self, market: str = "北向资金") -> pd.DataFrame:
        """沪深港通资金流向"""
        pass

    # ----- 其他 (2个) -----
    @abstractmethod
    def get_retail_sales_yearly(self) -> pd.DataFrame:
        """社会消费品零售总额"""
        pass

    @abstractmethod
    def get_fixed_asset_investment(self) -> pd.DataFrame:
        """固定资产投资"""
        pass

    # ----- 已有接口（保持兼容） -----
    @abstractmethod
    def get_fund_manager(self, fund_code: str) -> dict[str, Any]:
        """获取基金经理信息"""
        pass

    @abstractmethod
    def get_fund_rating(self, fund_code: str) -> int | None:
        """获取基金评级"""
        pass

    @abstractmethod
    def batch_get_fund_nav(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """批量获取基金净值数据"""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self._name!r})"


class DataSourceError(Exception):
    """数据源错误"""

    pass


class DataNotFoundError(Exception):
    """数据未找到错误"""

    pass


class NetworkError(Exception):
    """网络错误"""

    pass

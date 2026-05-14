"""
Qieman MCP 适配器

基于且慢 MCP 服务器实现数据获取，支持基金分析、归因分析、组合诊断等功能。
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from fund_cli.data.adapters.qieman.client import QiemanMCPClient, QiemanMCPError
from fund_cli.data.adapters.qieman.tools import (
    QIEMAN_TOOLS,
    TOOL_STATS,
    get_tool_definition,
    list_all_tools,
)
from fund_cli.data.base import (
    DataNotFoundError,
    DataSourceAdapter,
    DataSourceError,
)
from fund_cli.data.cache import DataCache

logger = logging.getLogger(__name__)


class QiemanAdapter(DataSourceAdapter):
    """
    Qieman MCP 适配器
    
    通过 MCP 协议与且慢服务器通信，提供基金数据分析能力。
    
    Attributes:
        api_key: API 密钥
        base_url: MCP 服务器 URL
        timeout: 请求超时时间
        cache: 缓存管理器
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        timeout: int | None = None,
        cache: DataCache | None = None,
        max_retries: int | None = None,
    ):
        """
        初始化 Qieman 适配器
        
        Args:
            api_key: API 密钥
            base_url: MCP 服务器 URL
            timeout: 请求超时时间
            cache: 缓存管理器
            max_retries: 最大重试次数（已弃用，保留兼容性）
        """
        super().__init__("qieman")
        self._client = QiemanMCPClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self._cache = cache
    
    def is_available(self) -> bool:
        """检查 Qieman MCP 服务是否可用"""
        return self._client.health_check()
    
    def _call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
            
        Raises:
            DataSourceError: 调用失败
            DataNotFoundError: 数据不存在
        """
        try:
            return self._client.call_tool(tool_name, arguments)
        except QiemanMCPError as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "不存在" in error_msg:
                raise DataNotFoundError(f"数据不存在: {e}") from e
            raise DataSourceError(f"MCP 调用失败: {e}") from e
    
    def _to_dataframe(
        self,
        data: list[dict] | dict,
        orient: str = "records",
    ) -> pd.DataFrame:
        """
        将数据转换为 DataFrame
        
        Args:
            data: 数据
            orient: 数据方向
            
        Returns:
            DataFrame
        """
        if isinstance(data, dict):
            if "data" in data:
                data = data["data"]
            elif "items" in data:
                data = data["items"]
            elif "list" in data:
                data = data["list"]
        
        if not data:
            return pd.DataFrame()
        
        if isinstance(data, list):
            return pd.DataFrame(data)
        else:
            return pd.DataFrame([data])
    
    def _format_date(self, d: date | str | None) -> str | None:
        """格式化日期"""
        if d is None:
            return None
        if isinstance(d, str):
            return d
        return d.strftime("%Y-%m-%d")
    
    # =========================================================================
    # P0 核心接口实现
    # =========================================================================
    
    def get_fund_holdings(
        self,
        fund_codes: str | list[str],
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金持仓数据
        
        Args:
            fund_code: 基金代码
            report_date: 报告日期
            
        Returns:
            持仓数据 DataFrame
        """
        if isinstance(fund_codes, str):
            fund_codes = [fund_codes]
        arguments = {
            "fundCodes": fund_codes,
        }
        if report_date:
            arguments["reportDate"] = self._format_date(report_date)
        
        result = self._call_tool("BatchGetFundsHolding", arguments)
        
        # 解析结果
        if isinstance(result, list) and len(result) > 0:
            holdings = result[0]
        elif isinstance(result, dict):
            holdings = result.get(fund_codes[0], result)
        else:
            holdings = result
        return self._to_dataframe(holdings.get("stockHoldings", holdings) if isinstance(holdings, dict) else holdings)
    
    def batch_get_fund_holdings(
        self,
        fund_codes: list[str],
        report_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        批量获取基金持仓数据
        
        Args:
            fund_codes: 基金代码列表
            report_date: 报告日期
            
        Returns:
            基金代码到持仓 DataFrame 的映射
        """
        arguments = {
            "fundCodes": fund_codes,
        }
        if report_date:
            arguments["reportDate"] = self._format_date(report_date)
        
        result = self._call_tool("BatchGetFundsHolding", arguments)
        
        holdings_dict = {}
        for fund_code in fund_codes:
            holdings = result.get(fund_code, {})
            holdings_dict[fund_code] = self._to_dataframe(
                holdings.get("stockHoldings", holdings)
            )
        
        return holdings_dict
    
    def get_brinson_indicator(
        self,
        fund_code: str,
        time_period: str = "LAST_YEAR",
        start_date: date | None = None,
        end_date: date | None = None,
        benchmark_code: str | None = None,
    ) -> dict[str, Any]:
        """
        获取 Brinson 归因分析指标
        
        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            benchmark_code: 基准代码
            
        Returns:
            Brison 归因分析结果
        """
        arguments = {
            "fundCode": fund_code,
            "timePeriod": time_period,
        }
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        if benchmark_code:
            arguments["benchmarkCode"] = benchmark_code
        
        return self._call_tool("getFundBrinsonIndicator", arguments)
    
    def diagnose_portfolio(
        self,
        fund_codes: list[str],
        weights: list[float] | None = None,
        analysis_date: date | None = None,
    ) -> dict[str, Any]:
        """
        诊断基金组合
        
        Args:
            fund_codes: 基金代码列表
            weights: 基金权重列表
            analysis_date: 分析日期
            
        Returns:
            组合诊断结果
        """
        arguments = {
            "fundCodes": fund_codes,
        }
        if weights:
            arguments["weights"] = weights
        if analysis_date:
            arguments["analysisDate"] = self._format_date(analysis_date)
        
        return self._call_tool("DiagnoseFundPortfolio", arguments)
    
    def backtest_portfolio(
        self,
        fund_codes: list[str],
        weights: list[float] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        rebalance_frequency: str | None = None,
    ) -> dict[str, Any]:
        """
        基金组合回测分析
        
        Args:
            fund_codes: 基金代码列表
            weights: 基金权重列表
            start_date: 回测开始日期
            end_date: 回测结束日期
            rebalance_frequency: 再平衡频率
            
        Returns:
            回测结果
        """
        if weights is None:
            weights = [1.0 / len(fund_codes)] * len(fund_codes)
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()
        arguments = {
            "fundCodes": fund_codes,
            "weights": weights,
            "startDate": self._format_date(start_date),
            "endDate": self._format_date(end_date),
        }
        if rebalance_frequency:
            arguments["rebalanceFrequency"] = rebalance_frequency
        
        return self._call_tool("GetFundsBackTest", arguments)
    
    def get_fund_nav_history(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """
        批量获取基金历史净值数据
        
        Args:
            fund_codes: 基金代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            基金代码到净值 DataFrame 的映射
        """
        arguments = {
            "fundCodes": fund_codes,
        }
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("BatchGetFundNavHistory", arguments)
        
        nav_dict = {}
        for fund_code in fund_codes:
            nav_data = result.get(fund_code, [])
            df = self._to_dataframe(nav_data)
            if not df.empty and "nav_date" in df.columns:
                df["nav_date"] = pd.to_datetime(df["nav_date"])
            nav_dict[fund_code] = df
        
        return nav_dict
    
    def get_fund_performance(
        self,
        fund_codes: list[str],
        indicators: list[str] | None = None,
    ) -> pd.DataFrame:
        """
        批量获取基金业绩表现数据
        
        Args:
            fund_codes: 基金代码列表
            indicators: 业绩指标列表
            
        Returns:
            业绩数据 DataFrame
        """
        arguments = {
            "fundCodes": fund_codes,
        }
        if indicators:
            arguments["indicators"] = indicators
        
        result = self._call_tool("GetBatchFundPerformance", arguments)
        return self._to_dataframe(result)
    
    def get_fund_details(
        self,
        fund_codes: list[str],
    ) -> pd.DataFrame:
        """
        批量获取基金详细信息
        
        Args:
            fund_codes: 基金代码列表
            
        Returns:
            基金详情 DataFrame
        """
        result = self._call_tool("BatchGetFundsDetail", {"fundCodes": fund_codes})
        return self._to_dataframe(result)
    
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
            min_scale: 最小规模（亿元）
            max_scale: 最大规模（亿元）
            keyword: 关键词
            limit: 返回数量限制
            
        Returns:
            基金列表 DataFrame
        """
        arguments = {"limit": limit}
        if keyword:
            arguments["keyword"] = keyword
        if fund_type:
            arguments["fundType"] = fund_type
        if company:
            arguments["company"] = company
        if min_scale is not None:
            arguments["minScale"] = min_scale
        if max_scale is not None:
            arguments["maxScale"] = max_scale
        
        result = self._call_tool("SearchFunds", arguments)
        return self._to_dataframe(result)
    
    def get_funds_correlation(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金相关性分析矩阵
        
        Args:
            fund_codes: 基金代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            相关性矩阵 DataFrame
        """
        arguments = {
            "fundCodes": fund_codes,
        }
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("GetFundsCorrelation", arguments)
        
        # 转换相关性矩阵
        matrix = result.get("correlationMatrix", result) if isinstance(result, dict) else result
        if isinstance(matrix, dict):
            # 确保有index
            if matrix:
                return pd.DataFrame(matrix, index=list(matrix.keys()))
            return pd.DataFrame()
        return self._to_dataframe(matrix)
    
    def analyze_fund_risk(
        self,
        fund_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """
        分析基金风险指标
        
        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            风险分析结果
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()
        arguments = {
            "fundCode": fund_code,
        }
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        return self._call_tool("AnalyzeFundRisk", arguments)
    
    # =========================================================================
    # P1 扩展接口实现
    # =========================================================================
    
    def get_campisi_indicator(
        self,
        fund_code: str,
        time_period: str = "LAST_YEAR",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """
        获取 Campisi 归因分析指标
        
        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Campisi 归因分析结果
        """
        arguments = {
            "fundCode": fund_code,
            "timePeriod": time_period,
        }
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        return self._call_tool("getFundCampisiIndicator", arguments)
    
    def get_bond_indicator(self, fund_code: str) -> dict[str, Any]:
        """
        获取债券基金指标数据
        
        Args:
            fund_code: 基金代码
            
        Returns:
            债券基金指标
        """
        return self._call_tool("getBondIndicator", {"fundCode": fund_code})
    
    def get_market_timing_indicator(
        self,
        fund_code: str,
        time_range: str = "LAST_YEAR",
    ) -> dict[str, Any]:
        """
        获取基金择时能力指标
        
        Args:
            fund_code: 基金代码
            time_range: 时间区间
            
        Returns:
            择时能力指标
        """
        arguments = {
            "fundCode": fund_code,
            "timeRange": time_range,
        }
        
        return self._call_tool("getMarketTimingIndicator", arguments)
    
    def get_turnover_rate(
        self,
        fund_code: str,
        year: int | None = None,
    ) -> dict[str, Any]:
        """
        获取基金换手率数据
        
        Args:
            fund_code: 基金代码
            year: 年份
            
        Returns:
            换手率数据
        """
        arguments = {"fundCode": fund_code}
        if year:
            arguments["year"] = year
        
        return self._call_tool("getFundTurnoverRate", arguments)
    
    def analyze_financial_indicators(
        self,
        fund_code: str | None = None,
        indicators: list[str] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        分析基金财务指标
        
        Args:
            fund_code: 基金代码
            indicators: 指标列表
            **kwargs: 其他参数（total_assets, net_profit等）
            
        Returns:
            财务指标分析结果
        """
        arguments: dict[str, Any] = {}
        if fund_code:
            arguments["fundCode"] = fund_code
        if indicators:
            arguments["indicators"] = indicators
        arguments.update(kwargs)
        
        return self._call_tool("AnalyzeFinancialIndicators", arguments)
    
    def get_industry_preference(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金行业偏好分析
        
        Args:
            fund_code: 基金代码
            report_date: 报告日期
            
        Returns:
            行业偏好 DataFrame
        """
        arguments = {"fundCode": fund_code}
        if report_date:
            arguments["reportDate"] = self._format_date(report_date)
        
        result = self._call_tool("getFundIndustryPreference", arguments)
        return self._to_dataframe(result)
    
    def get_industry_returns(
        self,
        fund_code: str,
        time_range: str = "LAST_YEAR",
    ) -> pd.DataFrame:
        """
        获取基金行业收益贡献分析
        
        Args:
            fund_code: 基金代码
            time_range: 时间区间
            
        Returns:
            行业收益贡献 DataFrame
        """
        arguments = {
            "fundCode": fund_code,
            "timeRange": time_range,
        }
        
        result = self._call_tool("getFundIndustryReturns", arguments)
        return self._to_dataframe(result)
    
    def get_industry_allocation(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金行业配置数据
        
        Args:
            fund_code: 基金代码
            report_date: 报告日期
            
        Returns:
            行业配置 DataFrame
        """
        arguments = {"fundCode": fund_code}
        if report_date:
            arguments["reportDate"] = self._format_date(report_date)
        
        result = self._call_tool("getFundIndustryAllocation", arguments)
        return self._to_dataframe(result)
    
    def get_industry_concentration(
        self,
        fund_code: str,
        top_n: int = 3,
    ) -> dict[str, Any]:
        """
        获取基金行业集中度分析
        
        Args:
            fund_code: 基金代码
            top_n: 前N大行业
            
        Returns:
            行业集中度分析结果
        """
        return self._call_tool(
            "getFundIndustryConcentration",
            {"fundCode": fund_code, "topN": top_n},
        )
    
    def get_stock_allocation(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金股票配置及相关指标
        
        Args:
            fund_code: 基金代码
            report_date: 报告日期
            
        Returns:
            股票配置 DataFrame
        """
        arguments = {"fundCode": fund_code}
        if report_date:
            arguments["reportDate"] = self._format_date(report_date)
        
        result = self._call_tool("getStockAllocationAndMetricsByFundCode", arguments)
        return self._to_dataframe(result)
    
    def get_bond_allocation(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金债券配置数据
        
        Args:
            fund_code: 基金代码
            report_date: 报告日期
            
        Returns:
            债券配置 DataFrame
        """
        arguments = {"fundCode": fund_code}
        if report_date:
            arguments["reportDate"] = self._format_date(report_date)
        
        result = self._call_tool("getBondAllocationByFundCode", arguments)
        return self._to_dataframe(result)
    
    def get_bond_credit_rating(self, fund_code: str) -> pd.DataFrame:
        """
        获取债券基金信用评级分布
        
        Args:
            fund_code: 基金代码
            
        Returns:
            信用评级分布 DataFrame
        """
        result = self._call_tool("getBondFundCreditRatingLevel", {"fundCode": fund_code})
        return self._to_dataframe(result)
    
    def get_bond_alert_funds(
        self,
        alert_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        diving_threshold: float | None = None,
    ) -> pd.DataFrame:
        """
        获取有预警记录的债券基金列表
        
        Args:
            alert_type: 预警类型
            start_date: 开始日期
            end_date: 结束日期
            diving_threshold: 预警阈值（浮点数）
            
        Returns:
            预警基金列表 DataFrame
        """
        arguments: dict[str, Any] = {"bondAlterType": alert_type or "DIVE", "divingThreshold": diving_threshold or -0.03}
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("getBondFundWithAlertRecord", arguments)
        return self._to_dataframe(result)
    
    def filter_by_turnover(
        self,
        min_turnover: float | None = None,
        max_turnover: float | None = None,
        year: int | None = None,
    ) -> pd.DataFrame:
        """
        按股票换手率筛选股票型基金
        
        Args:
            min_turnover: 最小换手率
            max_turnover: 最大换手率
            year: 年份
            
        Returns:
            筛选结果 DataFrame
        """
        arguments = {}
        if min_turnover is not None:
            arguments["minTurnover"] = min_turnover
        if max_turnover is not None:
            arguments["maxTurnover"] = max_turnover
        if year:
            arguments["year"] = year
        
        result = self._call_tool("filterStockFundByStockTurnover", arguments)
        return self._to_dataframe(result)
    
    def filter_by_bond_type(
        self,
        bond_type: str,
        min_ratio: float | None = None,
    ) -> pd.DataFrame:
        """
        按债券类型筛选债券型基金
        
        Args:
            bond_type: 债券类型
            min_ratio: 最小占比
            
        Returns:
            筛选结果 DataFrame
        """
        arguments = {"bondType": bond_type}
        if min_ratio is not None:
            arguments["minRatio"] = min_ratio
        
        result = self._call_tool("filterBondFundByBondType", arguments)
        return self._to_dataframe(result)
    
    def filter_by_credit_rating(
        self,
        rating_level: str,
        min_ratio: float | None = None,
    ) -> pd.DataFrame:
        """
        按信用评级筛选债券型基金
        
        Args:
            rating_level: 评级等级
            min_ratio: 最小占比
            
        Returns:
            筛选结果 DataFrame
        """
        arguments = {"ratingLevel": rating_level}
        if min_ratio is not None:
            arguments["minRatio"] = min_ratio
        
        result = self._call_tool("filterBondFundByCreditRating", arguments)
        return self._to_dataframe(result)
    
    def get_qdii_area_allocation(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取 QDII 基金区域配置数据
        
        Args:
            fund_code: 基金代码
            report_date: 报告日期
            
        Returns:
            区域配置 DataFrame
        """
        arguments = {"fundCode": fund_code}
        if report_date:
            arguments["reportDate"] = self._format_date(report_date)
        
        result = self._call_tool("getQdFundAreaAllocation", arguments)
        return self._to_dataframe(result)
    
    def get_benchmark_info(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金基准信息
        
        Args:
            fund_code: 基金代码
            
        Returns:
            基准信息
        """
        return self._call_tool("getFundBenchmarkInfo", {"fundCode": fund_code})
    
    def get_fund_diagnosis(
        self,
        fund_code: str,
        analysis_type: str | None = None,
    ) -> dict[str, Any]:
        """
        获取基金诊断报告
        
        Args:
            fund_code: 基金代码
            analysis_type: 分析类型
            
        Returns:
            诊断报告
        """
        arguments = {"fundCode": fund_code}
        if analysis_type:
            arguments["analysisType"] = analysis_type
        
        return self._call_tool("GetFundDiagnosis", arguments)
    
    def get_popular_funds(
        self,
        fund_type: str | None = None,
        period: str | None = None,
        limit: int = 20,
    ) -> pd.DataFrame:
        """
        获取热门基金列表
        
        Args:
            fund_type: 基金类型
            period: 统计周期
            limit: 返回数量
            
        Returns:
            热门基金列表 DataFrame
        """
        arguments = {"limit": limit}
        if fund_type:
            arguments["fundType"] = fund_type
        if period:
            arguments["period"] = period
        
        result = self._call_tool("GetPopularFund", arguments)
        return self._to_dataframe(result)
    
    # =========================================================================
    # P2 扩展接口实现
    # =========================================================================
    
    # ----- 资产配置接口 -----
    
    def get_asset_allocation(
        self,
        risk_level: str | None = None,
        investment_period: str | None = None,
    ) -> dict[str, Any]:
        """
        获取资产配置建议
        
        Args:
            risk_level: 风险等级
            investment_period: 投资期限
            
        Returns:
            资产配置建议
        """
        arguments = {}
        if risk_level:
            arguments["riskLevel"] = risk_level
        if investment_period:
            arguments["investmentPeriod"] = investment_period
        
        return self._call_tool("GetAssetAllocation", arguments)
    
    def get_fund_asset_class_analysis(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金资产类别分析
        
        Args:
            fund_code: 基金代码
            
        Returns:
            资产类别分析结果
        """
        return self._call_tool("GetFundAssetClassAnalysis", {"fundCode": fund_code})
    
    def monte_carlo_simulate(
        self,
        fund_codes: list[str],
        weights: list[float],
        simulation_count: int = 1000,
        years: int = 10,
    ) -> dict[str, Any]:
        """
        蒙特卡洛模拟分析
        
        Args:
            fund_codes: 基金代码列表
            weights: 权重列表
            simulation_count: 模拟次数
            years: 模拟年数
            
        Returns:
            模拟结果
        """
        return self._call_tool(
            "MonteCarloSimulate",
            {
                "fundCodes": fund_codes,
                "weights": weights,
                "simulationCount": simulation_count,
                "years": years,
            },
        )
    
    def get_asset_allocation_plan(self, plan_id: str) -> dict[str, Any]:
        """
        获取资产配置方案
        
        Args:
            plan_id: 方案ID
            
        Returns:
            资产配置方案
        """
        return self._call_tool("GetAssetAllocationPlan", {"planId": plan_id})
    
    def get_composite_model(self, model_id: str) -> dict[str, Any]:
        """
        获取组合模型详情
        
        Args:
            model_id: 模型ID
            
        Returns:
            组合模型详情
        """
        return self._call_tool("GetCompositeModel", {"modelId": model_id})
    
    def analyze_portfolio_risk(
        self,
        fund_codes: list[str],
        weights: list[float] | None = None,
    ) -> dict[str, Any]:
        """
        分析组合风险
        
        Args:
            fund_codes: 基金代码列表
            weights: 权重列表
            
        Returns:
            组合风险分析结果
        """
        if weights is None:
            weights = [1.0 / len(fund_codes)] * len(fund_codes)
        return self._call_tool(
            "AnalyzePortfolioRisk",
            {"fundCodes": fund_codes, "weights": weights},
        )
    
    # ----- 行情资讯接口 -----
    
    def get_latest_quotations(self, symbols: list[str]) -> pd.DataFrame:
        """
        获取最新行情数据
        
        Args:
            symbols: 证券代码列表
            
        Returns:
            行情数据 DataFrame
        """
        result = self._call_tool("GetLatestQuotations", {"symbols": symbols})
        return self._to_dataframe(result)
    
    def search_hot_topic(
        self,
        keyword: str | None = None,
        limit: int = 20,
    ) -> pd.DataFrame:
        """
        搜索热门话题
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量
            
        Returns:
            热门话题 DataFrame
        """
        arguments = {"limit": limit}
        if keyword:
            arguments["keyword"] = keyword
        
        result = self._call_tool("SearchHotTopic", arguments)
        return self._to_dataframe(result)
    
    def search_financial_news(
        self,
        keyword: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 20,
    ) -> pd.DataFrame:
        """
        搜索财经新闻
        
        Args:
            keyword: 搜索关键词
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量
            
        Returns:
            财经新闻 DataFrame
        """
        arguments = {"limit": limit}
        if keyword:
            arguments["keyword"] = keyword
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("SearchFinancialNews", arguments)
        return self._to_dataframe(result)
    
    def search_realtime_ai_analysis(self, topic: str) -> dict[str, Any]:
        """
        搜索实时 AI 分析
        
        Args:
            topic: 分析主题
            
        Returns:
            AI 分析结果
        """
        return self._call_tool("searchRealtimeAiAnalysis", {"topic": topic})
    
    def search_manager_viewpoint(
        self,
        fund_code: str | None = None,
        manager_name: str | None = None,
    ) -> pd.DataFrame:
        """
        搜索基金经理观点
        
        Args:
            fund_code: 基金代码
            manager_name: 基金经理姓名
            
        Returns:
            基金经理观点 DataFrame
        """
        arguments = {}
        if fund_code:
            arguments["fundCode"] = fund_code
        if manager_name:
            arguments["managerName"] = manager_name
        
        result = self._call_tool("SearchManagerViewpoint", arguments)
        return self._to_dataframe(result)
    
    def search_invest_advisor_content(
        self,
        keyword: str | None = None,
        content_type: str | None = None,
    ) -> pd.DataFrame:
        """
        搜索投顾内容
        
        Args:
            keyword: 搜索关键词
            content_type: 内容类型
            
        Returns:
            投顾内容 DataFrame
        """
        arguments = {}
        if keyword:
            arguments["keyword"] = keyword
        if content_type:
            arguments["contentType"] = content_type
        
        result = self._call_tool("searchInvestAdvisorContent", arguments)
        return self._to_dataframe(result)
    
    def get_current_time(self) -> dict[str, Any]:
        """
        获取当前服务器时间
        
        Returns:
            当前时间信息
        """
        return self._call_tool("GetCurrentTime")
    
    # ----- 策略接口 -----
    
    def get_strategy_details(self, strategy_id: str) -> dict[str, Any]:
        """
        获取策略详情
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            策略详情
        """
        return self._call_tool("GetStrategyDetails", {"strategyId": strategy_id})
    
    def batch_get_strategies_composition(
        self,
        strategy_ids: list[str],
    ) -> dict[str, Any]:
        """
        批量获取策略组合
        
        Args:
            strategy_ids: 策略ID列表
            
        Returns:
            策略组合映射
        """
        return self._call_tool(
            "BatchGetStrategiesComposition",
            {"strategyIds": strategy_ids},
        )
    
    def get_strategy_asset_class_analysis(self, strategy_id: str) -> dict[str, Any]:
        """
        获取策略资产类别分析
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            资产类别分析结果
        """
        return self._call_tool(
            "GetStrategyAssetClassAnalysis",
            {"strategyId": strategy_id},
        )
    
    def get_strategy_benchmark(self, strategy_id: str) -> dict[str, Any]:
        """
        获取策略基准
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            策略基准信息
        """
        return self._call_tool("GetStrategyBenchmark", {"strategyId": strategy_id})
    
    def get_strategy_risk_info(self, strategy_id: str) -> dict[str, Any]:
        """
        获取策略风险信息
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            策略风险信息
        """
        return self._call_tool("GetStrategyRiskInfo", {"strategyId": strategy_id})
    
    def batch_get_po_trade_composition(self, po_ids: list[str]) -> dict[str, Any]:
        """
        批量获取 PO 交易组合
        
        Args:
            po_ids: PO ID列表
            
        Returns:
            PO 交易组合映射
        """
        return self._call_tool("BatchGetPoTradeComposition", {"poIds": po_ids})
    
    def strategy_search_by_keyword(
        self,
        keyword: str,
        limit: int = 20,
    ) -> pd.DataFrame:
        """
        按关键词搜索策略
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量
            
        Returns:
            策略列表 DataFrame
        """
        result = self._call_tool(
            "StrategySearchByKeyword",
            {"keyword": keyword, "limit": limit},
        )
        return self._to_dataframe(result)
    
    # ----- 其他接口 -----
    
    def get_fund_announcement(
        self,
        fund_code: str | list[str] | None = None,
        announcement_type: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        获取基金公告
        
        Args:
            fund_code: 基金代码（支持单个代码或列表）
            announcement_type: 公告类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            公告列表 DataFrame
        """
        arguments: dict[str, Any] = {}
        # 兼容 fund_codes 关键字参数
        if "fund_codes" in kwargs:
            fund_code = kwargs.pop("fund_codes")
        if fund_code is not None:
            if isinstance(fund_code, list):
                arguments["fundCodes"] = fund_code
            else:
                arguments["fundCode"] = fund_code
        if announcement_type:
            arguments["announcementType"] = announcement_type
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        # 兼容其他额外关键字参数
        arguments.update(kwargs)
        
        result = self._call_tool("GetFundAnnouncement", arguments)
        return self._to_dataframe(result)
    
    def get_fund_dividend(
        self,
        fund_code: str,
        year: int | None = None,
    ) -> pd.DataFrame:
        """
        获取基金分红信息
        
        Args:
            fund_code: 基金代码
            year: 年份
            
        Returns:
            分红信息 DataFrame
        """
        arguments = {"fundCode": fund_code}
        if year:
            arguments["year"] = year
        
        result = self._call_tool("GetFundDividend", arguments)
        return self._to_dataframe(result)
    
    def get_fund_split(self, fund_code: str) -> pd.DataFrame:
        """
        获取基金拆分信息
        
        Args:
            fund_code: 基金代码
            
        Returns:
            拆分信息 DataFrame
        """
        result = self._call_tool("GetFundSplit", {"fundCode": fund_code})
        return self._to_dataframe(result)
    
    def get_fund_trade_rules(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金交易规则
        
        Args:
            fund_code: 基金代码
            
        Returns:
            交易规则
        """
        return self._call_tool("GetFundTradeRules", {"fundCode": fund_code})
    
    def get_fund_fee_info(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金费率信息
        
        Args:
            fund_code: 基金代码
            
        Returns:
            费率信息
        """
        return self._call_tool("GetFundFeeInfo", {"fundCode": fund_code})
    
    def get_fund_manager_info(self, manager_id: str) -> dict[str, Any]:
        """
        获取基金经理信息
        
        Args:
            manager_id: 基金经理ID
            
        Returns:
            基金经理信息
        """
        return self._call_tool("GetFundManagerInfo", {"managerId": manager_id})
    
    def get_fund_manager_performance(self, manager_id: str) -> dict[str, Any]:
        """
        获取基金经理业绩
        
        Args:
            manager_id: 基金经理ID
            
        Returns:
            基金经理业绩
        """
        return self._call_tool("GetFundManagerPerformance", {"managerId": manager_id})
    
    def get_fund_company_info(self, company_id: str) -> dict[str, Any]:
        """
        获取基金公司信息
        
        Args:
            company_id: 基金公司ID
            
        Returns:
            基金公司信息
        """
        return self._call_tool("GetFundCompanyInfo", {"companyId": company_id})
    
    def get_fund_company_products(self, company_id: str) -> pd.DataFrame:
        """
        获取基金公司产品列表
        
        Args:
            company_id: 基金公司ID
            
        Returns:
            产品列表 DataFrame
        """
        result = self._call_tool("GetFundCompanyProducts", {"companyId": company_id})
        return self._to_dataframe(result)
    
    def get_fund_rating(self, fund_code: str) -> int | None:
        """获取基金评级 - 基类兼容"""
        try:
            result = self._call_tool("GetFundRating", {"fundCodes": [fund_code]})
            if isinstance(result, list) and result:
                item = result[0]
                # 尝试多种字段名
                for key in ["rating", "score", "level", "fundRating"]:
                    val = item.get(key)
                    if val is not None:
                        if isinstance(val, (int, float)):
                            return int(val)
                        if isinstance(val, str) and val.isdigit():
                            return int(val)
            if isinstance(result, dict):
                for key in ["rating", "score", "level", "fundRating"]:
                    val = result.get(key)
                    if val is not None:
                        if isinstance(val, (int, float)):
                            return int(val)
            return None
        except Exception:
            return None
    
    def get_fund_rating_detail(
        self,
        fund_codes: list[str],
        rating_agency: str | None = None,
    ) -> dict[str, Any]:
        """
        获取基金评级
        
        Args:
            fund_code: 基金代码
            rating_agency: 评级机构
            
        Returns:
            基金评级
        """
        arguments = {"fundCodes": fund_codes}
        if rating_agency:
            arguments["ratingAgency"] = rating_agency
        
        return self._call_tool("GetFundRating", arguments)
    
    def get_fund_scale_history(
        self,
        fund_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金规模历史
        
        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            规模历史 DataFrame
        """
        arguments = {"fundCode": fund_code}
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("GetFundScaleHistory", arguments)
        return self._to_dataframe(result)
    
    def get_fund_holder_structure(self) -> pd.DataFrame:
        """天天基金-持有人结构(全市场汇总) - 基类兼容"""
        return pd.DataFrame()
    
    def get_fund_holder_structure_detail(
        self,
        fund_code: str,
        report_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取基金持有人结构
        
        Args:
            fund_code: 基金代码
            report_date: 报告日期
            
        Returns:
            持有人结构 DataFrame
        """
        arguments = {"fundCode": fund_code}
        if report_date:
            arguments["reportDate"] = self._format_date(report_date)
        
        result = self._call_tool("GetFundHolderStructure", arguments)
        return self._to_dataframe(result)
    
    def get_fund_style_analysis(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金风格分析
        
        Args:
            fund_code: 基金代码
            
        Returns:
            风格分析结果
        """
        return self._call_tool("GetFundStyleAnalysis", {"fundCode": fund_code})
    
    def get_fund_factor_exposure(self, fund_code: str) -> dict[str, Any]:
        """
        获取基金因子暴露
        
        Args:
            fund_code: 基金代码
            
        Returns:
            因子暴露
        """
        return self._call_tool("GetFundFactorExposure", {"fundCode": fund_code})
    
    def get_fund_performance_attribution(
        self,
        fund_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """
        获取基金业绩归因
        
        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            业绩归因结果
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()
        return self._call_tool(
            "GetFundPerformanceAttribution",
            {
                "fundCode": fund_code,
                "startDate": self._format_date(start_date),
                "endDate": self._format_date(end_date),
            },
        )
    
    def get_index_constituents(self, index_code: str) -> pd.DataFrame:
        """
        获取指数成分股
        
        Args:
            index_code: 指数代码
            
        Returns:
            成分股 DataFrame
        """
        result = self._call_tool("GetIndexConstituents", {"indexCode": index_code})
        return self._to_dataframe(result)
    
    def get_index_weights(self, index_code: str) -> pd.DataFrame:
        """
        获取指数权重
        
        Args:
            index_code: 指数代码
            
        Returns:
            权重 DataFrame
        """
        result = self._call_tool("GetIndexWeights", {"indexCode": index_code})
        return self._to_dataframe(result)
    
    def get_market_index_data(
        self,
        index_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取市场指数数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            指数数据 DataFrame
        """
        arguments = {"indexCode": index_code}
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("GetMarketIndexData", arguments)
        return self._to_dataframe(result)
    
    def _get_bond_yield_curve_mcp(
        self,
        bond_type: str,
        date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取债券收益率曲线
        
        Args:
            bond_type: 债券类型
            date: 日期
            
        Returns:
            收益率曲线 DataFrame
        """
        arguments = {"bondType": bond_type}
        if date:
            arguments["date"] = self._format_date(date)
        
        result = self._call_tool("GetBondYieldCurve", arguments)
        return self._to_dataframe(result)
    
    def get_credit_spread(
        self,
        rating_level: str = "AAA",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取信用利差数据
        
        Args:
            rating_level: 评级等级
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            信用利差 DataFrame
        """
        arguments = {"ratingLevel": rating_level}
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("GetCreditSpread", arguments)
        return self._to_dataframe(result)
    
    def get_macro_economic_data(
        self,
        indicator: str = "GDP年率",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取宏观经济数据
        
        Args:
            indicator: 经济指标
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            宏观经济数据 DataFrame
        """
        arguments = {"indicator": indicator}
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("GetMacroEconomicData", arguments)
        return self._to_dataframe(result)
    
    def render_pdf_report(
        self,
        template_id: str = "default",
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        渲染 PDF 报告
        
        Args:
            template_id: 模板ID
            data: 报告数据
            
        Returns:
            PDF 报告信息
        """
        if data is None:
            data = {}
        return self._call_tool(
            "RenderPdfReport",
            {"templateId": template_id, "data": data},
        )
    
    def get_user_portfolio(self, portfolio_id: str) -> dict[str, Any]:
        """
        获取用户组合
        
        Args:
            portfolio_id: 组合ID
            
        Returns:
            用户组合信息
        """
        return self._call_tool("GetUserPortfolio", {"portfolioId": portfolio_id})
    
    def get_user_transactions(
        self,
        portfolio_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """
        获取用户交易记录
        
        Args:
            portfolio_id: 组合ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易记录 DataFrame
        """
        arguments = {"portfolioId": portfolio_id}
        if start_date:
            arguments["startDate"] = self._format_date(start_date)
        if end_date:
            arguments["endDate"] = self._format_date(end_date)
        
        result = self._call_tool("GetUserTransactions", arguments)
        return self._to_dataframe(result)
    
    # =========================================================================
    # DataSourceAdapter 基类接口实现（兼容性方法）
    # =========================================================================
    
    def get_fund_info(self, fund_code: str) -> dict[str, Any]:
        """获取基金基础信息"""
        result = self._call_tool("BatchGetFundsDetail", {"fundCodes": [fund_code]})
        if isinstance(result, dict):
            funds = result.get("funds", [result])
            if funds:
                return funds[0]
        return result
    
    def get_all_fund_names(self) -> pd.DataFrame:
        """获取所有基金名称列表"""
        result = self.search_funds(limit=10000)
        return result
    
    def get_fund_info_ths(self, fund_code: str) -> dict[str, Any]:
        """同花顺-基金基本信息"""
        return self.get_fund_info(fund_code)
    
    def get_index_fund_info(
        self,
        category: str = "全部",
        indicator: str = "全部",
    ) -> pd.DataFrame:
        """东方财富-指数型基金基本信息"""
        return self.search_funds(fund_type="指数型", limit=1000)
    
    def get_fund_overview(self, fund_code: str) -> dict[str, Any]:
        """天天基金-基金档案基本概况"""
        return self.get_fund_info(fund_code)
    
    def get_fund_purchase_status(self) -> pd.DataFrame:
        """东方财富-基金申购/赎回状态"""
        return self.search_funds(limit=1000)
    
    def get_fund_nav(
        self,
        fund_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """获取基金净值数据"""
        nav_dict = self.get_fund_nav_history([fund_code], start_date, end_date)
        return nav_dict.get(fund_code, pd.DataFrame())
    
    def get_fund_daily_nav(self) -> pd.DataFrame:
        """东方财富-开放式基金每日净值(全部)"""
        return self.search_funds(limit=5000)
    
    def get_etf_spot(self) -> pd.DataFrame:
        """东方财富-ETF实时行情(全部)"""
        return self.search_funds(fund_type="ETF", limit=1000)
    
    def get_fund_category_spot(
        self,
        category: str = "",
        date: str | None = None,
    ) -> pd.DataFrame:
        """同花顺-基金实时行情(按类型)"""
        return self.search_funds(fund_type=category, limit=1000)
    
    def get_etf_spot_ths(self, date: str | None = None) -> pd.DataFrame:
        """同花顺-ETF实时行情"""
        return self.get_etf_spot()
    
    def get_lof_spot(self) -> pd.DataFrame:
        """东方财富-LOF实时行情(全部)"""
        return self.search_funds(fund_type="LOF", limit=1000)
    
    def get_etf_hist(
        self,
        fund_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """东方财富-ETF历史行情"""
        return self.get_fund_nav(
            fund_code,
            start_date and datetime.strptime(start_date, "%Y%m%d").date(),
            end_date and datetime.strptime(end_date, "%Y%m%d").date(),
        )
    
    def get_lof_hist(
        self,
        fund_code: str,
        period: str = "daily",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """东方财富-LOF历史行情"""
        return self.get_fund_nav(
            fund_code,
            start_date and datetime.strptime(start_date, "%Y%m%d").date(),
            end_date and datetime.strptime(end_date, "%Y%m%d").date(),
        )
    
    def get_etf_minute(
        self,
        fund_code: str,
        period: str = "1",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """东方财富-ETF分时行情"""
        return self.get_fund_nav(fund_code)
    
    def get_lof_minute(
        self,
        fund_code: str,
        period: str = "1",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        """东方财富-LOF分时行情"""
        return self.get_fund_nav(fund_code)
    
    def get_fund_bond_holdings(
        self,
        fund_code: str,
        year: int | None = None,
    ) -> pd.DataFrame:
        """天天基金-基金债券持仓"""
        return self.get_bond_allocation(fund_code)
    
    def get_fund_industry_allocation(
        self,
        fund_code: str,
        year: int | None = None,
    ) -> pd.DataFrame:
        """天天基金-行业配置"""
        return self.get_industry_allocation(fund_code)
    
    def get_fund_portfolio_change(
        self,
        fund_code: str,
        indicator: str = "累计买入",
        year: int | None = None,
    ) -> pd.DataFrame:
        """天天基金-重大变动(累计买入/卖出)"""
        return self.get_fund_holdings(fund_code)
    
    def get_all_fund_managers(self) -> pd.DataFrame:
        """天天基金-基金经理大全"""
        result = self.search_funds(limit=5000)
        if "manager" in result.columns:
            return result[["manager"]].drop_duplicates()
        return pd.DataFrame()
    
    def get_fund_list(self, fund_type: str | None = None) -> pd.DataFrame:
        """获取基金列表"""
        return self.search_funds(fund_type=fund_type, limit=5000)
    
    def get_benchmark_nav(
        self,
        benchmark_code: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.DataFrame:
        """获取基准指数净值数据"""
        return self.get_market_index_data(benchmark_code, start_date, end_date)
    
    def get_fund_fee(self, fund_code: str) -> dict[str, Any]:
        """获取基金费率信息"""
        return self.get_fund_fee_info(fund_code)
    
    def get_fund_company_aum(self) -> pd.DataFrame:
        """东方财富-基金公司管理规模排名"""
        return pd.DataFrame()
    
    def get_fund_aum_trend(self) -> pd.DataFrame:
        """东方财富-基金市场管理规模走势"""
        return pd.DataFrame()
    
    def get_fund_company_aum_history(self, year: int | None = None) -> pd.DataFrame:
        """东方财富-基金公司历年管理规模排行"""
        return pd.DataFrame()
    
    def get_fund_scale_change(self) -> pd.DataFrame:
        """天天基金-规模变动(全市场汇总)"""
        return pd.DataFrame()
    
    def get_fund_holder_structure_summary(self, fund_codes: str | list[str] | None = None) -> pd.DataFrame:
        """天天基金-持有人结构(全市场汇总)"""
        return pd.DataFrame()
    
    def get_fund_ratings(self) -> pd.DataFrame:
        """天天基金-基金评级总汇"""
        return pd.DataFrame()
    
    def get_fund_rating_sh(self, date: str | None = None) -> pd.DataFrame:
        """天天基金-上海证券评级"""
        return pd.DataFrame()
    
    def get_fund_rating_zs(self, date: str | None = None) -> pd.DataFrame:
        """天天基金-招商证券评级"""
        return pd.DataFrame()
    
    def get_fund_rating_ja(self, date: str | None = None) -> pd.DataFrame:
        """天天基金-济安金信评级"""
        return pd.DataFrame()
    
    def get_fund_dividends(
        self,
        year: int | None = None,
        fund_type: str = "",
        page: int = -1,
    ) -> pd.DataFrame:
        """天天基金-基金分红"""
        return pd.DataFrame()
    
    def get_fund_splits(
        self,
        year: int | None = None,
        fund_type: str = "",
        page: int = -1,
    ) -> pd.DataFrame:
        """天天基金-基金拆分"""
        return pd.DataFrame()
    
    def get_fund_dividend_rank(self) -> pd.DataFrame:
        """天天基金-基金累计分红排行"""
        return pd.DataFrame()
    
    def get_fund_rank_by_type(self, fund_type: str = "全部") -> pd.DataFrame:
        """东方财富-开放式基金排行"""
        return self.search_funds(fund_type=fund_type, limit=1000)
    
    def get_exchange_fund_rank(self) -> pd.DataFrame:
        """东方财富-场内交易基金排行"""
        return pd.DataFrame()
    
    def get_money_fund_rank(self) -> pd.DataFrame:
        """东方财富-货币型基金排行"""
        return self.search_funds(fund_type="货币型", limit=500)
    
    def get_lcx_fund_rank(self) -> pd.DataFrame:
        """东方财富-理财基金排行"""
        return pd.DataFrame()
    
    def get_hk_fund_rank(self) -> pd.DataFrame:
        """东方财富-香港基金排行"""
        return pd.DataFrame()
    
    def get_fund_achievement(self, fund_code: str) -> pd.DataFrame:
        """雪球-基金业绩(年度+阶段)"""
        result = self.get_fund_performance([fund_code])
        return result
    
    def get_fund_risk_analysis(self, fund_code: str) -> pd.DataFrame:
        """雪球-基金数据分析(夏普/回撤等)"""
        return pd.DataFrame()
    
    def get_fund_profit_probability(self, fund_code: str) -> pd.DataFrame:
        """雪球-基金盈利概率"""
        return pd.DataFrame()
    
    def get_fund_asset_allocation(
        self,
        fund_code: str,
        date: str | None = None,
    ) -> pd.DataFrame:
        """雪球-基金资产配置"""
        return self.get_industry_allocation(fund_code)
    
    def get_index_spot_em(self, category: str = "沪深重要指数") -> pd.DataFrame:
        """东财-沪深京指数实时行情"""
        return pd.DataFrame()
    
    def get_index_spot_sina(self) -> pd.DataFrame:
        """新浪-中国股票指数实时行情"""
        return pd.DataFrame()
    
    def get_index_daily_tx(
        self,
        code: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """腾讯-指数历史行情"""
        return self.get_market_index_data(code)
    
    def get_index_daily_em(
        self,
        code: str,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """东财-指数历史行情"""
        return self.get_market_index_data(code)
    
    def get_index_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """东财-指数通用历史行情"""
        return self.get_market_index_data(code)
    
    def get_index_minute(
        self,
        code: str,
        period: str = "1",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """东财-指数分时行情"""
        return pd.DataFrame()
    
    def get_macro_leverage_ratio(self) -> pd.DataFrame:
        """中国宏观杠杆率"""
        return self.get_macro_economic_data("宏观杠杆率")
    
    def get_enterprise_price_index(self) -> pd.DataFrame:
        """企业商品价格指数"""
        return self.get_macro_economic_data("企业商品价格指数")
    
    def get_fdi_data(self) -> pd.DataFrame:
        """外商直接投资数据"""
        return self.get_macro_economic_data("外商直接投资")
    
    def get_lpr_data(self) -> pd.DataFrame:
        """LPR品种数据"""
        return self.get_macro_economic_data("LPR")
    
    def get_urban_unemployment(self) -> pd.DataFrame:
        """城镇调查失业率"""
        return self.get_macro_economic_data("城镇调查失业率")
    
    def get_social_financing(self) -> pd.DataFrame:
        """社会融资规模增量"""
        return self.get_macro_economic_data("社会融资规模")
    
    def get_gdp_yearly(self) -> pd.DataFrame:
        """中国GDP年率"""
        return self.get_macro_economic_data("GDP年率")
    
    def get_gdp_quarterly(self) -> pd.DataFrame:
        """中国GDP季度数据"""
        return self.get_macro_economic_data("GDP季度")
    
    def get_cpi_yearly(self) -> pd.DataFrame:
        """中国CPI年率"""
        return self.get_macro_economic_data("CPI年率")
    
    def get_cpi_monthly(self) -> pd.DataFrame:
        """中国CPI月率"""
        return self.get_macro_economic_data("CPI月率")
    
    def get_ppi_yearly(self) -> pd.DataFrame:
        """中国PPI年率"""
        return self.get_macro_economic_data("PPI年率")
    
    def get_ppi_monthly(self) -> pd.DataFrame:
        """中国PPI月率"""
        return self.get_macro_economic_data("PPI月率")
    
    def get_exports_yearly(self) -> pd.DataFrame:
        """出口年率"""
        return self.get_macro_economic_data("出口年率")
    
    def get_imports_yearly(self) -> pd.DataFrame:
        """进口年率"""
        return self.get_macro_economic_data("进口年率")
    
    def get_trade_balance(self) -> pd.DataFrame:
        """贸易帐"""
        return self.get_macro_economic_data("贸易帐")
    
    def get_industrial_production(self) -> pd.DataFrame:
        """工业增加值增长"""
        return self.get_macro_economic_data("工业增加值")
    
    def get_pmi_official(self) -> pd.DataFrame:
        """官方制造业PMI"""
        return self.get_macro_economic_data("官方PMI")
    
    def get_pmi_caixin(self) -> pd.DataFrame:
        """财新制造业PMI"""
        return self.get_macro_economic_data("财新PMI")
    
    def get_services_pmi(self) -> pd.DataFrame:
        """财新服务业PMI"""
        return self.get_macro_economic_data("服务业PMI")
    
    def get_non_manufacturing_pmi(self) -> pd.DataFrame:
        """官方非制造业PMI"""
        return self.get_macro_economic_data("非制造业PMI")
    
    def get_m2_yearly(self) -> pd.DataFrame:
        """M2货币供应年率"""
        return self.get_macro_economic_data("M2年率")
    
    def get_new_loan(self) -> pd.DataFrame:
        """新增人民币贷款"""
        return self.get_macro_economic_data("新增贷款")
    
    def get_china_interest_rate(self) -> pd.DataFrame:
        """中国央行利率决议"""
        return self.get_macro_economic_data("央行利率")
    
    def get_usa_interest_rate(self) -> pd.DataFrame:
        """美联储利率决议"""
        return self.get_macro_economic_data("美联储利率")
    
    def get_euro_interest_rate(self) -> pd.DataFrame:
        """欧洲央行利率决议"""
        return self.get_macro_economic_data("欧洲央行利率")
    
    def get_japan_interest_rate(self) -> pd.DataFrame:
        """日本央行利率决议"""
        return self.get_macro_economic_data("日本央行利率")
    
    def get_uk_interest_rate(self) -> pd.DataFrame:
        """英国央行利率决议"""
        return self.get_macro_economic_data("英国央行利率")
    
    def get_shibor(self) -> pd.DataFrame:
        """SHIBOR利率"""
        return self.get_macro_economic_data("SHIBOR")
    
    def get_shibor_lpr(self) -> pd.DataFrame:
        """SHIBOR-LPR"""
        return self.get_macro_economic_data("LPR")
    
    def get_hibor(self) -> pd.DataFrame:
        """人民币香港银行同业拆息"""
        return self.get_macro_economic_data("HIBOR")
    
    def get_industry_boards(self) -> pd.DataFrame:
        """行业板块列表"""
        return pd.DataFrame()
    
    def get_industry_board_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """行业板块历史行情"""
        return pd.DataFrame()
    
    def get_concept_boards(self) -> pd.DataFrame:
        """概念板块列表"""
        return pd.DataFrame()
    
    def get_concept_board_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """概念板块历史行情"""
        return pd.DataFrame()
    
    def get_sector_fund_flow(self, period: str = "今日") -> pd.DataFrame:
        """板块资金流向"""
        return pd.DataFrame()
    
    def get_china_us_bond_yield(self) -> pd.DataFrame:
        """中美国债收益率"""
        return pd.DataFrame()
    
    def get_bond_yield_curve(
        self,
        bond_type: str = "国债",
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """收盘收益率曲线"""
        return self._get_bond_yield_curve_mcp(bond_type)
    
    def get_bond_spot_quote(self) -> pd.DataFrame:
        """现券市场做市报价"""
        return pd.DataFrame()
    
    def get_convertible_bonds(self) -> pd.DataFrame:
        """可转债数据一览"""
        return pd.DataFrame()
    
    def get_convertible_bond_detail(self, code: str) -> dict[str, Any]:
        """可转债详情"""
        return {}
    
    def get_bond_spot(self, code: str) -> pd.DataFrame:
        """沪深债券实时行情"""
        return pd.DataFrame()
    
    def get_bond_hist(
        self,
        code: str,
        period: str = "daily",
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """沪深债券历史行情"""
        return pd.DataFrame()
    
    def get_a_share_valuation(self) -> pd.DataFrame:
        """A股等权重与中位数PE/PB"""
        return pd.DataFrame()
    
    def get_stock_valuation_lg(self, code: str) -> pd.DataFrame:
        """个股估值-乐咕乐股"""
        return pd.DataFrame()
    
    def get_index_valuation(
        self,
        code: str,
        indicator: str = "pe",
    ) -> pd.DataFrame:
        """指数估值-乐咕乐股"""
        return pd.DataFrame()
    
    def get_market_pe_lg(self, code: str) -> pd.DataFrame:
        """指数市盈率-乐咕乐股"""
        return pd.DataFrame()
    
    def get_market_pb_lg(self, code: str) -> pd.DataFrame:
        """指数市净率-乐咕乐股"""
        return pd.DataFrame()
    
    def get_market_fund_flow(self) -> pd.DataFrame:
        """大盘资金流向"""
        return pd.DataFrame()
    
    def get_stock_fund_flow(
        self,
        code: str,
        market: str = "sh",
    ) -> pd.DataFrame:
        """个股资金流向"""
        return pd.DataFrame()
    
    def get_north_fund_flow(self, market: str = "北向资金") -> pd.DataFrame:
        """沪深港通资金流向"""
        return pd.DataFrame()
    
    def get_retail_sales_yearly(self) -> pd.DataFrame:
        """社会消费品零售总额"""
        return self.get_macro_economic_data("社会消费品零售总额")
    
    def get_fixed_asset_investment(self) -> pd.DataFrame:
        """固定资产投资"""
        return self.get_macro_economic_data("固定资产投资")
    
    def get_fund_manager(self, fund_code: str) -> dict[str, Any]:
        """获取基金经理信息"""
        info = self.get_fund_info(fund_code)
        return {"manager": info.get("manager", "")}
    
    def get_fund_rating_base(self, fund_code: str) -> int | None:
        """获取基金评级（基类兼容性方法）"""
        result = self._call_tool("GetFundRating", {"fundCode": fund_code})
        return result.get("rating")
    
    def batch_get_fund_nav(
        self,
        fund_codes: list[str],
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, pd.DataFrame]:
        """批量获取基金净值数据"""
        return self.get_fund_nav_history(fund_codes, start_date, end_date)
    
    # =========================================================================
    # 工具管理方法
    # =========================================================================
    
    def list_tools(self) -> list[str]:
        """
        列出所有可用工具
        
        Returns:
            工具名称列表
        """
        return list_all_tools()
    
    def get_tool_stats(self) -> dict[str, Any]:
        """
        获取工具统计信息
        
        Returns:
            工具统计信息
        """
        return TOOL_STATS.copy()
    
    def get_client(self) -> QiemanMCPClient:
        """
        获取 MCP 客户端实例
        
        Returns:
            MCP 客户端
        """
        return self._client

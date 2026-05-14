"""
全球化配置分析器

分析海外资产配置的超额收益
"""

from typing import Any

import pandas as pd


class GlobalAllocationAnalyzer:
    """
    全球化配置分析器
    
    功能：
    - 计算全球化配置超额收益（vs MSCI全球指数）
    - 分析各地区贡献
    - 评估全球化配置效果
    - 分析美股科技七巨头配置
    """
    
    # 科技七巨头关键词
    TECH_GIANTS = [
        "苹果", "Apple", "微软", "Microsoft", "谷歌", "Google", 
        "亚马逊", "Amazon", "英伟达", "NVIDIA", "Meta", "特斯拉", "Tesla",
        "META", "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA"
    ]
    
    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import get_data_manager
        self._dm = data_manager or get_data_manager()
    
    def analyze_global_allocation(
        self,
        fund_codes: list[str],
        weights: list[float],
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """
        全球化配置分析
        
        Args:
            fund_codes: 基金代码列表
            weights: 权重列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            {
                "海外资产占比": x,
                "全球化超额收益": {...},
                "各地区贡献": {...},
                "美股科技配置": {...},
                "评价": str,
            }
        """
        result = {}
        
        # 1. 计算海外资产占比
        from fund_cli.analysis.asset_lookthrough import AssetLookthroughAnalyzer
        lookthrough = AssetLookthroughAnalyzer(self._dm)
        
        values = dict(zip(fund_codes, weights))
        country_alloc = lookthrough.country_lookthrough(fund_codes, values)
        
        result["海外资产占比"] = country_alloc.get("海外", 0)
        result["国内资产占比"] = country_alloc.get("国内", 0)
        
        # 2. 计算全球化超额收益
        excess_return = self._calculate_global_excess_return(
            fund_codes, weights, start_date, end_date
        )
        result["全球化超额收益"] = excess_return
        
        # 3. 分析各地区贡献
        result["各地区贡献"] = self._analyze_regional_contribution(
            fund_codes, weights, start_date, end_date
        )
        
        # 4. 分析美股科技配置（科技七巨头）
        result["美股科技配置"] = self._analyze_us_tech_allocation(
            fund_codes, values
        )
        
        # 5. 生成评价
        result["评价"] = self._generate_global_evaluation(result)
        
        return result
    
    def _calculate_global_excess_return(
        self,
        fund_codes: list[str],
        weights: list[float],
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """计算相对MSCI全球指数的超额收益"""
        from fund_cli.analysis.portfolio_nav import PortfolioNavCalculator
        
        calculator = PortfolioNavCalculator(self._dm)
        
        try:
            # 计算组合收益
            portfolio_nav = calculator.compute_portfolio_nav(
                fund_codes, weights, start_date, end_date
            )
            portfolio_return = portfolio_nav.iloc[-1] / portfolio_nav.iloc[0] - 1
        except Exception:
            portfolio_return = 0
        
        # 获取MSCI全球指数收益（使用QDII股票型基金指数作为代理）
        benchmark_return = 0
        try:
            # 尝试获取QDII基金指数
            benchmark_nav = self._dm.get_index_nav("885065.WI", start_date, end_date)
            if benchmark_nav is not None and not benchmark_nav.empty:
                nav_col = "accumulated_nav" if "accumulated_nav" in benchmark_nav.columns else "unit_nav"
                benchmark_return = benchmark_nav[nav_col].iloc[-1] / benchmark_nav[nav_col].iloc[0] - 1
        except Exception:
            # 使用固定基准（简化）
            pass
        
        excess = portfolio_return - benchmark_return
        
        return {
            "组合收益": round(portfolio_return * 100, 2),
            "MSCI全球指数收益": round(benchmark_return * 100, 2),
            "超额收益": round(excess * 100, 2),
            "结论": "跑赢" if excess > 0.02 else "跑输" if excess < -0.02 else "持平",
        }
    
    def _analyze_regional_contribution(
        self,
        fund_codes: list[str],
        weights: list[float],
        start_date: str,
        end_date: str,
    ) -> dict[str, Any]:
        """分析各地区收益贡献"""
        # 区分QDII和国内基金
        qdii_funds = []
        qdii_weights = []
        domestic_funds = []
        domestic_weights = []
        
        for code, weight in zip(fund_codes, weights):
            try:
                info = self._dm.get_fund_info(code)
                ftype = info.get("type", "") if info else ""
                
                if "QDII" in ftype.upper():
                    qdii_funds.append(code)
                    qdii_weights.append(weight)
                else:
                    domestic_funds.append(code)
                    domestic_weights.append(weight)
            except Exception:
                domestic_funds.append(code)
                domestic_weights.append(weight)
        
        contributions = {}
        
        # 计算QDII部分收益
        if qdii_funds:
            try:
                from fund_cli.analysis.portfolio_nav import PortfolioNavCalculator
                calculator = PortfolioNavCalculator(self._dm)
                
                # 归一化权重
                total_qdii_weight = sum(qdii_weights)
                normalized_qdii_weights = [w / total_qdii_weight for w in qdii_weights]
                
                qdii_nav = calculator.compute_portfolio_nav(
                    qdii_funds, normalized_qdii_weights, start_date, end_date
                )
                qdii_return = qdii_nav.iloc[-1] / qdii_nav.iloc[0] - 1
                
                contributions["海外(QDII)"] = {
                    "权重": round(total_qdii_weight * 100, 2),
                    "收益": round(qdii_return * 100, 2),
                    "贡献": round(qdii_return * total_qdii_weight * 100, 2),
                }
            except Exception:
                contributions["海外(QDII)"] = {"权重": round(sum(qdii_weights) * 100, 2), "收益": "N/A", "贡献": "N/A"}
        
        # 计算国内部分收益
        if domestic_funds:
            try:
                from fund_cli.analysis.portfolio_nav import PortfolioNavCalculator
                calculator = PortfolioNavCalculator(self._dm)
                
                # 归一化权重
                total_domestic_weight = sum(domestic_weights)
                normalized_domestic_weights = [w / total_domestic_weight for w in domestic_weights]
                
                domestic_nav = calculator.compute_portfolio_nav(
                    domestic_funds, normalized_domestic_weights, start_date, end_date
                )
                domestic_return = domestic_nav.iloc[-1] / domestic_nav.iloc[0] - 1
                
                contributions["国内"] = {
                    "权重": round(total_domestic_weight * 100, 2),
                    "收益": round(domestic_return * 100, 2),
                    "贡献": round(domestic_return * total_domestic_weight * 100, 2),
                }
            except Exception:
                contributions["国内"] = {"权重": round(sum(domestic_weights) * 100, 2), "收益": "N/A", "贡献": "N/A"}
        
        return contributions
    
    def _analyze_us_tech_allocation(
        self,
        fund_codes: list[str],
        values: dict[str, float],
    ) -> dict[str, Any]:
        """分析美股科技七巨头配置"""
        from fund_cli.analysis.asset_lookthrough import AssetLookthroughAnalyzer
        lookthrough = AssetLookthroughAnalyzer(self._dm)
        
        # 获取重仓股穿透
        tech_exposure = 0.0
        tech_stocks = []
        
        try:
            top_stocks = lookthrough.stock_lookthrough(fund_codes, values, top_n=20)
            
            for stock in top_stocks:
                name = stock.get("股票名称", "")
                weight = stock.get("合并占比", 0)
                
                # 检查是否为科技七巨头
                is_tech_giant = any(giant.lower() in name.lower() for giant in self.TECH_GIANTS)
                
                if is_tech_giant:
                    tech_exposure += weight
                    tech_stocks.append({
                        "股票": name,
                        "占比": f"{weight:.2%}",
                    })
        except Exception:
            pass
        
        return {
            "科技七巨头合计占比": round(tech_exposure * 100, 2),
            "持仓明细": tech_stocks[:7],  # Top 7
            "评价": "高配" if tech_exposure > 0.15 else "中配" if tech_exposure > 0.08 else "低配",
        }
    
    def _generate_global_evaluation(self, result: dict) -> str:
        """生成全球化配置评价"""
        evaluations = []
        
        # 超额收益评价
        excess = result.get("全球化超额收益", {}).get("超额收益", 0)
        if excess > 5:
            evaluations.append("全球化配置创造了显著超额收益")
        elif excess > 0:
            evaluations.append("全球化配置有一定超额收益")
        elif excess < -5:
            evaluations.append("全球化配置表现落后，需关注海外资产选择")
        
        # 海外占比评价
        overseas_ratio = result.get("海外资产占比", 0)
        if overseas_ratio > 0.5:
            evaluations.append("海外资产配置比例较高，分散化效果较好")
        elif overseas_ratio > 0.3:
            evaluations.append("海外资产配置适中")
        else:
            evaluations.append("海外资产配置较低，可考虑适当增加")
        
        # 科技配置评价
        tech_ratio = result.get("美股科技配置", {}).get("科技七巨头合计占比", 0)
        if tech_ratio > 15:
            evaluations.append(f"美股科技七巨头配置较高（{tech_ratio:.1f}%），需关注估值风险")
        
        return "；".join(evaluations)
    
    def generate_global_report(
        self,
        fund_codes: list[str],
        weights: list[float],
        start_date: str,
        end_date: str,
    ) -> str:
        """
        生成全球化配置报告（Markdown格式）
        
        Args:
            fund_codes: 基金代码列表
            weights: 权重列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            Markdown格式的报告
        """
        result = self.analyze_global_allocation(fund_codes, weights, start_date, end_date)
        
        lines = ["### 全球化配置分析\n"]
        
        # 海外资产占比
        lines.append(f"**海外资产占比**: {result['海外资产占比']:.2%}")
        lines.append(f"**国内资产占比**: {result['国内资产占比']:.2%}")
        lines.append("")
        
        # 全球化超额收益
        lines.append("#### 全球化超额收益\n")
        excess_data = result.get("全球化超额收益", {})
        lines.append(f"- 组合收益: {excess_data.get('组合收益', 'N/A')}%")
        lines.append(f"- MSCI全球指数收益: {excess_data.get('MSCI全球指数收益', 'N/A')}%")
        lines.append(f"- 超额收益: {excess_data.get('超额收益', 'N/A')}% ({excess_data.get('结论', 'N/A')})")
        lines.append("")
        
        # 各地区贡献
        lines.append("#### 各地区贡献\n")
        lines.append("| 地区 | 权重 | 收益 | 贡献 |")
        lines.append("| --- | --- | --- | --- |")
        for region, data in result.get("各地区贡献", {}).items():
            lines.append(
                f"| {region} | {data.get('权重', 'N/A')}% | "
                f"{data.get('收益', 'N/A')}% | {data.get('贡献', 'N/A')}% |"
            )
        lines.append("")
        
        # 美股科技配置
        lines.append("#### 美股科技七巨头配置\n")
        tech_data = result.get("美股科技配置", {})
        lines.append(f"**合计占比**: {tech_data.get('科技七巨头合计占比', 0)}% ({tech_data.get('评价', 'N/A')})")
        
        if tech_data.get("持仓明细"):
            lines.append("\n| 股票 | 占比 |")
            lines.append("| --- | --- |")
            for stock in tech_data["持仓明细"]:
                lines.append(f"| {stock['股票']} | {stock['占比']} |")
        lines.append("")
        
        # 整体评价
        lines.append(f"**整体评价**: {result.get('评价', 'N/A')}")
        
        return "\n".join(lines)

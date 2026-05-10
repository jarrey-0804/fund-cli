"""
基金监控管理器

提供基金池管理和净值监控功能。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class FundMonitor:
    """
    基金监控管理器

    功能：
    - 基金池管理（增删查） (FUND-MONITOR-001)
    - 净值监控和预警 (FUND-MONITOR-002)
    - 数据持久化（JSON文件）
    """

    def __init__(self, config_dir: str = "~/.fund_cli"):
        """
        初始化监控管理器

        Args:
            config_dir: 配置目录
        """
        self._config_dir = Path(config_dir).expanduser()
        self._config_dir.mkdir(parents=True, exist_ok=True)
        self._watchlist_path = self._config_dir / "watchlist.json"
        self._rules_path = self._config_dir / "monitor_rules.json"
        self._pools: dict[str, list[dict]] = {}
        self._rules: list[dict] = []
        self._load()

    def _load(self) -> None:
        """从文件加载数据"""
        if self._watchlist_path.exists():
            try:
                data = json.loads(self._watchlist_path.read_text(encoding="utf-8"))
                self._pools = data.get("pools", {})
            except (json.JSONDecodeError, KeyError):
                self._pools = {}
        else:
            self._pools = {}

        if self._rules_path.exists():
            try:
                self._rules = json.loads(self._rules_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self._rules = []
        else:
            self._rules = []

    def _save(self) -> None:
        """保存数据到文件"""
        self._watchlist_path.write_text(
            json.dumps({"pools": self._pools}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._rules_path.write_text(
            json.dumps(self._rules, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ========== 基金池管理 (FUND-MONITOR-001) ==========

    def add_to_pool(self, fund_code: str, group: str = "default") -> None:
        """
        添加基金到监控池

        Args:
            fund_code: 基金代码
            group: 分组名称
        """
        if group not in self._pools:
            self._pools[group] = []

        existing = [f["code"] for f in self._pools[group]]
        if fund_code not in existing:
            self._pools[group].append(
                {
                    "code": fund_code,
                    "added_at": datetime.now().isoformat(),
                }
            )
            self._save()

    def remove_from_pool(self, fund_code: str, group: str | None = None) -> bool:
        """
        从监控池移除基金

        Args:
            fund_code: 基金代码
            group: 分组名称，None表示从所有分组移除

        Returns:
            是否移除成功
        """
        removed = False
        if group:
            if group in self._pools:
                before = len(self._pools[group])
                self._pools[group] = [f for f in self._pools[group] if f["code"] != fund_code]
                removed = len(self._pools[group]) < before
        else:
            for g in self._pools:
                before = len(self._pools[g])
                self._pools[g] = [f for f in self._pools[g] if f["code"] != fund_code]
                if len(self._pools[g]) < before:
                    removed = True

        if removed:
            self._save()
        return removed

    def list_pool(self, group: str | None = None) -> list[dict]:
        """
        列出监控池中的基金

        Args:
            group: 分组名称，None表示列出所有

        Returns:
            基金列表
        """
        if group:
            return self._pools.get(group, [])
        result = []
        for g, funds in self._pools.items():
            for f in funds:
                result.append({**f, "group": g})
        return result

    def create_pool(self, name: str) -> bool:
        """创建新的基金池分组"""
        if name not in self._pools:
            self._pools[name] = []
            self._save()
            return True
        return False

    def delete_pool(self, name: str) -> bool:
        """删除基金池分组"""
        if name in self._pools and name != "default":
            del self._pools[name]
            self._save()
            return True
        return False

    # ========== 净值监控 (FUND-MONITOR-002) ==========

    # 支持的监控规则类型
    RULE_TYPES: dict[str, dict[str, Any]] = {
        "nav_change": {"name": "日收益率", "unit": "%", "default": -2.0},
        "max_drawdown": {"name": "最大回撤", "unit": "%", "default": -10.0},
        "volatility": {"name": "波动率", "unit": "%", "default": 30.0},
        "sharpe_ratio": {"name": "夏普比率", "unit": "", "default": 0.5},
    }

    def add_rule(
        self, fund_code: str, rule_type: str = "nav_change", threshold: float | None = None
    ) -> bool:
        """
        添加监控规则

        Args:
            fund_code: 基金代码
            rule_type: 规则类型 (nav_change/max_drawdown/volatility/sharpe_ratio)
            threshold: 预警阈值，None 使用默认值

        Returns:
            是否添加成功
        """
        if rule_type not in self.RULE_TYPES:
            return False

        # 使用默认值
        actual_threshold: float
        if threshold is None:
            default_val = self.RULE_TYPES[rule_type]["default"]
            actual_threshold = float(default_val) if default_val is not None else 0.0
        else:
            actual_threshold = threshold

        self._rules.append(
            {
                "fund_code": fund_code,
                "rule_type": rule_type,
                "threshold": actual_threshold,
                "enabled": True,
                "created_at": datetime.now().isoformat(),
            }
        )
        self._save()
        return True

    def get_rules(self, fund_code: str | None = None) -> list[dict]:
        """获取监控规则"""
        if fund_code:
            return [
                r for r in self._rules if r["fund_code"] == fund_code and r.get("enabled", True)
            ]
        return [r for r in self._rules if r.get("enabled", True)]

    def check_nav_changes(self, fund_codes: list[str], threshold: float = -2.0) -> list[dict]:
        """
        检查净值变动

        Args:
            fund_codes: 基金代码列表
            threshold: 预警阈值（默认-2%）

        Returns:
            触发预警的基金列表
        """
        alerts = []
        try:
            from fund_cli.core.data_manager import DataManager

            dm = DataManager()
            for code in fund_codes:
                try:
                    nav_df = dm.get_fund_nav(code)
                    if nav_df.empty or "daily_return" not in nav_df.columns:
                        continue
                    latest = nav_df.iloc[-1]["daily_return"]
                    if isinstance(latest, str):
                        latest = float(latest.replace("%", ""))
                    if latest <= threshold:
                        alerts.append(
                            {
                                "fund_code": code,
                                "daily_return": latest,
                                "threshold": threshold,
                                "alert_type": "nav_change",
                            }
                        )
                except Exception as e:
                    # 记录错误但不中断其他基金检查
                    import logging

                    logging.getLogger(__name__).debug(f"检查基金 {code} 净值失败: {e}")
                    continue
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"净值检查初始化失败: {e}")
        return alerts

    def check_rules(self, fund_code: str | None = None) -> list[dict]:
        """
        检查所有监控规则

        Args:
            fund_code: 指定基金代码，None 检查所有规则

        Returns:
            触发预警的列表
        """
        alerts: list[dict] = []
        rules = self.get_rules(fund_code)

        if not rules:
            return alerts

        try:
            from fund_cli.analysis.performance import PerformanceAnalyzer
            from fund_cli.analysis.risk import RiskAnalyzer
            from fund_cli.core.data_manager import DataManager

            dm = DataManager()
            perf_analyzer = PerformanceAnalyzer()
            risk_analyzer = RiskAnalyzer()

            # 按基金分组规则
            fund_rules: dict[str, list[dict]] = {}
            for rule in rules:
                code = rule["fund_code"]
                if code not in fund_rules:
                    fund_rules[code] = []
                fund_rules[code].append(rule)

            # 检查每个基金的规则
            for code, rule_list in fund_rules.items():
                try:
                    nav_df = dm.get_fund_nav(code)
                    if nav_df.empty or "daily_return" not in nav_df.columns:
                        continue

                    returns = nav_df["daily_return"].dropna() / 100
                    if len(returns) < 30:
                        continue

                    # 计算指标
                    perf_metrics = perf_analyzer.analyze(returns)
                    risk_metrics = risk_analyzer.analyze(returns)

                    # 检查每条规则
                    for rule in rule_list:
                        rule_type = rule["rule_type"]
                        threshold = rule["threshold"]

                        if rule_type == "nav_change":
                            latest = returns.iloc[-1] * 100
                            if latest <= threshold:
                                alerts.append(
                                    {
                                        "fund_code": code,
                                        "rule_type": rule_type,
                                        "current_value": latest,
                                        "threshold": threshold,
                                        "alert_type": rule_type,
                                    }
                                )

                        elif rule_type == "max_drawdown":
                            mdd = risk_metrics.get("max_drawdown", 0) * 100
                            if mdd <= threshold:
                                alerts.append(
                                    {
                                        "fund_code": code,
                                        "rule_type": rule_type,
                                        "current_value": mdd,
                                        "threshold": threshold,
                                        "alert_type": rule_type,
                                    }
                                )

                        elif rule_type == "volatility":
                            vol = (
                                risk_metrics.get(
                                    "volatility_annual", perf_metrics.get("volatility", 0)
                                )
                                * 100
                            )
                            if vol >= threshold:
                                alerts.append(
                                    {
                                        "fund_code": code,
                                        "rule_type": rule_type,
                                        "current_value": vol,
                                        "threshold": threshold,
                                        "alert_type": rule_type,
                                    }
                                )

                        elif rule_type == "sharpe_ratio":
                            sharpe = perf_metrics.get("sharpe", 0)
                            if sharpe <= threshold:
                                alerts.append(
                                    {
                                        "fund_code": code,
                                        "rule_type": rule_type,
                                        "current_value": sharpe,
                                        "threshold": threshold,
                                        "alert_type": rule_type,
                                    }
                                )

                except Exception as e:
                    import logging

                    logging.getLogger(__name__).debug(f"检查基金 {code} 规则失败: {e}")
                    continue

        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(f"规则检查初始化失败: {e}")

        return alerts

    def get_all_fund_codes(self) -> list[str]:
        """获取所有监控基金代码"""
        codes = set()
        for funds in self._pools.values():
            for f in funds:
                codes.add(f["code"])
        return sorted(codes)

    def get_pool_names(self) -> list[str]:
        """获取所有基金池名称"""
        return list(self._pools.keys())

    def __repr__(self) -> str:
        total = sum(len(funds) for funds in self._pools.values())
        return f"FundMonitor(pools={len(self._pools)}, funds={total})"

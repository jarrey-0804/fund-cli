"""
基金监控管理器

提供基金池管理和净值监控功能。
"""

import json
from datetime import datetime
from pathlib import Path


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

    def add_rule(
        self, fund_code: str, rule_type: str = "nav_change", threshold: float = -2.0
    ) -> None:
        """添加监控规则"""
        self._rules.append(
            {
                "fund_code": fund_code,
                "rule_type": rule_type,
                "threshold": threshold,
                "enabled": True,
                "created_at": datetime.now().isoformat(),
            }
        )
        self._save()

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
                except Exception:
                    continue
        except Exception:
            pass
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

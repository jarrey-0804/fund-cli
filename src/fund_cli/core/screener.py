"""基金筛选引擎"""

import json
import re
from pathlib import Path

import pandas as pd

from fund_cli.data.models import FundFilter


class FundScreener:
    """
    基金筛选引擎

    功能：
    - 费率筛选 (FUND-FILTER-005)
    - 经理筛选 (FUND-FILTER-006)
    - 评级筛选 (FUND-FILTER-007)
    - 高级表达式筛选 (FUND-FILTER-012)
    - 模板保存/加载 (FUND-FILTER-011)
    """

    # 允许的表达式函数白名单
    _SAFE_FUNCTIONS = {"sum", "mean", "min", "max", "abs", "len"}

    def __init__(self, data_manager=None):
        from fund_cli.core.data_manager import DataManager

        self._dm = data_manager or DataManager()
        self._template_dir = Path("~/.fund_cli/templates").expanduser()
        self._template_dir.mkdir(parents=True, exist_ok=True)

    def screen(self, filter_obj: FundFilter) -> pd.DataFrame:
        """执行通用筛选"""
        df = self._dm.search_funds(
            fund_type=filter_obj.fund_type.value if filter_obj.fund_type else None,
            company=filter_obj.company,
            min_scale=filter_obj.min_scale,
            max_scale=filter_obj.max_scale,
            keyword=filter_obj.keyword,
            limit=filter_obj.limit,
        )

        if df.empty:
            return df

        # 业绩筛选
        if filter_obj.min_return_1y is not None and "return_1y" in df.columns:
            df = df[df["return_1y"] >= filter_obj.min_return_1y]
        if filter_obj.max_return_1y is not None and "return_1y" in df.columns:
            df = df[df["return_1y"] <= filter_obj.max_return_1y]

        # 风险筛选
        if filter_obj.max_drawdown is not None and "max_drawdown" in df.columns:
            df = df[df["max_drawdown"] >= filter_obj.max_drawdown]
        if filter_obj.min_sharpe is not None and "sharpe_ratio" in df.columns:
            df = df[df["sharpe_ratio"] >= filter_obj.min_sharpe]

        # V1.0 新增筛选
        if filter_obj.fee_rate_max is not None and "fee_rate" in df.columns:
            df = df[df["fee_rate"] <= filter_obj.fee_rate_max]
        if filter_obj.manager_name and "manager" in df.columns:
            df = df[df["manager"].str.contains(filter_obj.manager_name, na=False)]
        if filter_obj.min_rating is not None and "rating" in df.columns:
            df = df[df["rating"] >= filter_obj.min_rating]

        # 排序
        if filter_obj.sort_by and filter_obj.sort_by in df.columns:
            ascending = filter_obj.sort_order == "asc"
            df = df.sort_values(filter_obj.sort_by, ascending=ascending)

        return df.reset_index(drop=True)

    def screen_by_fee(self, max_fee_rate: float, fund_type: str | None = None) -> pd.DataFrame:
        """费率筛选 (FUND-FILTER-005)"""
        f = FundFilter(fee_rate_max=max_fee_rate)
        if fund_type:
            from fund_cli.data.models import FundType

            f.fund_type = FundType(fund_type)
        return self.screen(f)

    def screen_by_manager(self, manager_name: str) -> pd.DataFrame:
        """经理筛选 (FUND-FILTER-006)"""
        f = FundFilter(manager_name=manager_name)
        return self.screen(f)

    def screen_by_rating(self, min_rating: int) -> pd.DataFrame:
        """评级筛选 (FUND-FILTER-007)"""
        f = FundFilter(min_rating=min_rating)
        return self.screen(f)

    def evaluate_expression(self, df: pd.DataFrame, expression: str) -> pd.DataFrame:
        """
        高级表达式筛选 (FUND-FILTER-012)

        使用 pandas query 安全执行表达式。
        支持的运算符: >, <, =, >=, <=, ==, !=
        支持的逻辑: AND, OR, and, or, &, |
        """
        try:
            # 安全检查：禁止危险操作
            dangerous = re.findall(
                r"(?:__|import|exec|eval|open|os\.|sys\.)", expression, re.IGNORECASE
            )
            if dangerous:
                raise ValueError(f"表达式包含不允许的操作: {dangerous}")

            result = df.query(expression)
            return result.reset_index(drop=True)
        except Exception as e:
            raise ValueError(f"表达式解析失败: {e}") from e

    def save_template(self, name: str, filter_obj: FundFilter) -> None:
        """保存筛选模板 (FUND-FILTER-011)"""
        path = self._template_dir / f"{name}.json"
        data = filter_obj.model_dump(mode="json")
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_template(self, name: str) -> FundFilter:
        """加载筛选模板"""
        path = self._template_dir / f"{name}.json"
        if not path.exists():
            raise FileNotFoundError(f"模板 {name} 不存在")
        data = json.loads(path.read_text(encoding="utf-8"))
        return FundFilter(**data)

    def list_templates(self) -> list[str]:
        """列出所有筛选模板"""
        templates = []
        for f in self._template_dir.glob("*.json"):
            templates.append(f.stem)
        return sorted(templates)

    def delete_template(self, name: str) -> bool:
        """删除筛选模板"""
        path = self._template_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

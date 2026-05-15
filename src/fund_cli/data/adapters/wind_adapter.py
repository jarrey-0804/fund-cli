"""
Wind 数据源适配器（占位实现）.

⚠️ DEPRECATED: 此模块为占位实现，尚未完成 Wind 终端集成。
如需使用 Wind 数据，请使用其他数据源（AKShare、Qieman MCP）。

未来计划:
- 集成 WindPy SDK
- 支持 Wind 专业数据接口
- 需要 Wind 终端授权

@deprecated: 当前版本仅为 API 占位，不建议在生产环境使用
"""

import warnings
from typing import Any

from fund_cli.data.adapters.mixins import DataSourceAdapterMixin
from fund_cli.data.base import DataSourceAdapter


class WindAdapter(DataSourceAdapterMixin, DataSourceAdapter):
    """
    Wind 数据源适配器（占位实现）.

    Wind（万得）是中国领先的金融数据提供商，特点：
    - 数据覆盖最全面
    - 需要商业授权
    - 通过 WindPy Python 接口访问

    当前为占位实现，待 WindPy 授权后完善。
    """

    def __init__(self, cache=None, **kwargs: Any):
        super().__init__("wind")
        self._cache = cache
        self._api = None
        warnings.warn(
            "WindAdapter 为占位实现，尚未完成 Wind 终端集成。"
            "请使用 AKShare 或 Qieman MCP 数据源。",
            DeprecationWarning,
            stacklevel=2,
        )

    def is_available(self) -> bool:
        """检查 Wind 是否可用."""
        return False

    def _ensure_api(self):
        """确保 Wind API 已连接."""
        raise NotImplementedError(
            "Wind API 尚未集成。如需使用 Wind 数据，请等待后续版本或联系开发者。"
        )

    # P0 核心方法 - 覆盖 Mixin 的占位实现
    def get_fund_info(self, fund_code: str) -> dict:
        self._ensure_api()

    def get_all_fund_names(self):
        self._ensure_api()

    def get_fund_nav(self, fund_code: str, start_date=None, end_date=None):
        self._ensure_api()

    def get_etf_spot(self):
        self._ensure_api()

    def get_lof_spot(self):
        self._ensure_api()

    def get_fund_manager(self, fund_code: str):
        self._ensure_api()

    def get_fund_holdings(self, fund_code: str, report_date=None):
        self._ensure_api()

    def get_fund_asset_allocation(self, fund_code: str, date=None):
        self._ensure_api()

    def get_fund_rating(self, fund_code: str):
        self._ensure_api()

    def get_fund_fee(self, fund_code: str):
        self._ensure_api()

    def batch_get_fund_nav(self, fund_codes, start_date=None, end_date=None):
        self._ensure_api()

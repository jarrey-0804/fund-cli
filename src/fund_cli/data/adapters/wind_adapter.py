"""
Wind 数据源适配器（占位实现）.

Wind（万得）是中国领先的金融数据提供商，特点：
- 数据覆盖最全面
- 需要商业授权
- 通过 WindPy Python 接口访问

当前为占位实现，待 WindPy 授权后完善。
"""

from fund_cli.data.adapters.mixins import DataSourceAdapterMixin
from fund_cli.data.base import DataSourceAdapter, DataSourceError


class WindAdapter(DataSourceAdapterMixin, DataSourceAdapter):
    """
    Wind 数据源适配器（占位实现）.

    Wind（万得）是中国领先的金融数据提供商，特点：
    - 数据覆盖最全面
    - 需要商业授权
    - 通过 WindPy Python 接口访问

    当前为占位实现，待 WindPy 授权后完善。
    """

    def __init__(self, cache=None):
        super().__init__("wind")
        self._cache = cache
        self._api = None

    def is_available(self) -> bool:
        """检查 Wind 是否可用."""
        try:
            from WindPy import w
            return w.isconnected()
        except ImportError:
            return False
        except Exception:
            return False

    def _ensure_api(self):
        """确保 Wind API 已连接."""
        if self._api is None:
            try:
                from WindPy import w
                w.start()
                self._api = w
            except ImportError as exc:
                raise DataSourceError("WindPy 未安装。请安装 WindPy 并确保已授权。") from exc
            except Exception as e:
                raise DataSourceError(f"Wind 连接失败: {e}") from e

    # P0 核心方法 - 覆盖 Mixin 的占位实现
    def get_fund_info(self, fund_code: str) -> dict:
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_all_fund_names(self):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_fund_nav(self, fund_code: str, start_date=None, end_date=None):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_etf_spot(self):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_lof_spot(self):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_fund_manager(self, fund_code: str):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_fund_holdings(self, fund_code: str, report_date=None):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_fund_asset_allocation(self, fund_code: str, date=None):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_fund_rating(self, fund_code: str):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def get_fund_fee(self, fund_code: str):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

    def batch_get_fund_nav(self, fund_codes, start_date=None, end_date=None):
        self._ensure_api()
        raise DataSourceError("WindAdapter P0 方法待实现（需要 WindPy 授权）")

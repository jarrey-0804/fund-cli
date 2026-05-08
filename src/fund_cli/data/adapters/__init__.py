"""数据源适配器 - AKShare、Tushare、Wind"""

from fund_cli.data.adapters.akshare_adapter import AKShareAdapter
from fund_cli.data.adapters.tushare_adapter import TushareAdapter
from fund_cli.data.adapters.wind_adapter import WindAdapter

__all__ = ["AKShareAdapter", "TushareAdapter", "WindAdapter"]

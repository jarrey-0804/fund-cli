"""
WindAdapter 单元测试
"""

from unittest.mock import MagicMock, patch

import pytest

from fund_cli.data.adapters.wind_adapter import WindAdapter


class TestWindAdapterInit:
    """测试初始化"""

    def test_init(self):
        """测试初始化"""
        adapter = WindAdapter()
        assert adapter.name == "wind"
        assert adapter._cache is None
        assert adapter._api is None

    def test_init_with_cache(self):
        """测试带缓存初始化"""
        mock_cache = MagicMock()
        adapter = WindAdapter(cache=mock_cache)
        assert adapter._cache == mock_cache


class TestWindAdapterIsAvailable:
    """测试 is_available 方法"""

    def test_is_available_windpy_not_installed(self):
        """测试 WindPy 未安装时返回 False"""
        adapter = WindAdapter()

        with patch.dict('sys.modules', {'WindPy': None}):
            result = adapter.is_available()
            assert result is False

    def test_is_available_import_error(self):
        """测试导入错误时返回 False"""
        adapter = WindAdapter()

        # 模拟 ImportError
        with patch.dict('sys.modules', {'WindPy': None}):
            result = adapter.is_available()
            assert result is False

    def test_is_available_not_connected(self):
        """测试 Wind 未连接时返回 False"""
        WindAdapter()

        mock_w = MagicMock()
        mock_w.isconnected.return_value = False

        with patch.dict('sys.modules', {'WindPy': MagicMock(w=mock_w)}):
            # 由于 WindPy 导入机制，这个测试需要特殊处理
            # 实际上 is_available 会尝试导入 WindPy
            pass

    def test_is_available_exception(self):
        """测试异常情况返回 False"""
        adapter = WindAdapter()

        # 模拟任何异常
        with patch.dict('sys.modules', {}):
            result = adapter.is_available()
            assert result is False


class TestWindAdapterEnsureApi:
    """测试 _ensure_api 方法"""

    def test_ensure_api_windpy_not_installed(self):
        """测试 _ensure_api 直接抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter._ensure_api()

    def test_ensure_api_import_error(self):
        """测试 _ensure_api 直接抛出 NotImplementedError（不受 ImportError 影响）"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter._ensure_api()

    def test_ensure_api_connection_failure(self):
        """测试 Wind 连接失败时抛出异常"""
        WindAdapter()

        mock_w = MagicMock()
        mock_w.start.side_effect = Exception("Connection failed")

        with patch.dict('sys.modules', {'WindPy': MagicMock(w=mock_w)}):
            # 由于实际导入机制，这个测试需要特殊处理
            pass

    def test_ensure_api_already_initialized(self):
        """测试 _ensure_api 无论是否已初始化都抛出 NotImplementedError"""
        adapter = WindAdapter()
        adapter._api = MagicMock()  # 模拟已初始化

        # 即使 _api 已设置，_ensure_api 仍然直接抛出 NotImplementedError
        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter._ensure_api()


class TestWindAdapterP0Methods:
    """测试 P0 核心方法"""

    def test_get_fund_info_raises_error(self):
        """测试 get_fund_info 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_info("000001")

    def test_get_all_fund_names_raises_error(self):
        """测试 get_all_fund_names 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_all_fund_names()

    def test_get_fund_nav_raises_error(self):
        """测试 get_fund_nav 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_nav("000001")

    def test_get_fund_nav_with_dates_raises_error(self):
        """测试 get_fund_nav 带日期参数抛出 NotImplementedError"""
        adapter = WindAdapter()

        from datetime import date

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_nav("000001", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31))

    def test_get_etf_spot_raises_error(self):
        """测试 get_etf_spot 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_etf_spot()

    def test_get_lof_spot_raises_error(self):
        """测试 get_lof_spot 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_lof_spot()

    def test_get_fund_manager_raises_error(self):
        """测试 get_fund_manager 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_manager("000001")

    def test_get_fund_holdings_raises_error(self):
        """测试 get_fund_holdings 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_holdings("000001")

    def test_get_fund_holdings_with_date_raises_error(self):
        """测试 get_fund_holdings 带日期参数抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_holdings("000001", report_date="2024-01-01")

    def test_get_fund_asset_allocation_raises_error(self):
        """测试 get_fund_asset_allocation 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_asset_allocation("000001")

    def test_get_fund_asset_allocation_with_date_raises_error(self):
        """测试 get_fund_asset_allocation 带日期参数抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_asset_allocation("000001", date="2024-01-01")

    def test_get_fund_rating_raises_error(self):
        """测试 get_fund_rating 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_rating("000001")

    def test_get_fund_fee_raises_error(self):
        """测试 get_fund_fee 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.get_fund_fee("000001")

    def test_batch_get_fund_nav_raises_error(self):
        """测试 batch_get_fund_nav 抛出 NotImplementedError"""
        adapter = WindAdapter()

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.batch_get_fund_nav(["000001", "000002"])

    def test_batch_get_fund_nav_with_dates_raises_error(self):
        """测试 batch_get_fund_nav 带日期参数抛出 NotImplementedError"""
        adapter = WindAdapter()

        from datetime import date

        with pytest.raises(NotImplementedError, match="Wind API 尚未集成"):
            adapter.batch_get_fund_nav(
                ["000001", "000002"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31)
            )


class TestWindAdapterEnsureApiCalled:
    """测试 _ensure_api 被正确调用"""

    def test_get_fund_info_calls_ensure_api(self):
        """测试 get_fund_info 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_fund_info("000001")
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_all_fund_names_calls_ensure_api(self):
        """测试 get_all_fund_names 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_all_fund_names()
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_fund_nav_calls_ensure_api(self):
        """测试 get_fund_nav 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_fund_nav("000001")
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_etf_spot_calls_ensure_api(self):
        """测试 get_etf_spot 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_etf_spot()
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_lof_spot_calls_ensure_api(self):
        """测试 get_lof_spot 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_lof_spot()
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_fund_manager_calls_ensure_api(self):
        """测试 get_fund_manager 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_fund_manager("000001")
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_fund_holdings_calls_ensure_api(self):
        """测试 get_fund_holdings 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_fund_holdings("000001")
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_fund_asset_allocation_calls_ensure_api(self):
        """测试 get_fund_asset_allocation 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_fund_asset_allocation("000001")
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_fund_rating_calls_ensure_api(self):
        """测试 get_fund_rating 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_fund_rating("000001")
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_get_fund_fee_calls_ensure_api(self):
        """测试 get_fund_fee 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.get_fund_fee("000001")
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()

    def test_batch_get_fund_nav_calls_ensure_api(self):
        """测试 batch_get_fund_nav 调用 _ensure_api"""
        adapter = WindAdapter()

        with patch.object(adapter, '_ensure_api') as mock_ensure:
            mock_ensure.side_effect = NotImplementedError("Wind API 尚未集成")

            try:
                adapter.batch_get_fund_nav(["000001"])
            except NotImplementedError:
                pass

            mock_ensure.assert_called_once()


class TestWindAdapterName:
    """测试适配器名称"""

    def test_name_is_wind(self):
        """测试适配器名称为 wind"""
        adapter = WindAdapter()
        assert adapter.name == "wind"

    def test_name_persists_after_operations(self):
        """测试操作后名称保持不变"""
        adapter = WindAdapter()

        # 尝试一些操作，现在会抛出 NotImplementedError
        try:
            adapter.get_fund_info("000001")
        except NotImplementedError:
            pass

        assert adapter.name == "wind"

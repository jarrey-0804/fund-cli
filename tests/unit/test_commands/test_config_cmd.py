"""配置命令测试"""

from typer.testing import CliRunner

from fund_cli.commands.config_cmd import app

runner = CliRunner()


class TestConfigCommands:
    def test_show_help(self):
        result = runner.invoke(app, ["show", "--help"])
        assert result.exit_code == 0

    def test_output_help(self):
        result = runner.invoke(app, ["output", "--help"])
        assert result.exit_code == 0

    def test_set_help(self):
        result = runner.invoke(app, ["set", "--help"])
        assert result.exit_code == 0

    def test_output_defaults(self):
        result = runner.invoke(app, ["output"])
        assert result.exit_code == 0
        assert "默认格式" in result.output

    def test_set_config_unknown_key(self):
        """未知配置键应返回错误"""
        result = runner.invoke(app, ["set", "unknown_key", "test_value"])
        assert result.exit_code == 1
        assert "未知配置键" in result.output

    def test_set_config_valid_key(self):
        """有效配置键应持久化成功"""
        result = runner.invoke(app, ["set", "debug", "true"])
        assert result.exit_code == 0
        assert "已持久化" in result.output

    def test_set_config_no_persist(self):
        """--no-persist 选项应仅设置当前会话"""
        result = runner.invoke(app, ["set", "debug", "true", "--no-persist"])
        assert result.exit_code == 0
        assert "当前会话" in result.output

    def test_list_keys(self):
        """list-keys 命令应显示所有可配置项"""
        result = runner.invoke(app, ["list-keys"])
        assert result.exit_code == 0
        assert "ai.provider" in result.output

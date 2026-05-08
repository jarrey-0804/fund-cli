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

    def test_set_config(self):
        result = runner.invoke(app, ["set", "test_key", "test_value"])
        assert result.exit_code == 0

"""对比命令测试"""

from typer.testing import CliRunner

from fund_cli.commands.compare_cmd import app

runner = CliRunner()


class TestCompareCommands:
    def test_funds_help(self):
        result = runner.invoke(app, ["funds", "--help"])
        assert result.exit_code == 0

    def test_rolling_win_help(self):
        result = runner.invoke(app, ["rolling-win", "--help"])
        assert result.exit_code == 0

    def test_correlation_help(self):
        result = runner.invoke(app, ["correlation", "--help"])
        assert result.exit_code == 0

    def test_report_help(self):
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0

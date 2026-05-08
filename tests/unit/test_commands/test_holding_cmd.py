"""持仓命令测试"""

from typer.testing import CliRunner

from fund_cli.commands.holding_cmd import app

runner = CliRunner()


class TestHoldingCommands:
    def test_query_help(self):
        result = runner.invoke(app, ["query", "--help"])
        assert result.exit_code == 0
        assert "持仓" in result.output

    def test_industry_help(self):
        result = runner.invoke(app, ["industry", "--help"])
        assert result.exit_code == 0

    def test_concentration_help(self):
        result = runner.invoke(app, ["concentration", "--help"])
        assert result.exit_code == 0

    def test_changes_help(self):
        result = runner.invoke(app, ["changes", "--help"])
        assert result.exit_code == 0

    def test_style_help(self):
        result = runner.invoke(app, ["style", "--help"])
        assert result.exit_code == 0

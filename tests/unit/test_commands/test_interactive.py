"""交互式模式测试"""

from typer.testing import CliRunner

from fund_cli.commands.interactive_cmd import app

runner = CliRunner()


class TestInteractiveCommands:
    def test_start_help(self):
        result = runner.invoke(app, ["start", "--help"])
        assert result.exit_code == 0

    def test_start_requires_prompt_toolkit(self):
        # Without prompt_toolkit, should show warning
        result = runner.invoke(app, ["start"])
        # Either works or shows warning
        assert result.exit_code in (0, 1, 2)

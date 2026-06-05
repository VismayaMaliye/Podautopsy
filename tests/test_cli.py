from click.testing import CliRunner
from podautopsy.cli import main

def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert 'analyze' in result.output
    assert 'scan' in result.output

def test_analyze_missing_args():
    runner = CliRunner()
    result = runner.invoke(main, ['analyze'])
    assert result.exit_code != 0
    assert 'namespace' in result.output.lower() or 'missing' in result.output.lower()

def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ['--version'])
    assert result.exit_code == 0
    assert '1.0.0' in result.output
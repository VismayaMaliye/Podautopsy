"""CLI integration tests using Click test runner."""
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from podautopsy.cli import main
from podautopsy.models import PostMortemReport, ContainerState, FailureType
 
 
def make_mock_report():
    r = PostMortemReport(pod_name='test-pod', namespace='prod', node_name='node-1')
    r.failure_type = FailureType.OOM_KILLED
    r.failure_summary = 'Container was OOMKilled'
    r.suggested_fix = 'Increase memory limit'
    r.containers = [ContainerState('app', False, 3, 'terminated', 'OOMKilled', 137)]
    return r
 
 
@patch('podautopsy.cli.get_k8s_clients')
@patch('podautopsy.cli.fetch_pod_data')
@patch('podautopsy.cli.fetch_pod_events', return_value=[])
@patch('podautopsy.cli.fetch_pod_logs', return_value=([], []))
@patch('podautopsy.cli.fetch_node_conditions', return_value=[])
@patch('podautopsy.cli.fetch_resource_usage')
@patch('podautopsy.cli.detect_failure')
@patch('podautopsy.cli.print_report')
def test_analyze_command(mock_print, mock_detect, mock_resources,
                         mock_node, mock_logs, mock_events, mock_pod, mock_k8s):
    mock_k8s.return_value = (MagicMock(), MagicMock())
    mock_pod.return_value = make_mock_report()
    mock_resources.return_value = MagicMock()
 
    runner = CliRunner()
    result = runner.invoke(main, ['analyze', '-n', 'prod', '-p', 'test-pod'])
    assert result.exit_code == 0
    mock_print.assert_called_once()
 
 
def test_missing_required_args():
    runner = CliRunner()
    result = runner.invoke(main, ['analyze'])
    assert result.exit_code != 0
    assert 'Missing option' in result.output
 
 
def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ['--version'])
    assert '1.0.0' in result.output
 

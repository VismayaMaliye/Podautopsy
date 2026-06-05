"""PodAutopsy CLI -entry point for all commands."""
import click
from rich.console import Console
 
console = Console()
 
 
@click.group()
@click.version_option(version='1.0.0')
def main():
    """PodAutopsy -Automated Kubernetes Incident Post-Mortem Generator."""
    pass
 
 
@main.command()
@click.option('--namespace', '-n', required=True, help='Kubernetes namespace')
@click.option('--pod', '-p', required=True, help='Pod name')
@click.option('--output', '-o', type=click.Choice(['terminal', 'markdown', 'html']),
              default='terminal', help='Output format')
@click.option('--ai', is_flag=True, default=False, help='Enable AI root cause analysis via AWS Bedrock')
@click.option('--log-lines', default=200, show_default=True, help='Number of log lines to fetch')
def analyze(namespace, pod, output, ai, log_lines):
    """Analyze a specific pod and generate an incident post-mortem report."""
    from podautopsy.k8s.client import get_k8s_clients
    from podautopsy.k8s.pod import fetch_pod_data
    from podautopsy.k8s.events import fetch_pod_events
    from podautopsy.k8s.logs import fetch_pod_logs
    from podautopsy.k8s.node import fetch_node_conditions
    from podautopsy.k8s.metrics import fetch_resource_usage
    from podautopsy.analyzer.failure import detect_failure
    from podautopsy.analyzer.ai import analyze_with_ai
    from podautopsy.report.terminal import print_report
    from podautopsy.report.markdown import save_markdown
    from podautopsy.report.html import save_html
 
    with console.status(f'[bold red]Collecting pod data for {pod}...[/]'):
        core_v1, _ = get_k8s_clients()
        report = fetch_pod_data(core_v1, namespace, pod)
        report.events = fetch_pod_events(core_v1, namespace, pod)
        report.logs, report.previous_logs = fetch_pod_logs(core_v1, namespace, pod, log_lines)
        if report.node_name:
            report.node_conditions = fetch_node_conditions(core_v1, report.node_name)
        report.resources = fetch_resource_usage(namespace, pod)
        detect_failure(report)
 
    if ai:
        with console.status('[bold purple]Asking Claude for root cause analysis...[/]'):
            analyze_with_ai(report)
    if output == 'terminal':
        print_report(report)
    elif output == 'markdown':
        path = save_markdown(report)
        console.print(f'[green]Report saved:[/] {path}')
    elif output == 'html':
        path = save_html(report)
        console.print(f'[green]Report saved:[/] {path}')
 
 
@main.command(name='scan')
@click.option('--namespace', '-n', required=True, help='Kubernetes namespace')
@click.option('--ai', is_flag=True, default=False)
def scan_namespace(namespace, ai):
    """Scan all failed/crashing pods in a namespace."""
    from podautopsy.k8s.client import get_k8s_clients
    from podautopsy.k8s.pod import list_failed_pods
    from podautopsy.report.terminal import print_scan_summary
 
    core_v1, _ = get_k8s_clients()
    failed = list_failed_pods(core_v1, namespace)
 
    if not failed:
        console.print(f'[green]✓ No failed pods in namespace {namespace!r}[/]')
        return
 
    console.print(f'[red]Found {len(failed)} failed pod(s) in {namespace!r}[/]')
    print_scan_summary(failed)

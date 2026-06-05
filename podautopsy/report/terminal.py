"""Rich terminal report renderer."""
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.rule import Rule
from rich.text import Text
from rich import box
from podautopsy.models import PostMortemReport, FailureType
from podautopsy.analyzer.timeline import build_timeline
console = Console()
 
FAILURE_COLORS = {
    FailureType.OOM_KILLED:  'red',
    FailureType.CRASH_LOOP:  'yellow',
    FailureType.EVICTED:     'magenta',
    FailureType.IMAGE_PULL:  'orange1',
    FailureType.PENDING:     'blue',
    FailureType.COMPLETED:   'green',
    FailureType.UNKNOWN:     'grey50',
}
FAILURE_ICONS = {
    FailureType.OOM_KILLED:  '💀',
    FailureType.CRASH_LOOP:  '🔄',
    FailureType.EVICTED:     '⚡',
    FailureType.IMAGE_PULL:  '🐳',
    FailureType.PENDING:     '⏳',
    FailureType.COMPLETED:   '✅',
    FailureType.UNKNOWN:     '❓',
}
 
 
def print_report(report: PostMortemReport) -> None:
    color = FAILURE_COLORS.get(report.failure_type, 'white')
    icon  = FAILURE_ICONS.get(report.failure_type, '?')
 
    # ── Header ────────────────────────────────────────────────
    console.print()
    console.print(Rule('[bold red]PodAutopsy — Incident Report[/]', style='red'))
    console.print()
 
    # ── Failure Banner ────────────────────────────────────────
    banner = Text()
    banner.append(f'{icon}  FAILURE TYPE: ', style='bold white')
    banner.append(report.failure_type.value, style=f'bold {color}')
    console.print(Panel(banner, border_style=color, padding=(0, 2)))
    console.print()
 
    # ── Identity ──────────────────────────────────────────────
    id_table = Table(box=box.SIMPLE, show_header=False, padding=(0,1))
    id_table.add_column('Key', style='bold dim', width=18)
    id_table.add_column('Value', style='white')
    id_table.add_row('Pod', report.pod_name)
    id_table.add_row('Namespace', report.namespace)
    id_table.add_row('Node', report.node_name or 'N/A')
    id_table.add_row('Analyzed At', report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC'))
    console.print(Panel(id_table, title='[bold]Pod Identity[/]', border_style='dim'))
    console.print()
 
    # ── Failure Summary ───────────────────────────────────────
    console.print(Panel(
        f'[bold]{color}]{report.failure_summary}[/]\n\n[dim]{report.suggested_fix}[/]',
        title=f'[bold {color}]Root Cause & Suggested Fix[/]',
        border_style=color, padding=(1, 2)
    ))
    console.print()
 
    # ── Containers ────────────────────────────────────────────
    if report.containers:
        ct = Table(title='Container States', box=box.ROUNDED, border_style='dim',
                   show_lines=True)
        ct.add_column('Container', style='bold cyan')
        ct.add_column('State')
        ct.add_column('Reason')
        ct.add_column('Exit Code')
        ct.add_column('Restarts', justify='right')
        ct.add_column('Ready')
        for c in report.containers:
            state_color = 'green' if c.state == 'running' else ('red' if c.state == 'terminated' else 'yellow')
            ready_str = '[green]✓[/]' if c.ready else '[red]✗[/]'
            ct.add_row(
                c.name,
                f'[{state_color}]{c.state}[/]',
                c.reason or '-',
                str(c.exit_code) if c.exit_code is not None else '-',
                f'[red]{c.restart_count}[/]' if c.restart_count > 2 else str(c.restart_count),
                ready_str,
            )
        console.print(ct)
        console.print()
 
    # ── Node Conditions ───────────────────────────────────────
    pressure = [c for c in report.node_conditions if c.status == 'True'
                and c.type != 'Ready']
    if pressure:
        console.print(Panel(
            '\n'.join(f'[red]⚠  {c.type}[/]: {c.message}' for c in pressure),
            title='[bold red]⚠  Node Under Pressure[/]', border_style='red'
        ))
        console.print()
 
    # ── Resource Usage ────────────────────────────────────────
    if report.resources and (report.resources.cpu_cores or report.resources.memory_bytes):
        r = report.resources
        mem_mb = round(r.memory_bytes / 1024 / 1024) if r.memory_bytes else 0
        console.print(Panel(
            f'CPU: [cyan]{r.cpu_cores:.3f} cores[/]   Memory: [cyan]{mem_mb} Mi[/]',
            title='Live Resource Usage (metrics-server)', border_style='dim'
        ))
        console.print()
 
    # ── Events Timeline ───────────────────────────────────────
    if report.events:
        et = Table(title='Event Timeline', box=box.SIMPLE, show_lines=False)
        et.add_column('Time', style='dim', width=22)
        et.add_column('Type', width=8)
        et.add_column('Reason', style='bold', width=22)
        et.add_column('Message')
        et.add_column('Count', justify='right', width=5)
        for ev in build_timeline(report.events):
            type_color = 'yellow' if ev['type'] == 'Warning' else 'green'
            et.add_row(
                ev['timestamp'],
                f'[{type_color}]{ev["type"]}[/]',
                ev['reason'],
                ev['message'][:120],
                str(ev['count']),
            )
        console.print(et)
        console.print()
 
    # ── Previous Container Logs (most useful for crashes) ─────
    if report.previous_logs:
        console.print(Rule('[yellow]Previous Container Logs (before last crash)[/]', style='yellow'))
        log_text = '\n'.join(report.previous_logs[-50:])  # last 50 lines
        console.print(Syntax(log_text, 'text', theme='monokai',
                             line_numbers=True, word_wrap=True))
        console.print()
 
    # ── Current Logs ──────────────────────────────────────────
    if report.logs:
        console.print(Rule('[cyan]Current Container Logs (last 50 lines)[/]', style='cyan'))
        log_text = '\n'.join(report.logs[-50:])
        console.print(Syntax(log_text, 'text', theme='monokai',
                             line_numbers=True, word_wrap=True))
        console.print()
 
    # ── AI Analysis ───────────────────────────────────────────
    if report.ai_analysis:
        console.print(Panel(
            report.ai_analysis,
            title=f'[bold purple]🤖 AI Root Cause Analysis ({report.ai_model})[/]',
            border_style='purple', padding=(1, 2)
        ))
        console.print()
 
    console.print(Rule(style='dim'))
    console.print(f'[dim]Generated by PodAutopsy at {report.generated_at.strftime("%Y-%m-%d %H:%M:%S UTC")}[/]')
    console.print()
 
 
def print_scan_summary(reports: list) -> None:
    """Print a summary table of all failed pods."""
    t = Table(title='Failed Pods Summary', box=box.ROUNDED, border_style='red')
    t.add_column('Pod', style='bold')
    t.add_column('Failure Type')
    t.add_column('Summary')
    for r in reports:
        color = FAILURE_COLORS.get(r.failure_type, 'white')
        t.add_row(
            r.pod_name,
            f'[{color}]{r.failure_type.value}[/]',
            r.failure_summary[:80],
        )
    console.print(t)

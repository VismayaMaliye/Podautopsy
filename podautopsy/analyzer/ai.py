import os
from podautopsy.models import PostMortemReport

MODEL_ID = 'claude-sonnet-4-5'

def analyze_with_ai(report: PostMortemReport) -> None:
    """Send report data to Claude via Anthropic API and populate report.ai_analysis."""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        report.ai_analysis = 'ANTHROPIC_API_KEY environment variable not set.'
        report.ai_model = MODEL_ID
        return

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except ImportError:
        report.ai_analysis = 'anthropic package not installed. Run: pip install anthropic'
        return

    prompt = _build_prompt(report)

    try:
        message = client.messages.create(
            model=MODEL_ID,
            max_tokens=1024,
            messages=[
                {'role': 'user', 'content': prompt}
            ]
        )
        report.ai_analysis = message.content[0].text
        report.ai_model = MODEL_ID
    except Exception as e:
        report.ai_analysis = f'AI analysis failed: {e}'
        report.ai_model = MODEL_ID

def _build_prompt(report: PostMortemReport) -> str:
    container_info = '\n'.join(
        f'  - {c.name}: state={c.state}, reason={c.reason}, '
        f'exit_code={c.exit_code}, restarts={c.restart_count}'
        for c in report.containers
    )

    prev_logs = '\n'.join(report.previous_logs[-20:]) if report.previous_logs else 'None'

    recent_events = '\n'.join(
        f'  [{e.type}] {e.reason}: {e.message[:150]}'
        for e in report.events[-5:]
    ) if report.events else 'None'

    pressure = [c.type for c in report.node_conditions if c.status == 'True' and c.type != 'Ready']

    return f"""You are an expert Kubernetes SRE. Analyze this pod failure and provide a concise root cause analysis.

POD: {report.pod_name}
NAMESPACE: {report.namespace}
NODE: {report.node_name}
FAILURE TYPE DETECTED: {report.failure_type.value}

CONTAINER STATES:
{container_info}

NODE PRESSURE CONDITIONS: {pressure if pressure else 'None'}

RECENT EVENTS:
{recent_events}

PREVIOUS CONTAINER LOGS (before last crash):
{prev_logs}

Provide:
1. Root cause (2-3 sentences max)
2. Most likely fix (specific, actionable)
3. How to prevent this in future (1-2 sentences)

Be direct and technical. No fluff."""
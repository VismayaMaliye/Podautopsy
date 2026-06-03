"""AI root cause analysis via AWS Bedrock (Claude 3 Sonnet)."""
import json
import boto3
from podautopsy.models import PostMortemReport
 
MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'
 
 
def analyze_with_ai(report: PostMortemReport) -> None:
    """
    Call AWS Bedrock Claude 3 Sonnet with the incident context.
    Populates report.ai_analysis and report.ai_model in place.
    Requires: AWS credentials configured + Bedrock model access enabled.
    """
    try:
        prompt = _build_prompt(report)
        client = boto3.client('bedrock-runtime', region_name='us-east-1')
 
        body = json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1024,
            'messages': [{'role': 'user', 'content': prompt}],
        })
 
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=body,
            contentType='application/json',
            accept='application/json',
        )
 
        result = json.loads(response['body'].read())
        report.ai_analysis = result['content'][0]['text']
        report.ai_model = 'Claude 3 Sonnet (AWS Bedrock)'
 
    except Exception as e:
        report.ai_analysis = f'AI analysis unavailable: {e}'
        report.ai_model = 'Error'
 
 
def _build_prompt(report: PostMortemReport) -> str:
    """Build a structured prompt with all incident context."""
    lines = []
    lines.append('You are an expert Kubernetes Site Reliability Engineer performing a post-mortem.')
    lines.append('Analyze the following Kubernetes pod incident and provide:')
    lines.append('1. Root cause explanation (what exactly went wrong and why)')
    lines.append('2. Contributing factors (node state, resource limits, etc.)')
    lines.append('3. Specific remediation steps with example YAML/commands where applicable')
    lines.append('4. Preventive measures to stop this from happening again')
    lines.append('')
    lines.append('--- INCIDENT CONTEXT ---')
    lines.append(f'Pod: {report.pod_name}')
    lines.append(f'Namespace: {report.namespace}')
    lines.append(f'Node: {report.node_name}')
    lines.append(f'Failure Type Detected: {report.failure_type.value}')
    lines.append(f'Summary: {report.failure_summary}')
    lines.append('')
 
    # Container states
    lines.append('Containers:')
    for c in report.containers:
        lines.append(f'  - {c.name}: state={c.state}, reason={c.reason}, exit_code={c.exit_code}, restarts={c.restart_count}')
    lines.append('')
 
    # Key events (Warning only, most recent 15)
    warning_events = [e for e in report.events if e.type == 'Warning'][-15:]
    if warning_events:
        lines.append('Warning Events (chronological):')
        for e in warning_events:
            lines.append(f'  [{e.reason}] {e.message[:200]}')
        lines.append('')
 
    # Node conditions
    pressure = [c for c in report.node_conditions if c.status == 'True' and c.type != 'Ready']
    if pressure:
        lines.append('Node Pressure Conditions:')
        for c in pressure:
            lines.append(f'  - {c.type}: {c.message}')
        lines.append('')
 
    # Previous container logs (the crash logs — most valuable)
    if report.previous_logs:
        lines.append('Previous Container Logs (last 50 lines before crash):')
        lines.append('```')
        lines.extend(report.previous_logs[-50:])
        lines.append('```')
        lines.append('')
 
    # Current logs
    if report.logs:
        lines.append('Current Container Logs (last 30 lines):')
        lines.append('```')
        lines.extend(report.logs[-30:])
        lines.append('```')
 
    lines.append('')
    lines.append('Please provide a thorough but concise analysis. Use markdown formatting.')
    return '\n'.join(lines)
"""Fetch current and previous container logs."""
from kubernetes.client import CoreV1Api
 
 
def fetch_pod_logs(
    core_v1: CoreV1Api,
    namespace: str,
    pod_name: str,
    tail_lines: int = 200,
) -> tuple[list[str], list[str]]:
    """
    Returns (current_logs, previous_logs).
    previous_logs = logs from the container BEFORE the last restart.
    These are often the most useful for crash diagnosis.
    """
    current = _fetch(core_v1, namespace, pod_name, tail_lines, previous=False)
    previous = _fetch(core_v1, namespace, pod_name, tail_lines, previous=True)
    return current, previous

def _fetch(core_v1, namespace, pod_name, tail_lines, previous=False) -> list[str]:
    try:
        raw = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines,
            previous=previous,
            timestamps=True,
        )
        # Handle bytes or string
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        elif not isinstance(raw, str):
            raw = str(raw)
        
        # Remove literal b'...' wrapping if present
        if raw.startswith("b'") or raw.startswith('b"'):
            raw = raw[2:-1]
            raw = raw.replace('\\n', '\n').replace('\\t', '\t')

        lines = [l for l in raw.splitlines() if l.strip()]
        return [l for l in lines if not l.startswith('unable to retrieve container logs')]
    except Exception:
        return []
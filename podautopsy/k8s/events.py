"""Fetch pod-related Kubernetes events sorted by timestamp."""
from kubernetes.client import CoreV1Api
from podautopsy.models import PodEvent
 
 
def fetch_pod_events(core_v1: CoreV1Api, namespace: str, pod_name: str) -> list[PodEvent]:
    events = core_v1.list_namespaced_event(
        namespace=namespace,
        field_selector=f'involvedObject.name={pod_name}'
    )
 
    result = []
    for e in events.items:
        result.append(PodEvent(
            timestamp=e.last_timestamp or e.event_time,
            type=e.type or 'Unknown',          # Normal or Warning
            reason=e.reason or '',             # Killing, BackOff, Evicted, Pulled...
            message=e.message or '',
            count=e.count or 1,
        ))
 
    # Sort oldest first so report reads chronologically
    result.sort(key=lambda x: x.timestamp or __import__('datetime').datetime.min.replace(
        tzinfo=__import__('datetime').timezone.utc))
    return result

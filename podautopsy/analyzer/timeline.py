"""Build a chronological timeline from events for display in reports."""
from podautopsy.models import PodEvent
 
 
def build_timeline(events: list[PodEvent]) -> list[dict]:
    """
    Convert events into a clean timeline list for display.
    Each entry: {timestamp_str, type, reason, message, count}
    """
    timeline = []
    for event in events:
        ts = ''
        if event.timestamp:
            if hasattr(event.timestamp, 'strftime'):
                ts = event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')
            else:
                ts = str(event.timestamp)
 
        timeline.append({
            'timestamp': ts,
            'type': event.type,           # Warning / Normal
            'reason': event.reason,
            'message': event.message[:300],  # truncate long messages
            'count': event.count,
        })
    return timeline

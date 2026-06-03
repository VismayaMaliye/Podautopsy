"""Fetch node conditions to detect MemoryPressure, DiskPressure, etc."""
from kubernetes.client import CoreV1Api
from podautopsy.models import NodeCondition
 
# These conditions being True means the node is under pressure
PRESSURE_CONDITIONS = {'MemoryPressure', 'DiskPressure', 'PIDPressure', 'NetworkUnavailable'}
 
 
def fetch_node_conditions(core_v1: CoreV1Api, node_name: str) -> list[NodeCondition]:
    try:
        node = core_v1.read_node(name=node_name)
    except Exception:
        return []
 
    result = []
    if node.status and node.status.conditions:
        for cond in node.status.conditions:
            result.append(NodeCondition(
                type=cond.type,
                status=cond.status,   # 'True', 'False', or 'Unknown'
                message=cond.message or '',
            ))
    return result
 
 
def is_node_under_pressure(conditions: list[NodeCondition]) -> bool:
    """Returns True if node has any pressure condition active."""
    return any(
        c.type in PRESSURE_CONDITIONS and c.status == 'True'
        for c in conditions
    )

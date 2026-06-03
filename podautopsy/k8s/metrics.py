"""Fetch live resource usage from metrics-server (if installed)."""
from kubernetes import client, config
from podautopsy.models import ResourceUsage
import re
 
 
def fetch_resource_usage(namespace: str, pod_name: str) -> ResourceUsage:
    """
    Calls the metrics.k8s.io API (requires metrics-server in cluster).
    Returns ResourceUsage with None values if metrics-server is unavailable.
    """
    try:
        api = client.CustomObjectsApi()
        data = api.get_namespaced_custom_object(
            group='metrics.k8s.io',
            version='v1beta1',
            namespace=namespace,
            plural='pods',
            name=pod_name,
        )
        containers = data.get('containers', [])
        if containers:
            usage = containers[0].get('usage', {})
            return ResourceUsage(
                cpu_cores=_parse_cpu(usage.get('cpu', '0')),
                memory_bytes=_parse_memory(usage.get('memory', '0')),
            )
    except Exception:
        pass  # metrics-server not installed or pod has no metrics yet
    return ResourceUsage()
 
 
def _parse_cpu(cpu_str: str) -> float:
    # '250m' -> 0.25 cores, '1' -> 1.0 cores
    if cpu_str.endswith('m'):
        return int(cpu_str[:-1]) / 1000
    return float(cpu_str)
 
 
def _parse_memory(mem_str: str) -> int:
    # '512Mi' -> bytes, '1Gi' -> bytes
    units = {'Ki': 1024, 'Mi': 1024**2, 'Gi': 1024**3, 'Ti': 1024**4,
             'K': 1000, 'M': 1000**2, 'G': 1000**3}
    for suffix, multiplier in units.items():
        if mem_str.endswith(suffix):
            return int(mem_str[:-len(suffix)]) * multiplier
    return int(mem_str)

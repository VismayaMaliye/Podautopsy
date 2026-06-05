"""Fetch pod metadata, container states, and restart history."""
from datetime import datetime, timezone
from typing import Optional
from kubernetes.client import CoreV1Api, V1Pod
from podautopsy.models import PostMortemReport, ContainerState, FailureType
 
 
def fetch_pod_data(core_v1: CoreV1Api, namespace: str, pod_name: str) -> PostMortemReport:
    """Fetch all pod data and return a partially-filled PostMortemReport."""
    try:
        pod: V1Pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
    except Exception as e:
        raise RuntimeError(f'Pod {pod_name!r} not found in namespace {namespace!r}: {e}')
 
    report = PostMortemReport(
        pod_name=pod_name,
        namespace=namespace,
        node_name=pod.spec.node_name,
    )
 
    # Parse each container
    if pod.status and pod.status.container_statuses:
        for cs in pod.status.container_statuses:
            report.containers.append(_parse_container_status(cs))
 
    return report
 
 
def _parse_container_status(cs) -> ContainerState:
    state = ContainerState(
        name=cs.name,
        ready=cs.ready or False,
        restart_count=cs.restart_count or 0,
        state='unknown',
    )
 
    if cs.state:
        if cs.state.running:
            state.state = 'running'
            state.last_started = cs.state.running.started_at
        elif cs.state.waiting:
            state.state = 'waiting'
            state.reason = cs.state.waiting.reason  # CrashLoopBackOff, ImagePullBackOff
        elif cs.state.terminated:
            state.state = 'terminated'
            state.reason = cs.state.terminated.reason  # OOMKilled, Error, Completed
            state.exit_code = cs.state.terminated.exit_code
            state.last_started = cs.state.terminated.started_at
            state.last_finished = cs.state.terminated.finished_at
            state.last_message = cs.state.terminated.message
 
    # Also check PREVIOUS container state (the crash before this restart)
    if cs.last_state and cs.last_state.terminated:
        lt = cs.last_state.terminated
        # If current state is 'waiting' (e.g. CrashLoopBackOff), the real crash
        # reason is in last_state.terminated.reason (OOMKilled, Error, etc.)
        if not state.reason:
            state.reason = lt.reason
        if not state.exit_code:
            state.exit_code = lt.exit_code
        state.last_finished = lt.finished_at
 
    return state
 
 
def list_failed_pods(core_v1: CoreV1Api, namespace: str) -> list[PostMortemReport]:
    """List all pods in non-Running/Succeeded state."""
    pods = core_v1.list_namespaced_pod(namespace=namespace)
    failed = []
    for pod in pods.items:
        phase = pod.status.phase if pod.status else 'Unknown'
        if phase in ('Failed', 'Unknown') or _has_crashing_container(pod):
            failed.append(fetch_pod_data(core_v1, namespace, pod.metadata.name))
    return failed
 
 
def _has_crashing_container(pod) -> bool:
    if not pod.status or not pod.status.container_statuses:
        return False
    for cs in pod.status.container_statuses:
        # Only flag if currently in a bad waiting state
        if cs.state and cs.state.waiting:
            reason = cs.state.waiting.reason or ''
            if reason in ('CrashLoopBackOff', 'OOMKilled', 'ImagePullBackOff', 'ErrImagePull'):
                return True
        # Or if restarting frequently right now (not just once from a node reboot)
        if cs.restart_count and cs.restart_count > 3:
            return True
    return False
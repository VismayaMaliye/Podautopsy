"""
Failure detection engine.
Inspects container states, events, and node conditions to determine
the root failure type and generate a human-readable summary + fix suggestion.
"""
from podautopsy.models import PostMortemReport, FailureType
from podautopsy.k8s.node import is_node_under_pressure
 
 
# ── Suggested fixes per failure type ───────────────────────────
FIXES = {
    FailureType.OOM_KILLED: (
        'Container exceeded its memory limit and was killed by the OOM killer. '
        'Increase the memory limit in your Deployment spec: '
        'resources.limits.memory. Also check for memory leaks in your application. '
        'Consider adding JVM flags like -XX:MaxRAMPercentage=75 if using Java.'
    ),
    FailureType.CRASH_LOOP: (
        'Container is crashing and Kubernetes keeps restarting it. '
        'Check the previous container logs (above) for the actual crash reason -'
        'CrashLoopBackOff is a symptom, not the root cause. Common causes: '
        'missing env vars/secrets, failed DB connection on startup, bad entrypoint.'
    ),
    FailureType.EVICTED: (
        'Pod was evicted from the node, most likely due to node resource pressure. '
        'Add resource requests to your pod spec so the scheduler places it correctly. '
        'Check node conditions above. Consider adding a PodDisruptionBudget.'
    ),
    FailureType.IMAGE_PULL: (
        'Kubernetes cannot pull the container image. Check: '
        '1) Image name/tag is correct, 2) ECR/registry credentials are valid, '
        '3) imagePullSecret is configured for private registries, '
        '4) You are not using :latest tag in production.'
    ),
    FailureType.PENDING: (
        'Pod cannot be scheduled. Check: '
        '1) Sufficient node capacity (kubectl describe nodes), '
        '2) Node selectors/affinity rules are satisfiable, '
        '3) PersistentVolumeClaims are bound, '
        '4) Resource requests are not too high.'
    ),
    FailureType.UNKNOWN: (
        'Could not determine failure type automatically. '
        'Review the events timeline and previous container logs above.'
    ),
}
 
 
def detect_failure(report: PostMortemReport) -> None:
    """
    Detect failure type and populate report.failure_type,
    report.failure_summary, and report.suggested_fix.
    Modifies report in place.
    """
    failure_type, summary = _detect(report)
    report.failure_type = failure_type
    report.failure_summary = summary
    report.suggested_fix = FIXES.get(failure_type, FIXES[FailureType.UNKNOWN])
 
 
def _detect(report: PostMortemReport) -> tuple[FailureType, str]:
    # Check containers in order of specificity
    for container in report.containers:
        reason = (container.reason or '').strip()
 
        # OOMKilled -container exceeded memory limit
        if reason == 'OOMKilled' or container.exit_code == 137:
            return FailureType.OOM_KILLED, (
                f'Container {container.name!r} was OOMKilled '
                f'(exit code 137). It exceeded its memory limit. '
                f'Restart count: {container.restart_count}.'
            )
 
        # CrashLoopBackOff -container keeps crashing on restart
        if reason == 'CrashLoopBackOff':
            return FailureType.CRASH_LOOP, (
                f'Container {container.name!r} is in CrashLoopBackOff. '
                f'It has restarted {container.restart_count} time(s). '
                f'Check previous container logs for the real crash reason.'
            )
 
        # ImagePullBackOff -cannot pull container image
        if reason in ('ImagePullBackOff', 'ErrImagePull'):
            return FailureType.IMAGE_PULL, (
                f'Container {container.name!r} cannot pull its image. '
                f'Reason: {reason}.'
            )
 
        # Error exit -non-zero exit code that is not OOM
        if container.state == 'terminated' and container.exit_code not in (0, None, 137):
            return FailureType.CRASH_LOOP, (
                f'Container {container.name!r} exited with code {container.exit_code}. '
                f'Restart count: {container.restart_count}.'
            )
 
    # Check events for Eviction
    for event in report.events:
        if event.reason == 'Evicted' or 'evict' in event.message.lower():
            return FailureType.EVICTED, (
                f'Pod was evicted from node {report.node_name!r}. '
                f'Reason: {event.message[:200]}'
            )
 
    # Check node pressure as contributing factor
    if is_node_under_pressure(report.node_conditions):
        pressure = [c.type for c in report.node_conditions if c.status == 'True']
        return FailureType.EVICTED, (
            f'Node {report.node_name!r} is under pressure: {pressure}. '
            f'This likely caused pod eviction or OOMKill.'
        )
 
    return FailureType.UNKNOWN, 'Could not determine failure type from available data.'



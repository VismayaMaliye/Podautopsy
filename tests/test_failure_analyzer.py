"""Unit tests for failure detection -no K8s cluster needed."""
from podautopsy.models import PostMortemReport, ContainerState, PodEvent, FailureType
from podautopsy.analyzer.failure import detect_failure
 
 
def make_report(**kwargs) -> PostMortemReport:
    return PostMortemReport(pod_name='test-pod', namespace='default',
                            node_name='node-1', **kwargs)
 
 
def test_detects_oomkill():
    report = make_report(containers=[
        ContainerState(name='app', ready=False, restart_count=3,
                       state='waiting', reason='OOMKilled', exit_code=137)
    ])
    detect_failure(report)
    assert report.failure_type == FailureType.OOM_KILLED
    assert 'memory' in report.suggested_fix.lower()
 
 
def test_detects_crashloop():
    report = make_report(containers=[
        ContainerState(name='app', ready=False, restart_count=5,
                       state='waiting', reason='CrashLoopBackOff')
    ])
    detect_failure(report)
    assert report.failure_type == FailureType.CRASH_LOOP
 
 
def test_detects_imagepull():
    report = make_report(containers=[
        ContainerState(name='app', ready=False, restart_count=0,
                       state='waiting', reason='ImagePullBackOff')
    ])
    detect_failure(report)
    assert report.failure_type == FailureType.IMAGE_PULL
 
 
def test_detects_eviction_via_event():
    report = make_report(events=[
        PodEvent(timestamp=None, type='Warning', reason='Evicted',
                 message='The node was low on resource: memory.')
    ])
    detect_failure(report)
    assert report.failure_type == FailureType.EVICTED
 
 
def test_unknown_when_no_signals():
    report = make_report()
    detect_failure(report)
    assert report.failure_type == FailureType.UNKNOWN



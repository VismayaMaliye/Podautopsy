"""Pydantic data models for PodAutopsy."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
 
 
class FailureType(str, Enum):
    OOM_KILLED        = "OOMKilled"
    CRASH_LOOP        = "CrashLoopBackOff"
    EVICTED           = "Evicted"
    IMAGE_PULL        = "ImagePullBackOff"
    PENDING           = "Pending"
    COMPLETED         = "Completed"
    UNKNOWN           = "Unknown"
 
 
@dataclass
class ContainerState:
    name: str
    ready: bool
    restart_count: int
    state: str                          # running / waiting / terminated
    reason: Optional[str] = None        # OOMKilled, CrashLoopBackOff, etc.
    exit_code: Optional[int] = None
    last_started: Optional[datetime] = None
    last_finished: Optional[datetime] = None
    last_message: Optional[str] = None  # termination message
 
 
@dataclass
class PodEvent:
    timestamp: Optional[datetime]
    type: str          # Normal / Warning
    reason: str        # Killing, BackOff, Evicted, etc.
    message: str
    count: int = 1
 
 
@dataclass
class NodeCondition:
    type: str          # MemoryPressure, DiskPressure, etc.
    status: str        # True / False / Unknown
    message: str = ''
 
 
@dataclass
class ResourceUsage:
    cpu_cores: Optional[float] = None   # actual usage in cores
    memory_bytes: Optional[int] = None  # actual usage in bytes
    cpu_limit: Optional[float] = None   # from pod spec
    memory_limit: Optional[int] = None  # from pod spec
    cpu_request: Optional[float] = None
    memory_request: Optional[int] = None
 
 
@dataclass
class PostMortemReport:
    # Identity
    pod_name: str
    namespace: str
    node_name: Optional[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)
 
    # Failure summary
    failure_type: FailureType = FailureType.UNKNOWN
    failure_summary: str = ''
    suggested_fix: str = ''
 
    # Details
    containers: list[ContainerState] = field(default_factory=list)
    events: list[PodEvent] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)
    previous_logs: list[str] = field(default_factory=list)
    node_conditions: list[NodeCondition] = field(default_factory=list)
    resources: Optional[ResourceUsage] = None
 
    # AI analysis
    ai_analysis: Optional[str] = None
    ai_model: Optional[str] = None



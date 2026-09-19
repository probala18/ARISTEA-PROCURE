"""Small in-process job registry for asynchronous API work.

Jobs are intentionally bounded to the lifetime of the API process. The job
payload and result are kept in memory; durable procurement records remain
owned by the existing database services.
"""
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Optional
from uuid import uuid4


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobRecord:
    def __init__(self, job_type: str):
        self.id = str(uuid4())
        self.job_type = job_type
        self.status = JobStatus.QUEUED
        self.result: Any = None
        self.error: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at
        self.future: Optional[Future[Any]] = None


class JobRegistry:
    """Thread-safe, bounded executor-backed job registry."""

    def __init__(self, max_workers: int = 4, max_jobs: int = 1000):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="aristea-job")
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = Lock()
        self._max_jobs = max_jobs
        self._shutdown = False

    def submit(self, job_type: str, work: Callable[[], Any]) -> JobRecord:
        with self._lock:
            if self._shutdown:
                raise RuntimeError("Asynchronous job registry is shut down.")
            self._evict_completed_jobs()
            if len(self._jobs) >= self._max_jobs:
                raise RuntimeError("Asynchronous job capacity is temporarily full.")
            record = JobRecord(job_type)
            self._jobs[record.id] = record
            record.future = self._executor.submit(self._run, record, work)
            return record

    def shutdown(self, wait: bool = True) -> None:
        """Stop accepting work and release executor resources.

        Shutdown is idempotent so application lifecycle hooks and explicit
        cleanup can safely call it more than once.
        """
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
        self._executor.shutdown(wait=wait)

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)

    def _run(self, record: JobRecord, work: Callable[[], Any]) -> None:
        with self._lock:
            record.status = JobStatus.RUNNING
            record.updated_at = datetime.now(timezone.utc)
        try:
            result = work()
        except Exception as exc:
            with self._lock:
                record.status = JobStatus.FAILED
                record.error = str(exc)
                record.updated_at = datetime.now(timezone.utc)
            return
        with self._lock:
            record.status = JobStatus.COMPLETED
            record.result = result
            record.updated_at = datetime.now(timezone.utc)

    def _evict_completed_jobs(self) -> None:
        if len(self._jobs) < self._max_jobs:
            return
        completed = [
            job_id for job_id, record in self._jobs.items()
            if record.status in (JobStatus.COMPLETED, JobStatus.FAILED)
        ]
        for job_id in completed[: max(1, len(completed) // 4)]:
            self._jobs.pop(job_id, None)


job_registry = JobRegistry()

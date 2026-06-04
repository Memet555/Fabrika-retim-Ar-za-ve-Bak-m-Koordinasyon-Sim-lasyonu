"""
Simülasyon boyunca toplanacak metrikleri yönetir.
"""
from typing import List, Dict
from simulation.entities import Job

class MetricsCollector:
    """Tüm simülasyon sonuçlarını toplayan merkezi yapı."""
    def __init__(self):
        self.jobs: List[Job] = []
        self.machine_busy_time: Dict[str, float] = {}
        self.machine_breakdowns: Dict[str, int] = {}
        self.machine_downtime: Dict[str, float] = {}
        self.machine_blocked_time: Dict[str, float] = {}
        self.machine_pm_time: Dict[str, float] = {}
        self.machine_accumulated_time: Dict[str, float] = {}
        self.technician_busy_time: float = 0.0
        self.total_breakdowns: int = 0
        self.total_pm_count: int = 0
        self.total_completed_jobs: int = 0
        
    def add_job(self, job: Job):
        """Sisteme giren yeni işi kaydeder."""
        self.jobs.append(job)
        
    def record_completed_job(self):
        """Tamamlanan iş sayacını artırır."""
        self.total_completed_jobs += 1

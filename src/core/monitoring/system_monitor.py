import psutil
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ProcessMetrics:
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    io_counters: Optional[Dict] = None
    thread_count: int = 0
    create_time: float = 0.0
    status: str = ""
    priority: int = 0

@dataclass
class SystemMetrics:
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io: Dict
    network_io: Dict
    processes: List[ProcessMetrics]
    context_switches: int
    interrupts: int
    boot_time: float

class SystemMonitor:
    def __init__(self):
        self.last_net_io = psutil.net_io_counters()
        self.last_disk_io = psutil.disk_io_counters()
        self.last_context_switches = psutil.cpu_stats().ctx_switches
        self.last_interrupts = psutil.cpu_stats().interrupts
        self.last_update = time.time()
        
        # Initialize process tracking
        self.tracked_processes = set()
        self.process_history = {}
        
        logger.info("SystemMonitor initialized")
        
    def get_latest_data(self) -> SystemMetrics:
        """Collect the latest system metrics"""
        try:
            current_time = time.time()
            time_diff = current_time - self.last_update
            
            # Get CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # Get disk I/O
            current_disk_io = psutil.disk_io_counters()
            disk_io = {
                'read_bytes': (current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_diff,
                'write_bytes': (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_diff,
                'read_count': (current_disk_io.read_count - self.last_disk_io.read_count) / time_diff,
                'write_count': (current_disk_io.write_count - self.last_disk_io.write_count) / time_diff
            }
            
            # Get network I/O
            current_net_io = psutil.net_io_counters()
            network_io = {
                'bytes_sent': (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_diff,
                'bytes_recv': (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_diff,
                'packets_sent': (current_net_io.packets_sent - self.last_net_io.packets_sent) / time_diff,
                'packets_recv': (current_net_io.packets_recv - self.last_net_io.packets_recv) / time_diff
            }
            
            # Get context switches and interrupts
            current_stats = psutil.cpu_stats()
            context_switches = current_stats.ctx_switches - self.last_context_switches
            interrupts = current_stats.interrupts - self.last_interrupts
            
            # Get process metrics
            processes = self._get_process_metrics()
            
            # Update last values
            self.last_net_io = current_net_io
            self.last_disk_io = current_disk_io
            self.last_context_switches = current_stats.ctx_switches
            self.last_interrupts = current_stats.interrupts
            self.last_update = current_time
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_io=disk_io,
                network_io=network_io,
                processes=processes,
                context_switches=context_switches,
                interrupts=interrupts,
                boot_time=psutil.boot_time()
            )
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
            raise
            
    def _get_process_metrics(self) -> List[ProcessMetrics]:
        """Collect detailed metrics for all processes"""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                          'io_counters', 'num_threads', 'create_time', 
                                          'status', 'nice']):
                try:
                    with proc.oneshot():
                        metrics = ProcessMetrics(
                            pid=proc.info['pid'],
                            name=proc.info['name'],
                            cpu_percent=proc.info['cpu_percent'],
                            memory_percent=proc.info['memory_percent'],
                            io_counters=proc.info['io_counters']._asdict() if proc.info['io_counters'] else None,
                            thread_count=proc.info['num_threads'],
                            create_time=proc.info['create_time'],
                            status=proc.info['status'],
                            priority=proc.info['nice']
                        )
                        processes.append(metrics)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Error collecting process metrics: {str(e)}")
            
        return processes
        
    def track_process(self, pid: int):
        """Start tracking a specific process"""
        self.tracked_processes.add(pid)
        
    def untrack_process(self, pid: int):
        """Stop tracking a specific process"""
        self.tracked_processes.discard(pid)
        
    def get_process_history(self, pid: int) -> List[ProcessMetrics]:
        """Get historical metrics for a specific process"""
        return self.process_history.get(pid, [])
        
    def clear_history(self):
        """Clear all historical process data"""
        self.process_history.clear() 
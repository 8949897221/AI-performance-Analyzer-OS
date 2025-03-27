import psutil
import win32process
import win32con
import win32api
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import os

logger = logging.getLogger(__name__)

@dataclass
class ProcessInfo:
    """Data class for industrial process information"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    status: str
    priority: int
    num_threads: int
    io_counters: Optional[Dict] = None
    create_time: Optional[datetime] = None
    process_type: str = "Standard"  # Industrial, Control, Monitoring, etc.
    criticality: str = "Low"  # Critical, High, Medium, Low
    uptime: float = 0.0
    response_time: float = 0.0

class ProcessManager:
    """Manager for industrial system processes"""
    
    def __init__(self):
        self._process_cache = {}
        self._last_update = 0
        self._update_interval = 0.5  # Reduced to 0.5 seconds for faster updates
        self._critical_processes = set()
        self._industrial_processes = {
            'plc': ['plc.exe', 'scada.exe', 'hmi.exe'],
            'control': ['control.exe', 'automation.exe', 'robot.exe'],
            'monitoring': ['monitor.exe', 'sensor.exe', 'data_logger.exe']
        }
        
        logger.info("Industrial ProcessManager initialized")
        
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get information about a specific process with improved response time"""
        try:
            if pid in self._process_cache:
                cached_info = self._process_cache[pid]
                if (datetime.now() - cached_info.create_time).total_seconds() < self._update_interval:
                    return cached_info

            proc = psutil.Process(pid)
            with proc.oneshot():
                process_type = self._get_process_type(proc.name())
                criticality = self._get_process_criticality(proc.name())
                
                info = ProcessInfo(
                    pid=proc.pid,
                    name=proc.name(),
                    cpu_percent=proc.cpu_percent(),
                    memory_percent=proc.memory_percent(),
                    status=proc.status(),
                    priority=proc.nice(),
                    num_threads=proc.num_threads(),
                    io_counters=proc.io_counters()._asdict() if proc.io_counters() else None,
                    create_time=datetime.fromtimestamp(proc.create_time()),
                    process_type=process_type,
                    criticality=criticality,
                    uptime=(datetime.now() - datetime.fromtimestamp(proc.create_time())).total_seconds(),
                    response_time=self._calculate_response_time(proc)
                )
                
                self._process_cache[pid] = info
                return info
                
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error getting process info for PID {pid}: {str(e)}")
            return None
            
    def get_all_processes(self) -> List[ProcessInfo]:
        """Get list of all running processes with improved performance"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent',
                                       'status', 'nice', 'num_threads']):
            try:
                info = proc.info
                process_type = self._get_process_type(info['name'])
                criticality = self._get_process_criticality(info['name'])
                
                process_info = ProcessInfo(
                    pid=info['pid'],
                    name=info['name'],
                    cpu_percent=info['cpu_percent'] or 0.0,
                    memory_percent=info['memory_percent'] or 0.0,
                    status=info['status'],
                    priority=info['nice'] or 0,
                    num_threads=info['num_threads'],
                    process_type=process_type,
                    criticality=criticality
                )
                
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return processes

    def _get_process_type(self, process_name: str) -> str:
        """Determine process type for industrial categorization"""
        process_name = process_name.lower()
        for proc_type, keywords in self._industrial_processes.items():
            if any(keyword in process_name for keyword in keywords):
                return proc_type.capitalize()
        return "Standard"

    def _get_process_criticality(self, process_name: str) -> str:
        """Determine process criticality for industrial systems"""
        process_name = process_name.lower()
        if any(keyword in process_name for keyword in ['plc', 'scada', 'control']):
            return "Critical"
        elif any(keyword in process_name for keyword in ['hmi', 'automation', 'robot']):
            return "High"
        elif any(keyword in process_name for keyword in ['monitor', 'sensor']):
            return "Medium"
        return "Low"

    def _calculate_response_time(self, proc) -> float:
        """Calculate process response time"""
        try:
            # Get process creation time and current time
            create_time = datetime.fromtimestamp(proc.create_time())
            current_time = datetime.now()
            
            # Calculate uptime
            uptime = (current_time - create_time).total_seconds()
            
            # Get CPU times
            cpu_times = proc.cpu_times()
            
            # Calculate response time (user + system time)
            response_time = cpu_times.user + cpu_times.system
            
            return response_time
        except:
            return 0.0

    def optimize_process(self, pid: int, optimization_level: str = "standard") -> bool:
        """Optimize a specific process with industrial considerations"""
        try:
            proc = psutil.Process(pid)
            current_priority = proc.nice()
            
            # Get process criticality
            criticality = self._get_process_criticality(proc.name())
            
            # Adjust optimization based on criticality
            if criticality == "Critical":
                return True  # Don't optimize critical processes
            elif criticality == "High":
                new_priority = max(-10, current_priority - 1)
            else:
                if optimization_level == "aggressive":
                    new_priority = max(-20, current_priority - 5)
                else:
                    new_priority = max(-10, current_priority - 2)
                    
            proc.nice(new_priority)
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error optimizing process {pid}: {str(e)}")
            return False
            
    def optimize_cpu_usage(self) -> None:
        """Optimize CPU usage with industrial process prioritization"""
        try:
            processes = self.get_all_processes()
            
            # Sort processes by criticality and CPU usage
            cpu_intensive = sorted(
                [p for p in processes if p.cpu_percent > 50],
                key=lambda x: (x.criticality != "Critical", x.cpu_percent),
                reverse=True
            )
            
            # Adjust priorities for CPU-intensive processes
            for proc in cpu_intensive:
                try:
                    if proc.criticality != "Critical":
                        psutil_proc = psutil.Process(proc.pid)
                        current_nice = psutil_proc.nice()
                        
                        # Lower priority for high CPU usage processes
                        if proc.cpu_percent > 80:
                            psutil_proc.nice(current_nice + 5)
                        elif proc.cpu_percent > 60:
                            psutil_proc.nice(current_nice + 3)
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            logger.error(f"Error optimizing CPU usage: {str(e)}")
            
    def optimize_memory_usage(self) -> None:
        """Optimize memory usage with industrial process considerations"""
        try:
            processes = self.get_all_processes()
            
            # Sort processes by criticality and memory usage
            mem_intensive = sorted(
                [p for p in processes if p.memory_percent > 5],
                key=lambda x: (x.criticality != "Critical", x.memory_percent),
                reverse=True
            )
            
            # Generate memory optimization report
            report = []
            for proc in mem_intensive:
                try:
                    if proc.criticality != "Critical":
                        details = self.get_process_info(proc.pid)
                        if details:
                            report.append({
                                'pid': proc.pid,
                                'name': proc.name,
                                'memory_percent': proc.memory_percent,
                                'memory_info': details.io_counters,
                                'recommendation': self._get_memory_recommendation(details)
                            })
                except Exception:
                    continue
                    
            # Log optimization report
            logger.info("Memory optimization report:")
            for item in report:
                logger.info(f"Process {item['name']} (PID: {item['pid']}): "
                          f"{item['memory_percent']:.1f}% memory usage - "
                          f"Recommendation: {item['recommendation']}")
                          
        except Exception as e:
            logger.error(f"Error optimizing memory usage: {str(e)}")
            
    def _get_memory_recommendation(self, process_details: ProcessInfo) -> str:
        """Get memory optimization recommendation for industrial processes"""
        try:
            memory_percent = process_details.memory_percent
            criticality = process_details.criticality
            
            if criticality == "Critical":
                return "Maintain current memory allocation"
            elif memory_percent > 80:
                return "Consider terminating or reducing process priority"
            elif memory_percent > 60:
                return "Monitor closely and optimize if possible"
            elif memory_percent > 40:
                return "Regular monitoring recommended"
            else:
                return "No immediate action needed"
                
        except Exception as e:
            logger.error(f"Error getting memory recommendation: {str(e)}")
            return "Unable to generate recommendation"
            
    def terminate_process(self, pid: int) -> bool:
        """Terminate a process by PID with industrial safety checks"""
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            
            # Check if process is critical
            if self._get_process_criticality(process_name) == "Critical":
                logger.warning(f"Attempted to terminate critical process: {process_name}")
                return False
                
            proc.terminate()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error terminating process {pid}: {str(e)}")
            return False
            
    def kill_process(self, pid: int) -> bool:
        """Force kill a process by PID with industrial safety checks"""
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            
            # Check if process is critical
            if self._get_process_criticality(process_name) == "Critical":
                logger.warning(f"Attempted to kill critical process: {process_name}")
                return False
                
            proc.kill()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error killing process {pid}: {str(e)}")
            return False
            
    def suspend_process(self, pid: int) -> bool:
        """Suspend a process with industrial safety checks"""
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            
            # Check if process is critical
            if self._get_process_criticality(process_name) == "Critical":
                logger.warning(f"Attempted to suspend critical process: {process_name}")
                return False
                
            proc.suspend()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error suspending process {pid}: {str(e)}")
            return False
            
    def resume_process(self, pid: int) -> bool:
        """Resume a suspended process"""
        try:
            proc = psutil.Process(pid)
            proc.resume()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Error resuming process {pid}: {str(e)}")
            return False 
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import psutil
import win32process
import win32con
import win32api

logger = logging.getLogger(__name__)

@dataclass
class OptimizationAction:
    pid: int
    action_type: str
    parameters: Dict
    timestamp: datetime
    priority: float

class SynergyCore:
    def __init__(self):
        self.optimization_history: List[OptimizationAction] = []
        self.action_threshold = 0.7  # Minimum priority to take action
        self.last_optimization = datetime.now()
        
        # Initialize optimization parameters
        self.cpu_threshold = 80.0  # CPU usage threshold
        self.memory_threshold = 85.0  # Memory usage threshold
        self.io_threshold = 1000000  # I/O operations threshold
        
        logger.info("SynergyCore initialized")
        
    def process(self, system_metrics):
        """Process system metrics and generate optimization actions"""
        try:
            # Check if optimization is needed
            if not self._should_optimize():
                return
                
            # Analyze system state
            actions = self._analyze_system_state(system_metrics)
            
            # Apply optimization actions
            for action in actions:
                if action.priority >= self.action_threshold:
                    self._apply_optimization(action)
                    
            self.last_optimization = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in SynergyCore processing: {str(e)}")
            
    def _should_optimize(self) -> bool:
        """Determine if optimization should be performed"""
        time_since_last = (datetime.now() - self.last_optimization).total_seconds()
        return time_since_last >= 0.5  # Optimize every 500ms
        
    def _analyze_system_state(self, system_metrics) -> List[OptimizationAction]:
        """Analyze system state and generate optimization actions"""
        actions = []
        
        # Analyze overall system state
        if system_metrics.cpu_percent > self.cpu_threshold:
            actions.extend(self._optimize_cpu_usage(system_metrics))
            
        if system_metrics.memory_percent > self.memory_threshold:
            actions.extend(self._optimize_memory_usage(system_metrics))
            
        # Analyze individual processes
        for proc in system_metrics.processes:
            if self._is_process_optimizable(proc):
                actions.extend(self._optimize_process(proc))
                
        return actions
        
    def _is_process_optimizable(self, proc) -> bool:
        """Check if a process can be optimized"""
        try:
            # Check if process is system process
            if proc.pid < 100:  # System processes typically have low PIDs
                return False
                
            # Check if process is critical
            if proc.name.lower() in ['system', 'svchost.exe', 'explorer.exe']:
                return False
                
            return True
            
        except Exception:
            return False
            
    def _optimize_cpu_usage(self, system_metrics) -> List[OptimizationAction]:
        """Generate CPU optimization actions"""
        actions = []
        
        # Sort processes by CPU usage
        sorted_procs = sorted(
            system_metrics.processes,
            key=lambda x: x.cpu_percent,
            reverse=True
        )
        
        # Target top CPU-consuming processes
        for proc in sorted_procs[:5]:  # Top 5 CPU consumers
            if proc.cpu_percent > 50:  # Only optimize high CPU processes
                actions.append(OptimizationAction(
                    pid=proc.pid,
                    action_type='cpu_optimization',
                    parameters={
                        'priority_class': 'BELOW_NORMAL',
                        'affinity_mask': self._calculate_optimal_affinity(proc)
                    },
                    timestamp=datetime.now(),
                    priority=proc.cpu_percent / 100.0
                ))
                
        return actions
        
    def _optimize_memory_usage(self, system_metrics) -> List[OptimizationAction]:
        """Generate memory optimization actions"""
        actions = []
        
        # Sort processes by memory usage
        sorted_procs = sorted(
            system_metrics.processes,
            key=lambda x: x.memory_percent,
            reverse=True
        )
        
        # Target high memory-consuming processes
        for proc in sorted_procs[:5]:  # Top 5 memory consumers
            if proc.memory_percent > 50:  # Only optimize high memory processes
                actions.append(OptimizationAction(
                    pid=proc.pid,
                    action_type='memory_optimization',
                    parameters={
                        'priority_class': 'BELOW_NORMAL',
                        'working_set_limit': self._calculate_working_set_limit(proc)
                    },
                    timestamp=datetime.now(),
                    priority=proc.memory_percent / 100.0
                ))
                
        return actions
        
    def _optimize_process(self, proc) -> List[OptimizationAction]:
        """Generate process-specific optimization actions"""
        actions = []
        
        # Check I/O operations
        if proc.io_counters and (proc.io_counters['read_bytes'] + proc.io_counters['write_bytes']) > self.io_threshold:
            actions.append(OptimizationAction(
                pid=proc.pid,
                action_type='io_optimization',
                parameters={
                    'priority_class': 'BELOW_NORMAL',
                    'io_priority': 'LOW'
                },
                timestamp=datetime.now(),
                priority=0.8
            ))
            
        # Check thread count
        if proc.thread_count > 100:  # High thread count threshold
            actions.append(OptimizationAction(
                pid=proc.pid,
                action_type='thread_optimization',
                parameters={
                    'priority_class': 'BELOW_NORMAL',
                    'thread_limit': 100
                },
                timestamp=datetime.now(),
                priority=0.7
            ))
            
        return actions
        
    def _calculate_optimal_affinity(self, proc) -> int:
        """Calculate optimal CPU affinity for a process"""
        try:
            # Get available CPU cores
            cpu_count = psutil.cpu_count()
            
            # Calculate optimal affinity mask based on process characteristics
            if proc.cpu_percent > 80:
                # High CPU usage: spread across all cores
                return (1 << cpu_count) - 1
            else:
                # Moderate CPU usage: use half of available cores
                return (1 << (cpu_count // 2)) - 1
                
        except Exception:
            return 0xFFFF  # Default to all cores
            
    def _calculate_working_set_limit(self, proc) -> int:
        """Calculate optimal working set limit for a process"""
        try:
            # Get system memory info
            memory = psutil.virtual_memory()
            
            # Calculate limit based on total memory and process usage
            if proc.memory_percent > 80:
                # High memory usage: limit to 50% of current usage
                return int(proc.memory_percent * memory.total * 0.5)
            else:
                # Moderate memory usage: limit to 75% of current usage
                return int(proc.memory_percent * memory.total * 0.75)
                
        except Exception:
            return 0  # No limit
            
    def _apply_optimization(self, action: OptimizationAction):
        """Apply optimization action to a process"""
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, action.pid)
            
            if action.action_type == 'cpu_optimization':
                # Set process priority
                if action.parameters['priority_class'] == 'BELOW_NORMAL':
                    win32process.SetPriorityClass(handle, win32process.BELOW_NORMAL_PRIORITY_CLASS)
                    
                # Set CPU affinity
                win32process.SetProcessAffinityMask(handle, action.parameters['affinity_mask'])
                
            elif action.action_type == 'memory_optimization':
                # Set process priority
                if action.parameters['priority_class'] == 'BELOW_NORMAL':
                    win32process.SetPriorityClass(handle, win32process.BELOW_NORMAL_PRIORITY_CLASS)
                    
                # Set working set limits
                if action.parameters['working_set_limit'] > 0:
                    win32process.SetProcessWorkingSetSizeEx(
                        handle,
                        -1,  # Minimum working set size
                        action.parameters['working_set_limit'],
                        win32process.QUOTA_LIMITS_HARDWS_MIN_DISABLE
                    )
                    
            elif action.action_type == 'io_optimization':
                # Set process priority
                if action.parameters['priority_class'] == 'BELOW_NORMAL':
                    win32process.SetPriorityClass(handle, win32process.BELOW_NORMAL_PRIORITY_CLASS)
                    
            elif action.action_type == 'thread_optimization':
                # Set process priority
                if action.parameters['priority_class'] == 'BELOW_NORMAL':
                    win32process.SetPriorityClass(handle, win32process.BELOW_NORMAL_PRIORITY_CLASS)
                    
            win32api.CloseHandle(handle)
            
            # Record optimization action
            self.optimization_history.append(action)
            
        except Exception as e:
            logger.error(f"Error applying optimization to process {action.pid}: {str(e)}")
            
    def get_optimization_history(self) -> List[OptimizationAction]:
        """Get the history of optimization actions"""
        return self.optimization_history 
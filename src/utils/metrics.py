import psutil
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import time
from .config_manager import ConfigManager
from .logger import get_logger
from concurrent.futures import ThreadPoolExecutor
import threading

logger = get_logger(__name__)

@dataclass
class SystemMetrics:
    """Data class for system metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_read: float
    disk_io_write: float
    network_sent: float
    network_recv: float
    process_count: int
    thread_count: int
    load_average: Tuple[float, float, float]
    swap_percent: float
    temperature: Optional[float] = None
    fan_speed: Optional[float] = None
    power_usage: Optional[float] = None

class MetricsCollector:
    """Collects system metrics efficiently"""
    
    def __init__(self):
        self.config = ConfigManager()
        self.monitoring_config = self.config.get_section('monitoring')
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._metrics_cache = {}
        self._last_update = 0
        self._update_interval = 0.1  # 100ms update interval
        self._lock = threading.Lock()
        self._last_disk_io = psutil.disk_io_counters()
        self._last_net_io = psutil.net_io_counters()
        self._last_time = time.time()
        self._last_collection = 0
        self._cache_ttl = 2  # Cache metrics for 2 seconds
        
    def get_metrics(self) -> Optional[Dict]:
        """Get current system metrics"""
        current_time = time.time()
        
        # Check if we need to update
        if current_time - self._last_update < self._update_interval:
            return self._metrics_cache
            
        try:
            # Collect metrics in parallel
            futures = {
                'cpu': self._executor.submit(self._get_cpu_metrics),
                'memory': self._executor.submit(self._get_memory_metrics),
                'disk': self._executor.submit(self._get_disk_metrics),
                'network': self._executor.submit(self._get_network_metrics),
                'processes': self._executor.submit(self._get_process_metrics)
            }
            
            # Gather results
            metrics = {}
            for key, future in futures.items():
                result = future.result()
                if key == 'cpu':
                    metrics['cpu_percent'] = result['cpu_percent']
                elif key == 'memory':
                    metrics['memory_percent'] = result['memory_percent']
                elif key == 'disk':
                    metrics['disk_percent'] = result['disk_percent']
                elif key == 'network':
                    metrics['network_percent'] = result['network_percent']
                elif key == 'processes':
                    metrics['processes'] = result
            
            # Update cache with lock
            with self._lock:
                self._metrics_cache = metrics
                self._last_update = current_time
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            return self._metrics_cache
            
    def _get_cpu_metrics(self) -> Dict:
        """Get CPU metrics"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=None),
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'cpu_stats': psutil.cpu_stats()._asdict()
        }
        
    def _get_memory_metrics(self) -> Dict:
        """Get memory metrics"""
        vm = psutil.virtual_memory()
        return {
            'memory_percent': vm.percent,
            'memory_available': vm.available,
            'memory_total': vm.total,
            'memory_used': vm.used,
            'memory_free': vm.free
        }
        
    def _get_disk_metrics(self) -> Dict:
        """Get disk metrics"""
        disk = psutil.disk_usage('/')
        return {
            'disk_percent': disk.percent,
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_free': disk.free
        }
        
    def _get_network_metrics(self) -> Dict:
        """Get network metrics"""
        net_io = psutil.net_io_counters()
        return {
            'network_percent': 0,  # Calculated based on previous values
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv
        }
        
    def _get_process_metrics(self) -> Dict:
        """Get process-related metrics"""
        try:
            processes = psutil.process_iter(['name', 'cpu_percent', 'memory_percent'])
            process_count = len(list(processes))
            return {
                'process_count': process_count
            }
        except Exception as e:
            logger.error(f"Error getting process metrics: {str(e)}")
            return {'process_count': 0}
        
    def __del__(self):
        """Cleanup resources"""
        self._executor.shutdown(wait=True)

    def _should_monitor_process(self, process) -> bool:
        """Check if a process should be monitored"""
        try:
            # Skip system processes and those with very low resource usage
            if process.pid < 100:
                return False
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        try:
            # Get basic metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            current_time = time.time()
            
            # Calculate IO rates
            time_diff = current_time - self._last_time
            disk_read_rate = (disk_io.read_bytes - self._last_disk_io.read_bytes) / time_diff
            disk_write_rate = (disk_io.write_bytes - self._last_disk_io.write_bytes) / time_diff
            net_sent_rate = (net_io.bytes_sent - self._last_net_io.bytes_sent) / time_diff
            net_recv_rate = (net_io.bytes_recv - self._last_net_io.bytes_recv) / time_diff
            
            # Update last values
            self._last_disk_io = disk_io
            self._last_net_io = net_io
            self._last_time = current_time
            
            # Get additional metrics
            process_count = len(psutil.pids())
            thread_count = sum(p.num_threads() for p in psutil.process_iter(['num_threads']))
            load_avg = psutil.getloadavg()
            
            # Create metrics object
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_io_read=disk_read_rate,
                disk_io_write=disk_write_rate,
                network_sent=net_sent_rate,
                network_recv=net_recv_rate,
                process_count=process_count,
                thread_count=thread_count,
                load_average=load_avg,
                swap_percent=psutil.swap_memory().percent
            )
            
            # Add optional metrics if available
            try:
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if temps:
                        metrics.temperature = max(temp.current for temp in temps.values())
            except Exception as e:
                logger.warning(f"Could not get temperature: {str(e)}")
                
            try:
                if hasattr(psutil, "sensors_fans"):
                    fans = psutil.sensors_fans()
                    if fans:
                        metrics.fan_speed = max(fan.current for fan in fans.values())
            except Exception as e:
                logger.warning(f"Could not get fan speed: {str(e)}")
                
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
            raise

class PerformanceAnalyzer:
    """Analyzer for system performance metrics"""
    
    def __init__(self, history_size: int = 1000):
        self.config = ConfigManager()
        self.history_size = history_size
        self.metrics_history: List[SystemMetrics] = []
        self.thresholds = self.config.get_section('performance')
        
    def add_metrics(self, metrics: SystemMetrics) -> None:
        """Add new metrics to history"""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.history_size:
            self.metrics_history.pop(0)
            
    def analyze_performance(self) -> Dict[str, float]:
        """Analyze current performance and return scores"""
        try:
            if not self.metrics_history:
                return {}
                
            # Get latest metrics
            current = self.metrics_history[-1]
            
            # Calculate performance scores
            scores = {
                'cpu_score': self._calculate_cpu_score(current),
                'memory_score': self._calculate_memory_score(current),
                'io_score': self._calculate_io_score(current),
                'network_score': self._calculate_network_score(current),
                'process_score': self._calculate_process_score(current),
                'overall_score': 0.0
            }
            
            # Calculate overall score
            weights = {
                'cpu_score': 0.3,
                'memory_score': 0.2,
                'io_score': 0.2,
                'network_score': 0.15,
                'process_score': 0.15
            }
            
            scores['overall_score'] = sum(
                score * weights[metric]
                for metric, score in scores.items()
                if metric != 'overall_score'
            )
            
            return scores
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {str(e)}")
            raise
            
    def _calculate_cpu_score(self, metrics: SystemMetrics) -> float:
        """Calculate CPU performance score"""
        cpu_threshold = self.thresholds.get('cpu_threshold', 80)
        return max(0, 100 - (metrics.cpu_percent / cpu_threshold * 100))
        
    def _calculate_memory_score(self, metrics: SystemMetrics) -> float:
        """Calculate memory performance score"""
        memory_threshold = self.thresholds.get('memory_threshold', 85)
        return max(0, 100 - (metrics.memory_percent / memory_threshold * 100))
        
    def _calculate_io_score(self, metrics: SystemMetrics) -> float:
        """Calculate I/O performance score"""
        io_threshold = self.thresholds.get('io_threshold', 1000 * 1024 * 1024)  # 1GB/s
        total_io = metrics.disk_io_read + metrics.disk_io_write
        return max(0, 100 - (total_io / io_threshold * 100))
        
    def _calculate_network_score(self, metrics: SystemMetrics) -> float:
        """Calculate network performance score"""
        network_threshold = self.thresholds.get('network_threshold', 100 * 1024 * 1024)  # 100MB/s
        total_network = metrics.network_sent + metrics.network_recv
        return max(0, 100 - (total_network / network_threshold * 100))
        
    def _calculate_process_score(self, metrics: SystemMetrics) -> float:
        """Calculate process performance score"""
        process_threshold = self.thresholds.get('process_threshold', 1000)
        return max(0, 100 - (metrics.process_count / process_threshold * 100))
        
    def detect_anomalies(self) -> List[Dict[str, any]]:
        """Detect performance anomalies"""
        try:
            if len(self.metrics_history) < 2:
                return []
                
            anomalies = []
            current = self.metrics_history[-1]
            previous = self.metrics_history[-2]
            
            # Check for CPU spikes
            if current.cpu_percent > previous.cpu_percent * 2:
                anomalies.append({
                    'type': 'cpu_spike',
                    'severity': 'high',
                    'current': current.cpu_percent,
                    'previous': previous.cpu_percent
                })
                
            # Check for memory spikes
            if current.memory_percent > previous.memory_percent * 1.5:
                anomalies.append({
                    'type': 'memory_spike',
                    'severity': 'high',
                    'current': current.memory_percent,
                    'previous': previous.memory_percent
                })
                
            # Check for I/O spikes
            if (current.disk_io_read + current.disk_io_write) > \
               (previous.disk_io_read + previous.disk_io_write) * 3:
                anomalies.append({
                    'type': 'io_spike',
                    'severity': 'medium',
                    'current': current.disk_io_read + current.disk_io_write,
                    'previous': previous.disk_io_read + previous.disk_io_write
                })
                
            # Check for network spikes
            if (current.network_sent + current.network_recv) > \
               (previous.network_sent + previous.network_recv) * 3:
                anomalies.append({
                    'type': 'network_spike',
                    'severity': 'medium',
                    'current': current.network_sent + current.network_recv,
                    'previous': previous.network_sent + previous.network_recv
                })
                
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            raise
            
    def get_performance_trend(self, window: int = 10) -> Dict[str, float]:
        """Calculate performance trends over a window"""
        try:
            if len(self.metrics_history) < window:
                return {}
                
            recent_metrics = self.metrics_history[-window:]
            
            # Calculate trends using linear regression
            trends = {}
            
            # CPU trend
            cpu_values = [m.cpu_percent for m in recent_metrics]
            trends['cpu_trend'] = np.polyfit(range(len(cpu_values)), cpu_values, 1)[0]
            
            # Memory trend
            memory_values = [m.memory_percent for m in recent_metrics]
            trends['memory_trend'] = np.polyfit(range(len(memory_values)), memory_values, 1)[0]
            
            # I/O trend
            io_values = [m.disk_io_read + m.disk_io_write for m in recent_metrics]
            trends['io_trend'] = np.polyfit(range(len(io_values)), io_values, 1)[0]
            
            # Network trend
            network_values = [m.network_sent + m.network_recv for m in recent_metrics]
            trends['network_trend'] = np.polyfit(range(len(network_values)), network_values, 1)[0]
            
            return trends
            
        except Exception as e:
            logger.error(f"Error calculating performance trends: {str(e)}")
            raise 
import numpy as np
from typing import Dict, List
import logging

class AIManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("AI manager initialized successfully")

    def predict_performance(self, metrics: Dict) -> Dict:
        """Make predictions about system performance"""
        try:
            # Extract features from metrics
            cpu_percent = metrics.get('cpu_percent', 0)
            memory_percent = metrics.get('memory_percent', 0)
            disk_usage = metrics.get('disk_usage_percent', 0)
            network_usage = metrics.get('network_usage_percent', 0)

            # Simple heuristic-based predictions
            cpu_health = max(0, min(1, 1.0 - (cpu_percent / 100)))
            memory_health = max(0, min(1, 1.0 - (memory_percent / 100)))
            overall_health = (cpu_health + memory_health) / 2

            return {
                'cpu_health': float(cpu_health),
                'memory_health': float(memory_health),
                'overall_health': float(overall_health)
            }
        except Exception as e:
            self.logger.error(f"Error making predictions: {str(e)}")
            return {
                'cpu_health': 0.5,
                'memory_health': 0.5,
                'overall_health': 0.5
            }

    def get_health_status(self, predictions: Dict) -> str:
        """Get health status based on predictions"""
        overall_health = predictions.get('overall_health', 0.5)
        if overall_health >= 0.8:
            return "Excellent"
        elif overall_health >= 0.6:
            return "Good"
        elif overall_health >= 0.4:
            return "Fair"
        else:
            return "Poor"

    def get_optimization_suggestions(self, predictions: Dict) -> List[str]:
        """Get optimization suggestions based on predictions"""
        suggestions = []
        
        cpu_health = predictions.get('cpu_health', 0.5)
        memory_health = predictions.get('memory_health', 0.5)
        
        if cpu_health < 0.6:
            suggestions.append("Consider closing resource-intensive applications")
            suggestions.append("Check for background processes consuming high CPU")
        
        if memory_health < 0.6:
            suggestions.append("Close unused applications to free up memory")
            suggestions.append("Consider increasing virtual memory")
        
        return suggestions 
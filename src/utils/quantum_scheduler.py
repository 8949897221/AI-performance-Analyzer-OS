import logging
import numpy as np
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class QuantumScheduler:
    """Quantum-inspired process scheduler"""
    
    def __init__(self):
        self.entanglement_level = 50  # Default entanglement level (0-100)
        self.optimization_mode = "Standard"
        self.process_limit = 10
        
    def set_entanglement_level(self, level: int):
        """Set the quantum entanglement level"""
        if 0 <= level <= 100:
            self.entanglement_level = level
            logger.info(f"Entanglement level set to {level}")
        else:
            logger.warning("Entanglement level must be between 0 and 100")
            
    def set_optimization_mode(self, mode: str):
        """Set the optimization mode"""
        valid_modes = ["Standard", "Aggressive", "Conservative"]
        if mode in valid_modes:
            self.optimization_mode = mode
            logger.info(f"Optimization mode set to {mode}")
        else:
            logger.warning(f"Invalid optimization mode. Must be one of {valid_modes}")
            
    def set_process_limit(self, limit: int):
        """Set the maximum number of processes to optimize"""
        if limit > 0:
            self.process_limit = limit
            logger.info(f"Process limit set to {limit}")
        else:
            logger.warning("Process limit must be greater than 0")
            
    def optimize_processes(self, processes: List[Dict]) -> List[Dict]:
        """Optimize process scheduling using quantum-inspired algorithms"""
        try:
            # Sort processes by resource usage
            sorted_processes = sorted(
                processes,
                key=lambda p: p.get('cpu_percent', 0) + p.get('memory_percent', 0),
                reverse=True
            )
            
            # Apply quantum-inspired optimization
            optimized = []
            for process in sorted_processes[:self.process_limit]:
                # Calculate quantum-inspired priority score
                score = self._calculate_quantum_score(process)
                
                # Apply optimization based on mode
                if self.optimization_mode == "Aggressive":
                    priority_adjustment = int(score * 1.5)
                elif self.optimization_mode == "Conservative":
                    priority_adjustment = int(score * 0.5)
                else:  # Standard mode
                    priority_adjustment = int(score)
                    
                process['priority_adjustment'] = priority_adjustment
                optimized.append(process)
                
            logger.info(f"Optimized {len(optimized)} processes")
            return optimized
            
        except Exception as e:
            logger.error(f"Error optimizing processes: {str(e)}")
            return processes
            
    def _calculate_quantum_score(self, process: Dict) -> float:
        """Calculate quantum-inspired optimization score"""
        try:
            # Base score from resource usage
            cpu_score = process.get('cpu_percent', 0) / 100
            mem_score = process.get('memory_percent', 0) / 100
            io_score = min(1.0, process.get('io_rate', 0) / 1e6)
            
            # Apply quantum entanglement effect
            entanglement_factor = self.entanglement_level / 100
            quantum_factor = np.sin(np.pi * entanglement_factor) ** 2
            
            # Calculate final score
            score = (cpu_score + mem_score + io_score) * quantum_factor
            return score * 100  # Convert to percentage
            
        except Exception as e:
            logger.error(f"Error calculating quantum score: {str(e)}")
            return 0.0 
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import torch
import torch.nn as nn
import torch.optim as optim
from river import drift, anomaly, linear_model
from river.stream import iter_array

logger = logging.getLogger(__name__)

@dataclass
class ProcessFeatures:
    pid: int
    cpu_usage: float
    memory_usage: float
    io_usage: float
    thread_count: int
    priority: float
    timestamp: datetime

class ProcessPredictor(nn.Module):
    def __init__(self, input_size: int = 5, hidden_size: int = 64):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers=2, batch_first=True)
        self.fc = nn.Linear(hidden_size, 3)  # Predict CPU, memory, and I/O usage
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        return self.fc(lstm_out[:, -1, :])

class ContinualLearner:
    def __init__(self):
        self.process_predictors: Dict[int, ProcessPredictor] = {}
        self.optimizers: Dict[int, optim.Adam] = {}
        self.feature_history: Dict[int, List[ProcessFeatures]] = {}
        self.drift_detector = drift.ADWIN()
        self.anomaly_detector = anomaly.HalfSpaceTrees()
        
        # Initialize learning parameters
        self.learning_rate = 0.001
        self.batch_size = 32
        self.sequence_length = 10
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"ContinualLearner initialized on device: {self.device}")
        
    def update(self, system_metrics):
        """Update models with new system metrics"""
        try:
            # Extract features from system metrics
            for proc in system_metrics.processes:
                features = self._extract_features(proc, system_metrics)
                self._update_process_model(proc.pid, features)
                
            # Check for concept drift
            self._detect_drift(system_metrics)
            
            # Detect anomalies
            self._detect_anomalies(system_metrics)
            
        except Exception as e:
            logger.error(f"Error in ContinualLearner update: {str(e)}")
            
    def _extract_features(self, proc, system_metrics) -> ProcessFeatures:
        """Extract features from process metrics"""
        return ProcessFeatures(
            pid=proc.pid,
            cpu_usage=proc.cpu_percent,
            memory_usage=proc.memory_percent,
            io_usage=proc.io_counters['read_bytes'] + proc.io_counters['write_bytes'] if proc.io_counters else 0,
            thread_count=proc.thread_count,
            priority=proc.priority,
            timestamp=system_metrics.timestamp
        )
        
    def _update_process_model(self, pid: int, features: ProcessFeatures):
        """Update or create model for a specific process"""
        try:
            # Initialize model if needed
            if pid not in self.process_predictors:
                self.process_predictors[pid] = ProcessPredictor().to(self.device)
                self.optimizers[pid] = optim.Adam(
                    self.process_predictors[pid].parameters(),
                    lr=self.learning_rate
                )
                self.feature_history[pid] = []
                
            # Update feature history
            self.feature_history[pid].append(features)
            if len(self.feature_history[pid]) > self.sequence_length:
                self.feature_history[pid].pop(0)
                
            # Train model if we have enough data
            if len(self.feature_history[pid]) >= self.sequence_length:
                self._train_process_model(pid)
                
        except Exception as e:
            logger.error(f"Error updating model for process {pid}: {str(e)}")
            
    def _train_process_model(self, pid: int):
        """Train the model for a specific process"""
        try:
            # Prepare training data
            features = self.feature_history[pid]
            input_data = torch.tensor([
                [
                    f.cpu_usage,
                    f.memory_usage,
                    f.io_usage,
                    f.thread_count,
                    f.priority
                ] for f in features
            ], dtype=torch.float32).to(self.device)
            
            # Get target values (next state)
            target_data = torch.tensor([
                [
                    features[i+1].cpu_usage,
                    features[i+1].memory_usage,
                    features[i+1].io_usage
                ] for i in range(len(features)-1)
            ], dtype=torch.float32).to(self.device)
            
            # Train model
            self.process_predictors[pid].train()
            self.optimizers[pid].zero_grad()
            
            # Forward pass
            output = self.process_predictors[pid](input_data.unsqueeze(0))
            loss = nn.MSELoss()(output, target_data[-1].unsqueeze(0))
            
            # Backward pass
            loss.backward()
            self.optimizers[pid].step()
            
        except Exception as e:
            logger.error(f"Error training model for process {pid}: {str(e)}")
            
    def _detect_drift(self, system_metrics):
        """Detect concept drift in system behavior"""
        try:
            # Prepare drift detection data
            drift_data = np.array([
                system_metrics.cpu_percent,
                system_metrics.memory_percent,
                system_metrics.context_switches,
                system_metrics.interrupts
            ])
            
            # Update drift detector
            self.drift_detector.update(drift_data)
            
            # Check for drift
            if self.drift_detector.drift_detected:
                logger.info("Concept drift detected in system behavior")
                self._handle_drift()
                
        except Exception as e:
            logger.error(f"Error in drift detection: {str(e)}")
            
    def _detect_anomalies(self, system_metrics):
        """Detect anomalies in system behavior"""
        try:
            # Prepare anomaly detection data
            anomaly_data = np.array([
                system_metrics.cpu_percent,
                system_metrics.memory_percent,
                system_metrics.context_switches,
                system_metrics.interrupts
            ])
            
            # Update anomaly detector
            self.anomaly_detector.learn_one(anomaly_data)
            score = self.anomaly_detector.score_one(anomaly_data)
            
            # Check for anomalies
            if score > 0.8:  # High anomaly score threshold
                logger.warning(f"Anomaly detected in system behavior (score: {score})")
                self._handle_anomaly(anomaly_data)
                
        except Exception as e:
            logger.error(f"Error in anomaly detection: {str(e)}")
            
    def _handle_drift(self):
        """Handle detected concept drift"""
        try:
            # Reset models for all processes
            for pid in self.process_predictors:
                self.process_predictors[pid] = ProcessPredictor().to(self.device)
                self.optimizers[pid] = optim.Adam(
                    self.process_predictors[pid].parameters(),
                    lr=self.learning_rate
                )
                self.feature_history[pid].clear()
                
            logger.info("Models reset after concept drift")
            
        except Exception as e:
            logger.error(f"Error handling drift: {str(e)}")
            
    def _handle_anomaly(self, anomaly_data):
        """Handle detected anomaly"""
        try:
            # Log anomaly details
            logger.warning(f"Anomaly detected with values: {anomaly_data}")
            
            # Adjust learning rate temporarily
            self.learning_rate *= 2.0
            for optimizer in self.optimizers.values():
                for param_group in optimizer.param_groups:
                    param_group['lr'] = self.learning_rate
                    
            logger.info("Learning rate adjusted after anomaly detection")
            
        except Exception as e:
            logger.error(f"Error handling anomaly: {str(e)}")
            
    def predict_process_metrics(self, pid: int) -> Optional[Dict[str, float]]:
        """Predict future metrics for a specific process"""
        try:
            if pid not in self.process_predictors or not self.feature_history[pid]:
                return None
                
            # Prepare input data
            features = self.feature_history[pid]
            input_data = torch.tensor([
                [
                    f.cpu_usage,
                    f.memory_usage,
                    f.io_usage,
                    f.thread_count,
                    f.priority
                ] for f in features
            ], dtype=torch.float32).to(self.device)
            
            # Make prediction
            self.process_predictors[pid].eval()
            with torch.no_grad():
                prediction = self.process_predictors[pid](input_data.unsqueeze(0))
                
            return {
                'cpu_usage': prediction[0][0].item(),
                'memory_usage': prediction[0][1].item(),
                'io_usage': prediction[0][2].item()
            }
            
        except Exception as e:
            logger.error(f"Error predicting metrics for process {pid}: {str(e)}")
            return None
            
    def get_model_history(self, pid: int) -> List[ProcessFeatures]:
        """Get the feature history for a specific process"""
        return self.feature_history.get(pid, []) 
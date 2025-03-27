import sys
import logging
from PyQt5.QtWidgets import QApplication
from gui.nexus.main_window import MainWindow
from utils.metrics import MetricsCollector, PerformanceAnalyzer
from utils.process_manager import ProcessManager
from utils.ai_manager import AIManager
from utils.quantum_scheduler import QuantumScheduler
from utils.quantum_entanglement import QuantumEntanglement

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        
        # Initialize components
        metrics_collector = MetricsCollector()
        performance_analyzer = PerformanceAnalyzer()
        process_manager = ProcessManager()
        ai_manager = AIManager()
        quantum_scheduler = QuantumScheduler()
        quantum_entanglement = QuantumEntanglement()
        
        # Create and show main window
        window = MainWindow(
            process_manager=process_manager,
            ai_manager=ai_manager,
            metrics_collector=metrics_collector,
            performance_analyzer=performance_analyzer,
            quantum_scheduler=quantum_scheduler,
            quantum_entanglement=quantum_entanglement
        )
        window.show()
        
        # Start event loop
        sys.exit(app.exec_())
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
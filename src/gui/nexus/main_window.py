import logging
from typing import Dict, List, Optional
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QLabel, QPushButton, QSlider, QComboBox, QTabWidget,
                           QTableWidget, QTableWidgetItem, QProgressBar,
                           QGroupBox, QSpinBox, QCheckBox, QGridLayout, QLineEdit,
                           QHeaderView, QDialog)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtOpenGL import QGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
import sys
import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

logger = logging.getLogger(__name__)

class ResourceSphere(QGLWidget):
    """3D resource sphere visualization"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.processes = []
        self.sphere_radius = 5.0
        self.rotation = 0.0
        
    def initializeGL(self):
        """Initialize OpenGL settings"""
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        
    def resizeGL(self, width, height):
        """Handle window resize events"""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, width / height, 0.1, 100.0)
        
    def paintGL(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0.0, 0.0, -20.0)
        glRotatef(self.rotation, 0.0, 1.0, 0.0)
        
        # Draw processes as spheres
        for process in self.processes:
            self._draw_process(process)
            
        # Update rotation
        self.rotation += 0.5
        if self.rotation >= 360.0:
            self.rotation = 0.0
            
    def _draw_process(self, process):
        """Draw a single process as a sphere"""
        x, y, z = self._calculate_process_position(process)
        r, g, b = self._calculate_process_color(process)
        
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(r, g, b)
        
        # Draw sphere
        quad = gluNewQuadric()
        gluSphere(quad, 0.5, 16, 16)
        gluDeleteQuadric(quad)
        
        glPopMatrix()
        
    def _calculate_process_position(self, process):
        """Calculate 3D position based on process metrics"""
        cpu = process.get('cpu_percent', 0) / 100.0
        mem = process.get('memory_percent', 0) / 100.0
        io = process.get('io_rate', 0) / 1000000.0  # Normalize IO rate
        
        # Convert to spherical coordinates
        theta = 2 * np.pi * cpu
        phi = np.pi * mem
        r = self.sphere_radius * (0.5 + 0.5 * io)
        
        # Convert to Cartesian coordinates
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        
        return x, y, z
        
    def _calculate_process_color(self, process):
        """Calculate process color based on metrics"""
        cpu = process.get('cpu_percent', 0) / 100.0
        mem = process.get('memory_percent', 0) / 100.0
        io = process.get('io_rate', 0) / 1000000.0
        
        # Red component based on CPU usage
        r = min(1.0, cpu)
        
        # Green component based on memory usage
        g = min(1.0, 1.0 - mem)
        
        # Blue component based on IO rate
        b = min(1.0, 1.0 - io)
        
        return r, g, b
        
    def update_processes(self, processes):
        """Update process data"""
        self.processes = processes
        self.updateGL()

class PerformanceGraph(FigureCanvas):
    """Performance metrics graph widget"""
    
    def __init__(self, parent=None, width=6, height=4, title="", color='#00ff9d'):
        # Create figure with higher DPI for better quality
        fig = Figure(figsize=(width, height), dpi=100, facecolor='#2d2d2d')
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        
        # Initialize data storage
        self.data = []
        self.timestamps = []
        self.max_points = 60  # Show last 60 seconds
        self.color = color
        self.title = title
        
        # Set style for better visibility
        self.figure.patch.set_facecolor('#2d2d2d')
        self.axes.set_facecolor('#2d2d2d')
        self.axes.grid(True, linestyle='--', alpha=0.3, color='#444')
        
        # Customize appearance
        self.axes.set_title(title, color='#ffffff', pad=10, fontsize=12, fontweight='bold')
        self.axes.tick_params(colors='#ffffff')
        self.axes.spines['bottom'].set_color('#444')
        self.axes.spines['top'].set_color('#444')
        self.axes.spines['left'].set_color('#444')
        self.axes.spines['right'].set_color('#444')
        
        # Enable interactive mode for smoother updates
        self.figure.set_tight_layout(True)
        
    def update_data(self, value):
        """Update graph with new data point"""
        current_time = datetime.now()
        
        # Update data storage
        self.timestamps.append(current_time)
        self.data.append(value)
        
        # Keep only last N points
        if len(self.timestamps) > self.max_points:
            self.timestamps.pop(0)
            self.data.pop(0)
        
        self._plot_data()
        
    def _plot_data(self):
        """Plot the performance data"""
        self.axes.clear()
        
        # Plot data with gradient fill
        self.axes.plot(self.timestamps, self.data, color=self.color, linewidth=2)
        self.axes.fill_between(self.timestamps, self.data, alpha=0.2, color=self.color)
        
        # Add warning thresholds
        self.axes.axhline(y=80, color='#ffd700', linestyle='--', alpha=0.5, label='Warning')
        self.axes.axhline(y=90, color='#ff6b6b', linestyle='--', alpha=0.5, label='Critical')
        
        # Customize appearance
        self.axes.set_ylim(0, 100)
        self.axes.set_ylabel('Usage %', color='#ffffff', fontsize=10, fontweight='bold')
        
        # Format x-axis
        self.axes.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.axes.tick_params(axis='x', rotation=45, colors='#ffffff')
        
        # Add current value as annotation
        if self.data:
            current_value = self.data[-1]
            self.axes.annotate(
                f'{current_value:.1f}%',
                xy=(self.timestamps[-1], current_value),
                xytext=(5, 5), textcoords='offset points',
                color=self.color,
                fontsize=12,
                fontweight='bold'
            )
        
        self.figure.tight_layout()
        self.draw()

class SystemHealthWidget(QWidget):
    """System health monitoring widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        
        # Health indicators
        health_group = QGroupBox("System Health")
        health_layout = QGridLayout()
        
        # CPU Health
        self.cpu_health = QProgressBar()
        self.cpu_health.setStyleSheet(self._get_progress_style())
        health_layout.addWidget(QLabel("CPU Health:"), 0, 0)
        health_layout.addWidget(self.cpu_health, 0, 1)
        
        # Memory Health
        self.mem_health = QProgressBar()
        self.mem_health.setStyleSheet(self._get_progress_style())
        health_layout.addWidget(QLabel("Memory Health:"), 1, 0)
        health_layout.addWidget(self.mem_health, 1, 1)
        
        # Disk Health
        self.disk_health = QProgressBar()
        self.disk_health.setStyleSheet(self._get_progress_style())
        health_layout.addWidget(QLabel("Disk Health:"), 2, 0)
        health_layout.addWidget(self.disk_health, 2, 1)
        
        # Network Health
        self.network_health = QProgressBar()
        self.network_health.setStyleSheet(self._get_progress_style())
        health_layout.addWidget(QLabel("Network Health:"), 3, 0)
        health_layout.addWidget(self.network_health, 3, 1)
        
        health_group.setLayout(health_layout)
        layout.addWidget(health_group)
        
        # System status
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout()
        
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(3)
        self.status_table.setHorizontalHeaderLabels(["Component", "Status", "Details"])
        self.status_table.horizontalHeader().setStretchLastSection(True)
        status_layout.addWidget(self.status_table)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
    def _get_progress_style(self):
        """Get custom progress bar style"""
        return """
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #00ff9d;
            }
        """
        
    def update_health(self, metrics):
        """Update health indicators with new metrics"""
        # Update progress bars
        self.cpu_health.setValue(int(100 - metrics['cpu_percent']))
        self.mem_health.setValue(int(100 - metrics['memory_percent']))
        self.disk_health.setValue(int(100 - metrics.get('disk_usage', 0)))
        self.network_health.setValue(int(100 - metrics.get('network_usage', 0)))
        
        # Update status table
        self.status_table.setRowCount(4)
        
        # CPU Status
        self.status_table.setItem(0, 0, QTableWidgetItem("CPU"))
        self.status_table.setItem(0, 1, QTableWidgetItem(self._get_status_text(metrics['cpu_percent'])))
        self.status_table.setItem(0, 2, QTableWidgetItem(f"Usage: {metrics['cpu_percent']:.1f}%"))
        
        # Memory Status
        self.status_table.setItem(1, 0, QTableWidgetItem("Memory"))
        self.status_table.setItem(1, 1, QTableWidgetItem(self._get_status_text(metrics['memory_percent'])))
        self.status_table.setItem(1, 2, QTableWidgetItem(f"Usage: {metrics['memory_percent']:.1f}%"))
        
        # Disk Status
        self.status_table.setItem(2, 0, QTableWidgetItem("Disk"))
        self.status_table.setItem(2, 1, QTableWidgetItem(self._get_status_text(metrics.get('disk_usage', 0))))
        self.status_table.setItem(2, 2, QTableWidgetItem(f"Usage: {metrics.get('disk_usage', 0):.1f}%"))
        
        # Network Status
        self.status_table.setItem(3, 0, QTableWidgetItem("Network"))
        self.status_table.setItem(3, 1, QTableWidgetItem(self._get_status_text(metrics.get('network_usage', 0))))
        self.status_table.setItem(3, 2, QTableWidgetItem(f"Usage: {metrics.get('network_usage', 0):.1f}%"))
        
    def _get_status_text(self, usage):
        """Get status text based on usage percentage"""
        if usage < 70:
            return "Healthy"
        elif usage < 85:
            return "Warning"
        else:
            return "Critical"

class MainWindow(QMainWindow):
    """Industrial System Monitor Window"""
    
    def __init__(self, process_manager, ai_manager, metrics_collector,
                 performance_analyzer, quantum_scheduler, quantum_entanglement):
        super().__init__()
        self.process_manager = process_manager
        self.ai_manager = ai_manager
        self.metrics_collector = metrics_collector
        self.performance_analyzer = performance_analyzer
        self.quantum_scheduler = quantum_scheduler
        self.quantum_entanglement = quantum_entanglement
        
        # Set window properties
        self.setWindowTitle("Industrial System Monitor")
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #333;
                background-color: #1a1a1a;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 12px 24px;
                border: 1px solid #333;
                border-bottom: none;
                font-size: 14px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #3d3d3d;
                border-bottom: 3px solid #00ff00;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #333;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                border-color: #00ff00;
            }
            QPushButton:pressed {
                background-color: #4d4d4d;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
            }
            QTableWidget {
                background-color: #1a1a1a;
                color: #ffffff;
                gridline-color: #333;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 5px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            QTableWidget::item:selected {
                background-color: #3d3d3d;
                color: #00ff00;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 10px;
                border: 1px solid #333;
                font-weight: bold;
                font-size: 13px;
            }
            QProgressBar {
                border: 1px solid #333;
                border-radius: 6px;
                text-align: center;
                background-color: #1a1a1a;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #00ff00;
                border-radius: 5px;
            }
            QGroupBox {
                border: 1px solid #333;
                border-radius: 8px;
                margin-top: 1.5em;
                padding: 15px;
                background-color: #1a1a1a;
                font-size: 14px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QSpinBox, QComboBox, QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #333;
                padding: 8px;
                border-radius: 6px;
                font-size: 13px;
                min-height: 25px;
            }
            QSpinBox:hover, QComboBox:hover, QLineEdit:hover {
                border-color: #00ff00;
            }
            QCheckBox {
                color: #ffffff;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #00ff00;
                border: 1px solid #00ff00;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #1a1a1a;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #3d3d3d;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #4d4d4d;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Create header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add logo/title
        title_label = QLabel("Industrial System Monitor")
        title_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #00ff00;
            padding: 10px;
        """)
        header_layout.addWidget(title_label)
        
        # Add status indicators
        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setSpacing(20)
        
        self.system_status = QLabel("System Status: Active")
        self.system_status.setStyleSheet("color: #00ff00; font-weight: bold;")
        status_layout.addWidget(self.system_status)
        
        self.last_update = QLabel("Last Update: Just now")
        status_layout.addWidget(self.last_update)
        
        header_layout.addStretch()
        header_layout.addWidget(status_widget)
        
        layout.addWidget(header)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.tab_widget.addTab(self._create_monitoring_tab(), "Industrial Dashboard")
        self.tab_widget.addTab(self._create_process_tab(), "Process Control")
        self.tab_widget.addTab(self._create_health_tab(), "System Health")
        self.tab_widget.addTab(self._create_optimization_tab(), "Performance Optimization")
        self.tab_widget.addTab(self._create_network_tab(), "Network Analysis")
        self.tab_widget.addTab(self._create_diagnostics_tab(), "System Diagnostics")
        
        # Set up update timer with faster refresh rate
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_metrics)
        self.update_timer.start(500)  # Update every 500ms for faster response
        
        logger.info("Industrial System Monitor initialized")
        
    def _create_monitoring_tab(self):
        """Create the real-time monitoring tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Create grid layout for graphs
        graph_grid = QGridLayout()
        graph_grid.setSpacing(15)
        
        # CPU Usage Graph
        cpu_group = QGroupBox("CPU Usage")
        cpu_layout = QVBoxLayout()
        self.cpu_graph = PerformanceGraph(title="CPU Usage", color='#00ff9d')
        cpu_layout.addWidget(self.cpu_graph)
        cpu_group.setLayout(cpu_layout)
        graph_grid.addWidget(cpu_group, 0, 0)
        
        # Memory Usage Graph
        mem_group = QGroupBox("Memory Usage")
        mem_layout = QVBoxLayout()
        self.memory_graph = PerformanceGraph(title="Memory Usage", color='#ff6b6b')
        mem_layout.addWidget(self.memory_graph)
        mem_group.setLayout(mem_layout)
        graph_grid.addWidget(mem_group, 0, 1)
        
        # Disk Usage Graph
        disk_group = QGroupBox("Disk Usage")
        disk_layout = QVBoxLayout()
        self.disk_graph = PerformanceGraph(title="Disk Usage", color='#4ecdc4')
        disk_layout.addWidget(self.disk_graph)
        disk_group.setLayout(disk_layout)
        graph_grid.addWidget(disk_group, 1, 0)
        
        # Network Usage Graph
        net_group = QGroupBox("Network Usage")
        net_layout = QVBoxLayout()
        self.network_graph = PerformanceGraph(title="Network Usage", color='#45b7d1')
        net_layout.addWidget(self.network_graph)
        net_group.setLayout(net_layout)
        graph_grid.addWidget(net_group, 1, 1)
        
        layout.addLayout(graph_grid)
        
        # Add current metrics display with modern styling
        metrics_group = QGroupBox("Current Metrics")
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(20)
        
        # CPU Usage
        cpu_metric = QWidget()
        cpu_metric_layout = QVBoxLayout()
        self.cpu_label = QLabel("CPU Usage")
        self.cpu_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #00ff9d;
            padding: 5px;
        """)
        self.cpu_value = QLabel("0%")
        self.cpu_value.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
            padding: 5px;
        """)
        cpu_metric_layout.addWidget(self.cpu_label)
        cpu_metric_layout.addWidget(self.cpu_value)
        cpu_metric.setLayout(cpu_metric_layout)
        metrics_layout.addWidget(cpu_metric, 0, 0)
        
        # Memory Usage
        mem_metric = QWidget()
        mem_metric_layout = QVBoxLayout()
        self.memory_label = QLabel("Memory Usage")
        self.memory_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #ff6b6b;
            padding: 5px;
        """)
        self.memory_value = QLabel("0%")
        self.memory_value.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
            padding: 5px;
        """)
        mem_metric_layout.addWidget(self.memory_label)
        mem_metric_layout.addWidget(self.memory_value)
        mem_metric.setLayout(mem_metric_layout)
        metrics_layout.addWidget(mem_metric, 0, 1)
        
        # Disk Usage
        disk_metric = QWidget()
        disk_metric_layout = QVBoxLayout()
        self.disk_label = QLabel("Disk Usage")
        self.disk_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #4ecdc4;
            padding: 5px;
        """)
        self.disk_value = QLabel("0%")
        self.disk_value.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
            padding: 5px;
        """)
        disk_metric_layout.addWidget(self.disk_label)
        disk_metric_layout.addWidget(self.disk_value)
        disk_metric.setLayout(disk_metric_layout)
        metrics_layout.addWidget(disk_metric, 1, 0)
        
        # Network Usage
        net_metric = QWidget()
        net_metric_layout = QVBoxLayout()
        self.network_label = QLabel("Network Usage")
        self.network_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #45b7d1;
            padding: 5px;
        """)
        self.network_value = QLabel("0%")
        self.network_value.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
            padding: 5px;
        """)
        net_metric_layout.addWidget(self.network_label)
        net_metric_layout.addWidget(self.network_value)
        net_metric.setLayout(net_metric_layout)
        metrics_layout.addWidget(net_metric, 1, 1)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        return widget
        
    def _create_process_tab(self):
        """Create the industrial process control tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Add search bar with modern styling
        search_group = QGroupBox("Process Search")
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        search_label = QLabel("Search:")
        search_label.setStyleSheet("font-weight: bold;")
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Enter process name...")
        self.search_box.textChanged.connect(self._filter_processes)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_box)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Process table with industrial columns
        table_group = QGroupBox("Process List")
        table_layout = QVBoxLayout()
        
        self.process_table = QTableWidget()
        self.process_table.setColumnCount(8)
        self.process_table.setHorizontalHeaderLabels([
            "PID", "Name", "Type", "Criticality", "CPU %", "Memory %", "Response Time", "Status"
        ])
        self.process_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.process_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.process_table.setSortingEnabled(True)
        table_layout.addWidget(self.process_table)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Process controls with modern styling
        controls_group = QGroupBox("Process Controls")
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)
        
        # Priority adjustment
        priority_widget = QWidget()
        priority_layout = QHBoxLayout()
        priority_layout.setSpacing(10)
        priority_label = QLabel("Priority:")
        priority_label.setStyleSheet("font-weight: bold;")
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Critical", "High", "Normal", "Low"])
        priority_layout.addWidget(priority_label)
        priority_layout.addWidget(self.priority_combo)
        priority_widget.setLayout(priority_layout)
        controls_layout.addWidget(priority_widget)
        
        # Add buttons with modern styling
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self._update_process_list)
        controls_layout.addWidget(self.refresh_btn)
        
        self.optimize_btn = QPushButton("⚡ Optimize Selected")
        self.optimize_btn.clicked.connect(self._optimize_selected_processes)
        controls_layout.addWidget(self.optimize_btn)
        
        self.terminate_btn = QPushButton("❌ Terminate Selected")
        self.terminate_btn.clicked.connect(self._terminate_selected_processes)
        controls_layout.addWidget(self.terminate_btn)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        return widget
        
    def _create_health_tab(self):
        """Create the system health tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # System health widget
        self.system_health = SystemHealthWidget()
        layout.addWidget(self.system_health)
        
        # Add AI predictions
        predictions_group = QGroupBox("AI Predictions")
        pred_layout = QVBoxLayout()
        self.predictions_label = QLabel("Loading predictions...")
        self.predictions_label.setStyleSheet("font-size: 12px;")
        pred_layout.addWidget(self.predictions_label)
        predictions_group.setLayout(pred_layout)
        layout.addWidget(predictions_group)
        
        return widget
        
    def _create_optimization_tab(self) -> QWidget:
        """Create system optimization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # CPU Optimization Section
        cpu_group = QGroupBox("CPU Optimization")
        cpu_layout = QVBoxLayout()
        
        # CPU Usage Analysis
        self.cpu_analysis = QLabel()
        cpu_layout.addWidget(self.cpu_analysis)
        
        # CPU Optimization Suggestions
        self.cpu_suggestions = QTableWidget()
        self.cpu_suggestions.setColumnCount(2)
        self.cpu_suggestions.setHorizontalHeaderLabels(["Suggestion", "Impact"])
        self.cpu_suggestions.horizontalHeader().setStretchLastSection(True)
        cpu_layout.addWidget(self.cpu_suggestions)
        
        # CPU Optimization Actions
        cpu_actions = QHBoxLayout()
        optimize_cpu_btn = QPushButton("Optimize CPU Usage")
        optimize_cpu_btn.clicked.connect(self._optimize_cpu)
        cpu_actions.addWidget(optimize_cpu_btn)
        cpu_layout.addLayout(cpu_actions)
        
        cpu_group.setLayout(cpu_layout)
        layout.addWidget(cpu_group)
        
        # Memory Optimization Section
        mem_group = QGroupBox("Memory Optimization")
        mem_layout = QVBoxLayout()
        
        # Memory Usage Analysis
        self.mem_analysis = QLabel()
        mem_layout.addWidget(self.mem_analysis)
        
        # Memory Optimization Suggestions
        self.mem_suggestions = QTableWidget()
        self.mem_suggestions.setColumnCount(2)
        self.mem_suggestions.setHorizontalHeaderLabels(["Suggestion", "Impact"])
        self.mem_suggestions.horizontalHeader().setStretchLastSection(True)
        mem_layout.addWidget(self.mem_suggestions)
        
        # Memory Optimization Actions
        mem_actions = QHBoxLayout()
        optimize_mem_btn = QPushButton("Optimize Memory Usage")
        optimize_mem_btn.clicked.connect(self._optimize_memory)
        mem_actions.addWidget(optimize_mem_btn)
        mem_layout.addLayout(mem_actions)
        
        mem_group.setLayout(mem_layout)
        layout.addWidget(mem_group)
        
        # System Recommendations
        rec_group = QGroupBox("System Recommendations")
        rec_layout = QVBoxLayout()
        
        self.recommendations = QTableWidget()
        self.recommendations.setColumnCount(3)
        self.recommendations.setHorizontalHeaderLabels(["Category", "Recommendation", "Priority"])
        self.recommendations.horizontalHeader().setStretchLastSection(True)
        rec_layout.addWidget(self.recommendations)
        
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)
        
        return tab
        
    def _create_network_tab(self) -> QWidget:
        """Create network analysis tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Network Overview
        overview_group = QGroupBox("Network Overview")
        overview_layout = QGridLayout()
        
        # Network Usage Graph
        self.network_graph = PerformanceGraph(title="Network Usage", color='#00ffff')
        overview_layout.addWidget(self.network_graph, 0, 0, 1, 2)
        
        # Network Stats
        self.network_stats = QTableWidget()
        self.network_stats.setColumnCount(2)
        self.network_stats.setHorizontalHeaderLabels(["Metric", "Value"])
        self.network_stats.horizontalHeader().setStretchLastSection(True)
        overview_layout.addWidget(self.network_stats, 1, 0, 1, 2)
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # Network Connections
        connections_group = QGroupBox("Active Connections")
        connections_layout = QVBoxLayout()
        
        self.connections_table = QTableWidget()
        self.connections_table.setColumnCount(5)
        self.connections_table.setHorizontalHeaderLabels(
            ["Protocol", "Local Address", "Remote Address", "Status", "Process"]
        )
        self.connections_table.horizontalHeader().setStretchLastSection(True)
        connections_layout.addWidget(self.connections_table)
        
        connections_group.setLayout(connections_layout)
        layout.addWidget(connections_group)
        
        return tab
        
    def _create_diagnostics_tab(self) -> QWidget:
        """Create system diagnostics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Diagnostics
        diag_group = QGroupBox("System Diagnostics")
        diag_layout = QVBoxLayout()
        
        # Diagnostic Tests
        self.diagnostic_tests = QTableWidget()
        self.diagnostic_tests.setColumnCount(4)
        self.diagnostic_tests.setHorizontalHeaderLabels(
            ["Test", "Status", "Result", "Details"]
        )
        self.diagnostic_tests.horizontalHeader().setStretchLastSection(True)
        diag_layout.addWidget(self.diagnostic_tests)
        
        # Run Diagnostics Button
        run_diag_btn = QPushButton("Run Diagnostics")
        run_diag_btn.clicked.connect(self._run_diagnostics)
        diag_layout.addWidget(run_diag_btn)
        
        diag_group.setLayout(diag_layout)
        layout.addWidget(diag_group)
        
        # Performance Analysis
        perf_group = QGroupBox("Performance Analysis")
        perf_layout = QVBoxLayout()
        
        self.performance_analysis = QTableWidget()
        self.performance_analysis.setColumnCount(3)
        self.performance_analysis.setHorizontalHeaderLabels(
            ["Component", "Score", "Recommendations"]
        )
        self.performance_analysis.horizontalHeader().setStretchLastSection(True)
        perf_layout.addWidget(self.performance_analysis)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        return tab
        
    def _optimize_cpu(self):
        """Optimize CPU usage"""
        try:
            # Get current metrics
            metrics = self.metrics_collector.get_metrics()
            if not metrics:
                return
                
            # Analyze CPU usage
            cpu_percent = metrics.get('cpu_percent', 0)
            
            # Generate optimization suggestions
            suggestions = []
            if cpu_percent > 80:
                suggestions.append(("Reduce background processes", "High"))
                suggestions.append(("Optimize running applications", "Medium"))
            elif cpu_percent > 60:
                suggestions.append(("Monitor resource-intensive apps", "Medium"))
                suggestions.append(("Consider process prioritization", "Low"))
                
            # Update suggestions table
            self.cpu_suggestions.setRowCount(len(suggestions))
            for i, (suggestion, impact) in enumerate(suggestions):
                self.cpu_suggestions.setItem(i, 0, QTableWidgetItem(suggestion))
                self.cpu_suggestions.setItem(i, 1, QTableWidgetItem(impact))
                
            # Apply optimizations
            self.process_manager.optimize_cpu_usage()
            
        except Exception as e:
            logger.error(f"Error optimizing CPU: {str(e)}")
            
    def _optimize_memory(self):
        """Optimize memory usage"""
        try:
            # Get current metrics
            metrics = self.metrics_collector.get_metrics()
            if not metrics:
                return
                
            # Analyze memory usage
            memory_percent = metrics.get('memory_percent', 0)
            
            # Generate optimization suggestions
            suggestions = []
            if memory_percent > 80:
                suggestions.append(("Close unnecessary applications", "High"))
                suggestions.append(("Clear system cache", "Medium"))
            elif memory_percent > 60:
                suggestions.append(("Monitor memory-intensive apps", "Medium"))
                suggestions.append(("Consider increasing swap space", "Low"))
                
            # Update suggestions table
            self.mem_suggestions.setRowCount(len(suggestions))
            for i, (suggestion, impact) in enumerate(suggestions):
                self.mem_suggestions.setItem(i, 0, QTableWidgetItem(suggestion))
                self.mem_suggestions.setItem(i, 1, QTableWidgetItem(impact))
                
            # Apply optimizations
            self.process_manager.optimize_memory_usage()
            
        except Exception as e:
            logger.error(f"Error optimizing memory: {str(e)}")
            
    def _run_diagnostics(self):
        """Run system diagnostics"""
        try:
            # Clear previous results
            self.diagnostic_tests.setRowCount(0)
            
            # Run CPU diagnostics
            cpu_test = self._run_cpu_diagnostics()
            self._add_diagnostic_result("CPU Test", cpu_test)
            
            # Run Memory diagnostics
            mem_test = self._run_memory_diagnostics()
            self._add_diagnostic_result("Memory Test", mem_test)
            
            # Run Disk diagnostics
            disk_test = self._run_disk_diagnostics()
            self._add_diagnostic_result("Disk Test", disk_test)
            
            # Update performance analysis
            self._update_performance_analysis()
            
            # Show reward/suggestion dialog
            self._show_diagnostic_results()
            
        except Exception as e:
            logger.error(f"Error running diagnostics: {str(e)}")
            
    def _run_cpu_diagnostics(self) -> Dict:
        """Run CPU diagnostics"""
        try:
            metrics = self.metrics_collector.get_metrics()
            if not metrics:
                return {'status': 'Failed', 'result': 'N/A', 'details': 'No metrics available'}
                
            cpu_percent = metrics.get('cpu_percent', 0)
            
            if cpu_percent > 90:
                return {
                    'status': 'Warning',
                    'result': 'High CPU Usage',
                    'details': f'CPU usage at {cpu_percent:.1f}%'
                }
            elif cpu_percent > 70:
                return {
                    'status': 'Caution',
                    'result': 'Moderate CPU Usage',
                    'details': f'CPU usage at {cpu_percent:.1f}%'
                }
            else:
                return {
                    'status': 'OK',
                    'result': 'Normal CPU Usage',
                    'details': f'CPU usage at {cpu_percent:.1f}%'
                }
                
        except Exception as e:
            return {'status': 'Error', 'result': 'Failed', 'details': str(e)}
            
    def _run_memory_diagnostics(self) -> Dict:
        """Run memory diagnostics"""
        try:
            metrics = self.metrics_collector.get_metrics()
            if not metrics:
                return {'status': 'Failed', 'result': 'N/A', 'details': 'No metrics available'}
                
            memory_percent = metrics.get('memory_percent', 0)
            
            if memory_percent > 90:
                return {
                    'status': 'Warning',
                    'result': 'High Memory Usage',
                    'details': f'Memory usage at {memory_percent:.1f}%'
                }
            elif memory_percent > 70:
                return {
                    'status': 'Caution',
                    'result': 'Moderate Memory Usage',
                    'details': f'Memory usage at {memory_percent:.1f}%'
                }
            else:
                return {
                    'status': 'OK',
                    'result': 'Normal Memory Usage',
                    'details': f'Memory usage at {memory_percent:.1f}%'
                }
                
        except Exception as e:
            return {'status': 'Error', 'result': 'Failed', 'details': str(e)}
            
    def _run_disk_diagnostics(self) -> Dict:
        """Run disk diagnostics"""
        try:
            metrics = self.metrics_collector.get_metrics()
            if not metrics:
                return {'status': 'Failed', 'result': 'N/A', 'details': 'No metrics available'}
                
            disk_percent = metrics.get('disk_percent', 0)
            
            if disk_percent > 90:
                return {
                    'status': 'Warning',
                    'result': 'High Disk Usage',
                    'details': f'Disk usage at {disk_percent:.1f}%'
                }
            elif disk_percent > 70:
                return {
                    'status': 'Caution',
                    'result': 'Moderate Disk Usage',
                    'details': f'Disk usage at {disk_percent:.1f}%'
                }
            else:
                return {
                    'status': 'OK',
                    'result': 'Normal Disk Usage',
                    'details': f'Disk usage at {disk_percent:.1f}%'
                }
                
        except Exception as e:
            return {'status': 'Error', 'result': 'Failed', 'details': str(e)}
            
    def _update_performance_analysis(self):
        """Update performance analysis table"""
        try:
            # Get performance scores
            scores = self.performance_analyzer.analyze_performance()
            
            # Update table
            self.performance_analysis.setRowCount(len(scores))
            for i, (component, score) in enumerate(scores.items()):
                self.performance_analysis.setItem(i, 0, QTableWidgetItem(component))
                self.performance_analysis.setItem(i, 1, QTableWidgetItem(f"{score:.1f}"))
                
                # Add recommendations based on score
                if score < 60:
                    recommendation = "Critical: Immediate action required"
                elif score < 70:
                    recommendation = "Poor: Consider optimization"
                elif score < 80:
                    recommendation = "Fair: Monitor closely"
                elif score < 90:
                    recommendation = "Good: Regular maintenance"
                else:
                    recommendation = "Excellent: Maintain current state"
                    
                self.performance_analysis.setItem(i, 2, QTableWidgetItem(recommendation))
                
        except Exception as e:
            logger.error(f"Error updating performance analysis: {str(e)}")
        
    def _filter_processes(self):
        """Filter process list based on search text"""
        search_text = self.search_box.text().lower()
        for row in range(self.process_table.rowCount()):
            name_item = self.process_table.item(row, 1)
            if name_item:
                name = name_item.text().lower()
                self.process_table.setRowHidden(row, search_text not in name)
                
    def _update_process_list(self):
        """Update the process list with industrial information"""
        try:
            processes = self.process_manager.get_all_processes()
            
            # Update table
            self.process_table.setSortingEnabled(False)
            self.process_table.setRowCount(len(processes))
            
            for i, process in enumerate(processes):
                pid_item = QTableWidgetItem(str(process.pid))
                name_item = QTableWidgetItem(process.name)
                type_item = QTableWidgetItem(process.process_type)
                criticality_item = QTableWidgetItem(process.criticality)
                cpu_item = QTableWidgetItem(f"{process.cpu_percent:.1f}%")
                mem_item = QTableWidgetItem(f"{process.memory_percent:.1f}%")
                response_item = QTableWidgetItem(f"{process.response_time:.2f}s")
                status_item = QTableWidgetItem(process.status)
                
                # Set colors based on criticality and usage
                if process.criticality == "Critical":
                    criticality_item.setBackground(Qt.red)
                    criticality_item.setForeground(Qt.white)
                elif process.criticality == "High":
                    criticality_item.setBackground(Qt.yellow)
                    criticality_item.setForeground(Qt.black)
                
                if process.cpu_percent > 80:
                    cpu_item.setBackground(Qt.red)
                    cpu_item.setForeground(Qt.white)
                elif process.cpu_percent > 60:
                    cpu_item.setBackground(Qt.yellow)
                    cpu_item.setForeground(Qt.black)
                
                if process.memory_percent > 80:
                    mem_item.setBackground(Qt.red)
                    mem_item.setForeground(Qt.white)
                elif process.memory_percent > 60:
                    mem_item.setBackground(Qt.yellow)
                    mem_item.setForeground(Qt.black)
                
                if process.response_time > 1.0:
                    response_item.setBackground(Qt.red)
                    response_item.setForeground(Qt.white)
                elif process.response_time > 0.5:
                    response_item.setBackground(Qt.yellow)
                    response_item.setForeground(Qt.black)
                
                self.process_table.setItem(i, 0, pid_item)
                self.process_table.setItem(i, 1, name_item)
                self.process_table.setItem(i, 2, type_item)
                self.process_table.setItem(i, 3, criticality_item)
                self.process_table.setItem(i, 4, cpu_item)
                self.process_table.setItem(i, 5, mem_item)
                self.process_table.setItem(i, 6, response_item)
                self.process_table.setItem(i, 7, status_item)
            
            self.process_table.setSortingEnabled(True)
            
        except Exception as e:
            logger.error(f"Error updating process list: {str(e)}")
            
    def _optimize_selected_processes(self):
        """Optimize selected processes with industrial considerations"""
        selected_rows = set(item.row() for item in self.process_table.selectedItems())
        if not selected_rows:
            return
            
        optimization_level = "aggressive" if self.priority_combo.currentText() == "High" else "standard"
        
        for row in selected_rows:
            pid = int(self.process_table.item(row, 0).text())
            criticality = self.process_table.item(row, 3).text()
            
            if criticality != "Critical":  # Don't optimize critical processes
                if self.process_manager.optimize_process(pid, optimization_level):
                    self.process_table.item(row, 7).setText("Optimized")
                    self.process_table.item(row, 7).setBackground(Qt.green)
                    self.process_table.item(row, 7).setForeground(Qt.black)
            
    def _terminate_selected_processes(self):
        """Terminate selected processes with industrial safety checks"""
        selected_rows = self.process_table.selectedItems()
        if not selected_rows:
            return
            
        for item in selected_rows:
            row = item.row()
            pid = int(self.process_table.item(row, 0).text())
            criticality = self.process_table.item(row, 3).text()
            
            if criticality != "Critical":  # Don't terminate critical processes
                self.process_manager.terminate_process(pid)
            
    def _update_metrics(self):
        """Update all metrics and visualizations with improved response time"""
        try:
            # Get current metrics
            metrics = self.metrics_collector.get_metrics()
            if not metrics:
                return
                
            # Update graphs
            self.cpu_graph.update_data(metrics.get('cpu_percent', 0))
            self.memory_graph.update_data(metrics.get('memory_percent', 0))
            self.disk_graph.update_data(metrics.get('disk_usage', 0))
            self.network_graph.update_data(metrics.get('network_usage', 0))
            
            # Update current metrics display
            self.cpu_value.setText(f"{metrics.get('cpu_percent', 0):.1f}%")
            self.memory_value.setText(f"{metrics.get('memory_percent', 0):.1f}%")
            self.disk_value.setText(f"{metrics.get('disk_usage', 0):.1f}%")
            self.network_value.setText(f"{metrics.get('network_usage', 0):.1f}%")
            
            # Update system health widget
            self.system_health.update_health(metrics)
            
            # Update process list
            self._update_process_list()
            
            # Update AI predictions
            predictions = self.ai_manager.predict_performance(metrics)
            if predictions:
                self.predictions_label.setText(
                    f"CPU Health: {predictions['cpu_health']:.1f}%\n"
                    f"Memory Health: {predictions['memory_health']:.1f}%\n"
                    f"Overall Health: {predictions['overall_health']:.1f}%"
                )
                
        except Exception as e:
            logger.error(f"Error updating metrics: {str(e)}")
            
    def closeEvent(self, event):
        """Clean up resources when closing"""
        try:
            # Stop timers
            self.update_timer.stop()
            
            super().closeEvent(event)
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            super().closeEvent(event)

    def _add_diagnostic_result(self, test_name: str, result: Dict):
        """Add a diagnostic result to the table with colors"""
        row = self.diagnostic_tests.rowCount()
        self.diagnostic_tests.insertRow(row)
        
        name_item = QTableWidgetItem(test_name)
        status_item = QTableWidgetItem(result['status'])
        result_item = QTableWidgetItem(result['result'])
        details_item = QTableWidgetItem(result['details'])
        
        # Set colors based on status
        if result['status'] == 'Warning':
            status_item.setBackground(Qt.yellow)
            status_item.setForeground(Qt.black)
        elif result['status'] == 'Critical':
            status_item.setBackground(Qt.red)
            status_item.setForeground(Qt.white)
        elif result['status'] == 'OK':
            status_item.setBackground(Qt.green)
            status_item.setForeground(Qt.black)
            
        self.diagnostic_tests.setItem(row, 0, name_item)
        self.diagnostic_tests.setItem(row, 1, status_item)
        self.diagnostic_tests.setItem(row, 2, result_item)
        self.diagnostic_tests.setItem(row, 3, details_item)
        
    def _show_diagnostic_results(self):
        """Show a dialog with diagnostic results and rewards"""
        try:
            metrics = self.metrics_collector.get_metrics()
            if not metrics:
                return
                
            overall_health = (
                (100 - metrics.get('cpu_percent', 0)) +
                (100 - metrics.get('memory_percent', 0)) +
                (100 - metrics.get('disk_usage', 0))
            ) / 3
            
            message = "System Health Report\n\n"
            
            if overall_health > 80:
                message += "🌟 Excellent System Health! Keep up the good work!\n"
                message += "Your system is running optimally.\n"
            elif overall_health > 60:
                message += "👍 Good System Health\n"
                message += "Some minor optimizations recommended:\n"
                if metrics.get('cpu_percent', 0) > 70:
                    message += "- Consider closing unnecessary CPU-intensive applications\n"
                if metrics.get('memory_percent', 0) > 70:
                    message += "- Free up some memory by closing unused applications\n"
            else:
                message += "⚠️ System Needs Attention\n"
                message += "Recommended actions:\n"
                if metrics.get('cpu_percent', 0) > 80:
                    message += "- Critical: Reduce CPU load immediately\n"
                if metrics.get('memory_percent', 0) > 80:
                    message += "- Critical: Free up memory immediately\n"
                if metrics.get('disk_usage', 0) > 80:
                    message += "- Critical: Clean up disk space\n"
                    
            # Create and show dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Diagnostic Results")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout()
            
            # Add icon based on health
            icon_label = QLabel()
            if overall_health > 80:
                icon_label.setText("🌟")
            elif overall_health > 60:
                icon_label.setText("👍")
            else:
                icon_label.setText("⚠️")
            icon_label.setStyleSheet("font-size: 48px; color: #00ff9d;")
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)
            
            # Add message
            text_label = QLabel(message)
            text_label.setStyleSheet("font-size: 12px; color: #ffffff;")
            text_label.setWordWrap(True)
            layout.addWidget(text_label)
            
            # Add close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.setStyleSheet("""
                QDialog {
                    background-color: #2d2d2d;
                }
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #444;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
            """)
            
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"Error showing diagnostic results: {str(e)}") 
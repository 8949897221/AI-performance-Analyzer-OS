import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import os
from .config_manager import ConfigManager

def setup_logging(log_file: Optional[str] = None) -> None:
    """Setup logging configuration"""
    try:
        # Get configuration
        config = ConfigManager()
        log_config = config.get_section('logging')
        
        # Create logs directory if it doesn't exist
        if log_file is None:
            log_file = log_config.get('file', 'neurapulse.log')
            
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / log_file
        
        # Setup logging format
        formatter = logging.Formatter(log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # Setup file handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=log_config.get('max_size', 10 * 1024 * 1024),  # 10MB default
            backupCount=log_config.get('backup_count', 5)
        )
        file_handler.setFormatter(formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_config.get('level', 'INFO'))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Log startup message
        logging.info("Logging system initialized")
        
    except Exception as e:
        print(f"Error setting up logging: {str(e)}")
        raise

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)

def set_log_level(level: str) -> None:
    """Set the logging level"""
    try:
        level = level.upper()
        if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Invalid log level: {level}")
            
        logging.getLogger().setLevel(level)
        logging.info(f"Log level set to {level}")
        
    except Exception as e:
        logging.error(f"Error setting log level: {str(e)}")
        raise

def add_file_handler(logger: logging.Logger, filename: str) -> None:
    """Add a file handler to a logger"""
    try:
        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        log_path = log_dir / filename
        
        # Get configuration
        config = ConfigManager()
        log_config = config.get_section('logging')
        
        # Create formatter
        formatter = logging.Formatter(log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        # Create and configure file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=log_config.get('max_size', 10 * 1024 * 1024),
            backupCount=log_config.get('backup_count', 5)
        )
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        logger.info(f"Added file handler: {filename}")
        
    except Exception as e:
        logger.error(f"Error adding file handler: {str(e)}")
        raise

def remove_file_handler(logger: logging.Logger, filename: str) -> None:
    """Remove a file handler from a logger"""
    try:
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                if handler.baseFilename.endswith(filename):
                    logger.removeHandler(handler)
                    handler.close()
                    logger.info(f"Removed file handler: {filename}")
                    break
                    
    except Exception as e:
        logger.error(f"Error removing file handler: {str(e)}")
        raise

def clear_handlers(logger: logging.Logger) -> None:
    """Clear all handlers from a logger"""
    try:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        logger.info("Cleared all handlers")
        
    except Exception as e:
        logger.error(f"Error clearing handlers: {str(e)}")
        raise

def setup_performance_logging() -> None:
    """Setup performance-specific logging"""
    try:
        # Get configuration
        config = ConfigManager()
        perf_config = config.get_section('performance')
        
        # Create performance logger
        perf_logger = logging.getLogger('performance')
        perf_logger.setLevel('INFO')
        
        # Add file handler for performance logs
        add_file_handler(perf_logger, 'performance.log')
        
        logging.info("Performance logging initialized")
        
    except Exception as e:
        logging.error(f"Error setting up performance logging: {str(e)}")
        raise

def setup_security_logging() -> None:
    """Setup security-specific logging"""
    try:
        # Get configuration
        config = ConfigManager()
        security_config = config.get_section('security')
        
        # Create security logger
        security_logger = logging.getLogger('security')
        security_logger.setLevel('INFO')
        
        # Add file handler for security logs
        add_file_handler(security_logger, 'security.log')
        
        logging.info("Security logging initialized")
        
    except Exception as e:
        logging.error(f"Error setting up security logging: {str(e)}")
        raise

def setup_network_logging() -> None:
    """Setup network-specific logging"""
    try:
        # Get configuration
        config = ConfigManager()
        network_config = config.get_section('network')
        
        # Create network logger
        network_logger = logging.getLogger('network')
        network_logger.setLevel('INFO')
        
        # Add file handler for network logs
        add_file_handler(network_logger, 'network.log')
        
        logging.info("Network logging initialized")
        
    except Exception as e:
        logging.error(f"Error setting up network logging: {str(e)}")
        raise 
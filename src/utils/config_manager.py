import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import os
import sys

logger = logging.getLogger(__name__)

class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._config:
            self._load_config()
            
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            # Get the base path
            base_path = Path(__file__).parent.parent.parent
            
            # Load default config
            config_path = base_path / 'config' / 'settings.yaml'
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
                
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f)
                
            # Override with environment variables if they exist
            self._load_env_vars()
            
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise
            
    def _load_env_vars(self):
        """Load configuration from environment variables"""
        try:
            # Define environment variable prefixes for each section
            prefixes = {
                'monitoring': 'NEURAPULSE_MONITORING_',
                'quantum': 'NEURAPULSE_QUANTUM_',
                'synergy': 'NEURAPULSE_SYNERGY_',
                'ai': 'NEURAPULSE_AI_',
                'gui': 'NEURAPULSE_GUI_',
                'logging': 'NEURAPULSE_LOGGING_',
                'performance': 'NEURAPULSE_PERFORMANCE_',
                'security': 'NEURAPULSE_SECURITY_',
                'network': 'NEURAPULSE_NETWORK_',
                'storage': 'NEURAPULSE_STORAGE_'
            }
            
            # Process each section
            for section, prefix in prefixes.items():
                if section not in self._config:
                    self._config[section] = {}
                    
                # Get all environment variables for this section
                env_vars = {k: v for k, v in os.environ.items() if k.startswith(prefix)}
                
                # Update configuration
                for key, value in env_vars.items():
                    # Remove prefix and convert to lowercase
                    config_key = key[len(prefix):].lower()
                    
                    # Convert value to appropriate type
                    if value.lower() == 'true':
                        value = True
                    elif value.lower() == 'false':
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    elif value.replace('.', '').isdigit():
                        value = float(value)
                    elif value.startswith('[') and value.endswith(']'):
                        # Handle list values
                        value = [item.strip() for item in value[1:-1].split(',')]
                        
                    self._config[section][config_key] = value
                    
        except Exception as e:
            logger.error(f"Error loading environment variables: {str(e)}")
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        try:
            return self._config.get(section, {}).get(key, default)
        except Exception as e:
            logger.error(f"Error getting configuration value: {str(e)}")
            return default
            
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section"""
        try:
            return self._config.get(section, {})
        except Exception as e:
            logger.error(f"Error getting configuration section: {str(e)}")
            return {}
            
    def set(self, section: str, key: str, value: Any):
        """Set a configuration value"""
        try:
            if section not in self._config:
                self._config[section] = {}
            self._config[section][key] = value
        except Exception as e:
            logger.error(f"Error setting configuration value: {str(e)}")
            
    def save(self):
        """Save current configuration to file"""
        try:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'settings.yaml'
            with open(config_path, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            
    def validate(self) -> bool:
        """Validate the configuration"""
        try:
            # Check required sections
            required_sections = ['monitoring', 'quantum', 'synergy', 'ai', 'gui']
            for section in required_sections:
                if section not in self._config:
                    logger.error(f"Missing required configuration section: {section}")
                    return False
                    
            # Validate monitoring settings
            monitoring = self._config['monitoring']
            if not isinstance(monitoring.get('update_interval'), (int, float)):
                logger.error("Invalid monitoring update interval")
                return False
                
            # Validate quantum settings
            quantum = self._config['quantum']
            if not isinstance(quantum.get('num_qubits'), int):
                logger.error("Invalid number of qubits")
                return False
                
            # Validate synergy settings
            synergy = self._config['synergy']
            if not isinstance(synergy.get('cpu_threshold'), (int, float)):
                logger.error("Invalid CPU threshold")
                return False
                
            # Validate AI settings
            ai = self._config['ai']
            if not isinstance(ai.get('learning_rate'), (int, float)):
                logger.error("Invalid learning rate")
                return False
                
            # Validate GUI settings
            gui = self._config['gui']
            if not isinstance(gui.get('window_width'), int):
                logger.error("Invalid window width")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating configuration: {str(e)}")
            return False
            
    def reload(self):
        """Reload configuration from file"""
        try:
            self._config.clear()
            self._load_config()
            logger.info("Configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Error reloading configuration: {str(e)}")
            
    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration"""
        return self._config.copy() 
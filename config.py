from dataclasses import dataclass
from typing import Tuple
import json

@dataclass
class GUIConfig:
    window_width: int = 1500
    window_height: int = 800
    timeline_height: int = 200
    node_list_width_ratio: float = 0.1
    
    # Colors
    node_color: str = 'lightblue'
    edge_color: str = 'grey'
    highlight_color: str = 'blue'
    flash_color: str = 'yellow'

@dataclass
class SimConfig:
    update_interval: int = 1000  # ms
    default_mode: str = 'SELFROLLING'
    
class Config:
    def __init__(self, config_file: str = 'config.json'):
        self.gui = GUIConfig()
        self.sim = SimConfig()
        self._load_config(config_file)
        
    def _load_config(self, config_file: str):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                
            # Update GUI config
            for key, value in config_data.get('gui', {}).items():
                if hasattr(self.gui, key):
                    setattr(self.gui, key, value)
                    
            # Update simulation config
            for key, value in config_data.get('sim', {}).items():
                if hasattr(self.sim, key):
                    setattr(self.sim, key, value)
                    
        except FileNotFoundError:
            print(f"Config file {config_file} not found, using defaults") 
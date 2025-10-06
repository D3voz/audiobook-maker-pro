import json
import os
from typing import Dict, Any, List


class SettingsManager:
    """Manages saving and loading of TTS settings"""
    
    def __init__(self, settings_dir: str = "presets"):
        self.settings_dir = settings_dir
        self.default_settings_file = "last_used.json"
        
        # Create settings directory if it doesn't exist
        if not os.path.exists(settings_dir):
            os.makedirs(settings_dir)
    
    def get_default_settings(self) -> dict:
        """Get default TTS settings"""
        return {
            "engine_type": "local",  # or "api"
            "api_url": "http://localhost:7778/v1",
            "model": "chatterbox",
            "voice": "",
            "device": "auto",
            "data_type": "float16",
            # Generation settings
            "exaggeration": 0.5,
            "cfg_weight": 0.5,
            "temperature": 0.8,
            "seed": -1,
            # Chunking settings
            "split_chunks": True,
            "desired_length": 200,
            "max_length": 300,
            "halve_first_chunk": False,
            # Advanced settings
            "max_new_tokens": 1000,
            "cache_length": 1500,
            "use_compilation": False,
        }
    
    def save_settings(self, settings: Dict[str, Any], filename: str = None) -> bool:
        """
        Save settings to a JSON file.
        
        Args:
            settings: Dictionary of settings to save
            filename: Name of the file (without path). If None, saves to default.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if filename is None:
            filename = self.default_settings_file
        
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self.settings_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def load_settings(self, filename: str = None) -> Dict[str, Any]:
        """
        Load settings from a JSON file.
        
        Args:
            filename: Name of the file (without path). If None, loads default.
        
        Returns:
            Dict: Settings dictionary, or empty dict if file doesn't exist
        """
        if filename is None:
            filename = self.default_settings_file
        
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = os.path.join(self.settings_dir, filename)
        
        if not os.path.exists(filepath):
            return {}
        
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}
    
    def get_preset_list(self) -> List[str]:
        """
        Get list of available preset files.
        
        Returns:
            List of preset names (without .json extension)
        """
        try:
            files = os.listdir(self.settings_dir)
            presets = [f[:-5] for f in files if f.endswith('.json')]
            # Remove default from list
            if self.default_settings_file[:-5] in presets:
                presets.remove(self.default_settings_file[:-5])
            return sorted(presets)
        except Exception as e:
            print(f"Error getting preset list: {e}")
            return []
    
    def delete_preset(self, filename: str) -> bool:
        """
        Delete a preset file.
        
        Args:
            filename: Name of the file to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not filename.endswith('.json'):
            filename += '.json'
        
        # Don't allow deleting the default settings
        if filename == self.default_settings_file:
            return False
        
        filepath = os.path.join(self.settings_dir, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False
    
    def preset_exists(self, filename: str) -> bool:
        """Check if a preset file exists"""
        if not filename.endswith('.json'):
            filename += '.json'
        filepath = os.path.join(self.settings_dir, filename)
        return os.path.exists(filepath)
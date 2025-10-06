"""
Utility for managing HuggingFace model cache.
"""

import os
from pathlib import Path
from typing import List, Dict


class ModelCacheManager:
    """Manages HuggingFace model cache for Chatterbox"""
    
    @staticmethod
    def get_cache_dir() -> Path:
        """Get HuggingFace cache directory"""
        hf_home = os.environ.get('HF_HOME')
        
        if not hf_home:
            if os.name == 'nt':  # Windows
                hf_home = os.path.join(
                    os.environ.get('USERPROFILE', ''), 
                    '.cache', 
                    'huggingface'
                )
            else:  # Linux/Mac
                hf_home = os.path.join(
                    os.path.expanduser('~'), 
                    '.cache', 
                    'huggingface'
                )
        
        return Path(hf_home) / 'hub'
    
    @staticmethod
    def list_cached_models() -> List[str]:
        """List all cached Chatterbox models"""
        cache_dir = ModelCacheManager.get_cache_dir()
        
        if not cache_dir.exists():
            return []
        
        models = []
        for model_dir in cache_dir.glob('models--*--chatterbox*'):
            models.append(model_dir.name)
        
        return models
    
    @staticmethod
    def get_model_info() -> Dict:
        """Get detailed information about cached models"""
        cache_dir = ModelCacheManager.get_cache_dir()
        
        info = {
            'cache_directory': str(cache_dir),
            'cache_exists': cache_dir.exists(),
            'models': []
        }
        
        if cache_dir.exists():
            for model_dir in cache_dir.glob('models--*--chatterbox*'):
                # Get model size
                total_size = sum(
                    f.stat().st_size 
                    for f in model_dir.rglob('*') 
                    if f.is_file()
                )
                
                info['models'].append({
                    'name': model_dir.name,
                    'path': str(model_dir),
                    'size_mb': total_size / (1024 * 1024),
                    'files': len(list(model_dir.rglob('*')))
                })
        
        return info
    
    @staticmethod
    def print_cache_info():
        """Print cache information to console"""
        info = ModelCacheManager.get_model_info()
        
        print("=" * 60)
        print("HuggingFace Model Cache Information")
        print("=" * 60)
        print(f"Cache Directory: {info['cache_directory']}")
        print(f"Cache Exists: {info['cache_exists']}")
        print(f"\nCached Models ({len(info['models'])}):")
        
        for model in info['models']:
            print(f"\n  📦 {model['name']}")
            print(f"     Path: {model['path']}")
            print(f"     Size: {model['size_mb']:.2f} MB")
            print(f"     Files: {model['files']}")
        
        if not info['models']:
            print("\n  No Chatterbox models found in cache.")
            print("  Models will be downloaded on first use.")
        
        print("=" * 60)
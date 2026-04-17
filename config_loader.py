"""
Krystal Configuration Loader
Handles loading and managing version-specific configurations
"""

import os
import yaml
from typing import Dict, Any, Optional


class Config:
    """
    Configuration manager for Krystal versions
    Loads YAML config files and provides feature flag access
    """
    
    def __init__(self, version: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            version: Version name ('basic', 'medium', 'advanced')
                     If None, reads from KRISTAL_VERSION environment variable
        """
        self.version = version or os.getenv('KRISTAL_VERSION', 'basic')
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        config_path = os.path.join(
            os.path.dirname(__file__), 
            'config', 
            f'{self.version}.yaml'
        )
        
        # Fallback to basic if specific version config doesn't exist
        if not os.path.exists(config_path):
            config_path = os.path.join(
                os.path.dirname(__file__), 
                'config', 
                'basic.yaml'
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            print(f"[Config] Loaded {self.version} configuration")
        except FileNotFoundError:
            print(f"[Config] Warning: Config file not found at {config_path}")
            self.config = self._get_default_config()
        except yaml.YAMLError as e:
            print(f"[Config] Error parsing YAML: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if loading fails"""
        return {
            'version': 'basic',
            'features': {
                'chat': True,
                'voice': True,
                'file_operations': True,
                'code_writer': True,
                'vector_memory': False,
                'trading': False,
                'multiple_providers': False,
                'project_context': False,
                'social_hub': False,
                'advanced_plugins': False,
                'dashboard': True,
                'memory_vault': False,
                'diary': False,
                'trading_hub': False,
                'api_keys': False,
            },
            'optimizations': {
                'lazy_loading': True,
                'minimal_animations': True,
                'cloud_services': True,
                'local_models': False,
            },
            'llm': {
                'primary_provider': 'groq',
                'fallback_provider': 'gemini',
                'max_tokens': 2048,
                'temperature': 0.7,
            },
            'voice': {
                'whisper_api': True,
                'local_model': False,
                'tts_enabled': True,
            },
            'database': {
                'mongodb_enabled': True,
                'pinecone_enabled': False,
                'local_search': True,
            },
            'resource_limits': {
                'max_memory_mb': 2048,
                'max_cpu_percent': 70,
                'max_concurrent_requests': 5,
            },
        }
    
    def is_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled
        
        Args:
            feature: Feature name (e.g., 'trading', 'voice', 'vector_memory')
        
        Returns:
            True if feature is enabled, False otherwise
        """
        return self.config.get('features', {}).get(feature, False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dot notation)
        
        Args:
            key: Configuration key (e.g., 'llm.max_tokens', 'optimizations.lazy_loading')
            default: Default value if key not found
        
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        
        return value if value is not None else default
    
    def get_features(self) -> Dict[str, bool]:
        """Get all feature flags"""
        return self.config.get('features', {})
    
    def get_optimizations(self) -> Dict[str, bool]:
        """Get all optimization settings"""
        return self.config.get('optimizations', {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.config.get('llm', {})
    
    def get_voice_config(self) -> Dict[str, bool]:
        """Get voice configuration"""
        return self.config.get('voice', {})
    
    def get_database_config(self) -> Dict[str, bool]:
        """Get database configuration"""
        return self.config.get('database', {})
    
    def get_resource_limits(self) -> Dict[str, int]:
        """Get resource limits"""
        return self.config.get('resource_limits', {})
    
    def get_version(self) -> str:
        """Get current version name"""
        return self.version
    
    def get_display_name(self) -> str:
        """Get version display name"""
        return self.config.get('display_name', 'Krystal')
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary (for API response)"""
        return {
            'version': self.version,
            'display_name': self.config.get('display_name', 'Krystal'),
            'description': self.config.get('description', ''),
            'features': self.get_features(),
            'optimizations': self.get_optimizations(),
        }


# Global config instance
_global_config: Optional[Config] = None


def get_config(version: Optional[str] = None) -> Config:
    """
    Get global configuration instance
    
    Args:
        version: Version name (only used on first call)
    
    Returns:
        Config instance
    """
    global _global_config
    
    if _global_config is None:
        _global_config = Config(version)
    
    return _global_config


def reload_config(version: Optional[str] = None) -> Config:
    """
    Reload configuration (useful for testing or version switching)
    
    Args:
        version: New version to load
    
    Returns:
        New Config instance
    """
    global _global_config
    _global_config = Config(version)
    return _global_config

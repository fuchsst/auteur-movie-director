# User Story: Service Configuration Model

**Story ID:** STORY-014  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Data Model & Configuration  
**Story Points:** 3  
**Priority:** Medium (P2)  

---

## Story Description

**As the** backend integration system  
**I want** a flexible configuration model for service endpoints  
**So that** users can easily configure services via environment variables, config files, or UI  

## Acceptance Criteria

### Functional Requirements
- [ ] Support multiple configuration sources (env vars, files, UI)
- [ ] Implement configuration precedence (env > file > UI > defaults)
- [ ] Validate configuration values
- [ ] Support dynamic configuration reloading
- [ ] Provide configuration templates
- [ ] Handle missing/invalid configurations gracefully
- [ ] Support both development and production configs
- [ ] Enable configuration debugging/inspection

### Technical Requirements
- [ ] Environment variable parsing
- [ ] YAML/JSON config file support
- [ ] Configuration schema validation
- [ ] Type-safe configuration access
- [ ] Configuration change detection
- [ ] Secure handling of sensitive data
- [ ] Cross-platform path handling
- [ ] Configuration inheritance/composition

### Quality Requirements
- [ ] Configuration loads in <100ms
- [ ] Clear error messages for invalid configs
- [ ] Zero configuration corruption
- [ ] Intuitive configuration structure
- [ ] Comprehensive validation
- [ ] Secure credential storage
- [ ] Easy debugging tools
- [ ] Complete documentation

## Implementation Notes

### Technical Approach

**Configuration Model:**
```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
import os
import yaml
import json

@dataclass
class ServiceEndpoint:
    """Configuration for a service endpoint"""
    url: str
    protocol: str = "http"
    timeout: float = 30.0
    retry_count: int = 3
    headers: Dict[str, str] = field(default_factory=dict)
    auth: Optional[Dict[str, str]] = None
    
@dataclass
class ServiceConfig:
    """Complete configuration for a backend service"""
    name: str
    enabled: bool = True
    endpoint: ServiceEndpoint = field(default_factory=ServiceEndpoint)
    health_check: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    custom_params: Dict[str, Any] = field(default_factory=dict)

class ConfigurationManager:
    """Manage service configurations from multiple sources"""
    
    def __init__(self):
        self.configs: Dict[str, ServiceConfig] = {}
        self.config_sources: List[str] = []
        self.schema_validator = ConfigSchemaValidator()
        
    def load_configurations(self):
        """Load configurations from all sources in precedence order"""
        # 1. Load defaults
        self.load_defaults()
        self.config_sources.append("defaults")
        
        # 2. Load from config file
        if config_file := self.find_config_file():
            self.load_from_file(config_file)
            self.config_sources.append(f"file:{config_file}")
            
        # 3. Load from environment variables
        self.load_from_environment()
        if self._has_env_vars():
            self.config_sources.append("environment")
            
        # 4. Load from Blender properties (UI)
        self.load_from_blender_props()
        self.config_sources.append("blender_ui")
        
        # 5. Validate final configuration
        self.validate_all_configs()
```

**Environment Variable Support:**
```python
class EnvironmentConfigLoader:
    """Load configuration from environment variables"""
    
    # Environment variable patterns
    ENV_PATTERNS = {
        'url': 'MOVIE_DIRECTOR_{SERVICE}_URL',
        'enabled': 'MOVIE_DIRECTOR_{SERVICE}_ENABLED',
        'timeout': 'MOVIE_DIRECTOR_{SERVICE}_TIMEOUT',
        'api_key': 'MOVIE_DIRECTOR_{SERVICE}_API_KEY',
    }
    
    def load_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Load config for a service from environment"""
        service_upper = service_name.upper()
        
        # Check if any env vars exist for this service
        url_var = self.ENV_PATTERNS['url'].format(SERVICE=service_upper)
        if url := os.environ.get(url_var):
            config = ServiceConfig(name=service_name)
            
            # Load URL (required)
            config.endpoint.url = url
            
            # Load optional settings
            if enabled := os.environ.get(self.ENV_PATTERNS['enabled'].format(SERVICE=service_upper)):
                config.enabled = enabled.lower() in ('true', '1', 'yes')
                
            if timeout := os.environ.get(self.ENV_PATTERNS['timeout'].format(SERVICE=service_upper)):
                try:
                    config.endpoint.timeout = float(timeout)
                except ValueError:
                    logger.warning(f"Invalid timeout value: {timeout}")
                    
            # Load authentication if present
            if api_key := os.environ.get(self.ENV_PATTERNS['api_key'].format(SERVICE=service_upper)):
                config.endpoint.auth = {'api_key': api_key}
                
            return config
            
        return None
```

**Configuration File Support:**
```python
class FileConfigLoader:
    """Load configuration from YAML/JSON files"""
    
    CONFIG_SEARCH_PATHS = [
        Path.home() / '.movie-director' / 'config.yaml',
        Path.home() / '.movie-director' / 'config.json',
        Path.cwd() / 'movie-director.yaml',
        Path.cwd() / 'movie-director.json',
        Path('/etc/movie-director/config.yaml'),  # Linux system-wide
    ]
    
    def find_config_file(self) -> Optional[Path]:
        """Find the first available config file"""
        for path in self.CONFIG_SEARCH_PATHS:
            if path.exists():
                return path
        return None
        
    def load_from_file(self, filepath: Path) -> Dict[str, ServiceConfig]:
        """Load configurations from file"""
        configs = {}
        
        try:
            # Load based on extension
            if filepath.suffix == '.yaml' or filepath.suffix == '.yml':
                with open(filepath, 'r') as f:
                    data = yaml.safe_load(f)
            elif filepath.suffix == '.json':
                with open(filepath, 'r') as f:
                    data = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {filepath.suffix}")
                
            # Parse services section
            if 'services' in data:
                for service_name, service_data in data['services'].items():
                    config = self.parse_service_config(service_name, service_data)
                    configs[service_name] = config
                    
        except Exception as e:
            logger.error(f"Error loading config file {filepath}: {e}")
            
        return configs
```

**Configuration Schema:**
```yaml
# Example configuration file schema
version: "1.0"
services:
  comfyui:
    enabled: true
    endpoint:
      url: "ws://localhost:8188"
      protocol: "websocket"
      timeout: 30.0
      retry_count: 3
    health_check:
      endpoint: "/system_stats"
      interval: 30
      timeout: 5
    capabilities:
      - image_generation
      - video_generation
    resource_limits:
      max_concurrent_jobs: 5
      max_vram_gb: 24
      
  litellm:
    enabled: true
    endpoint:
      url: "http://localhost:8000"
      protocol: "http"
      timeout: 60.0
      headers:
        Content-Type: "application/json"
      auth:
        type: "bearer"
        token: "${LITELLM_API_KEY}"  # Environment variable reference
    capabilities:
      - text_generation
      - chat_completion
```

**Configuration Validation:**
```python
class ConfigSchemaValidator:
    """Validate configuration against schema"""
    
    REQUIRED_FIELDS = {
        'endpoint.url': str,
        'name': str,
    }
    
    OPTIONAL_FIELDS = {
        'enabled': bool,
        'endpoint.timeout': float,
        'endpoint.retry_count': int,
        'capabilities': list,
    }
    
    def validate_service_config(self, config: ServiceConfig) -> List[str]:
        """Validate a service configuration"""
        errors = []
        
        # Check required fields
        for field_path, expected_type in self.REQUIRED_FIELDS.items():
            value = self._get_nested_value(config, field_path)
            if value is None:
                errors.append(f"Missing required field: {field_path}")
            elif not isinstance(value, expected_type):
                errors.append(f"Invalid type for {field_path}: expected {expected_type.__name__}")
                
        # Validate URL format
        if config.endpoint.url:
            if not self._is_valid_url(config.endpoint.url):
                errors.append(f"Invalid URL format: {config.endpoint.url}")
                
        # Validate numeric ranges
        if config.endpoint.timeout <= 0:
            errors.append("Timeout must be positive")
            
        if config.endpoint.retry_count < 0:
            errors.append("Retry count must be non-negative")
            
        return errors
```

**Configuration Templates:**
```python
class ConfigTemplateGenerator:
    """Generate configuration templates for users"""
    
    def generate_default_config(self) -> Dict:
        """Generate a complete default configuration"""
        return {
            'version': '1.0',
            'services': {
                'comfyui': {
                    'enabled': True,
                    'endpoint': {
                        'url': 'ws://localhost:8188',
                        'protocol': 'websocket',
                        'timeout': 30.0
                    }
                },
                'litellm': {
                    'enabled': True,
                    'endpoint': {
                        'url': 'http://localhost:8000',
                        'protocol': 'http',
                        'timeout': 60.0
                    }
                },
                # ... other services
            }
        }
        
    def generate_development_config(self) -> Dict:
        """Generate config for development environment"""
        config = self.generate_default_config()
        
        # Add development-specific settings
        for service in config['services'].values():
            service['debug'] = True
            service['endpoint']['timeout'] = 120.0  # Longer timeouts for debugging
            
        return config
```

**Dynamic Configuration Reloading:**
```python
class ConfigReloadHandler:
    """Handle dynamic configuration reloading"""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.file_watcher = None
        self.last_reload = 0
        
    def enable_auto_reload(self, config_file: Path):
        """Enable automatic config reloading on file changes"""
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        class ConfigFileHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path == str(config_file):
                    self.reload_configuration()
                    
        self.file_watcher = Observer()
        self.file_watcher.schedule(
            ConfigFileHandler(),
            path=str(config_file.parent),
            recursive=False
        )
        self.file_watcher.start()
        
    def reload_configuration(self):
        """Reload configuration from all sources"""
        # Debounce rapid changes
        if time.time() - self.last_reload < 1.0:
            return
            
        logger.info("Reloading configuration...")
        self.config_manager.load_configurations()
        self.last_reload = time.time()
        
        # Notify system of config changes
        bpy.ops.movie_director.configuration_reloaded()
```

### Configuration Access API
```python
def get_service_config(service_name: str) -> ServiceConfig:
    """Get configuration for a specific service"""
    config_manager = get_config_manager()
    return config_manager.configs.get(service_name)
    
def get_service_url(service_name: str) -> str:
    """Get URL for a service with all overrides applied"""
    config = get_service_config(service_name)
    return config.endpoint.url if config else None
```

## Testing Strategy

### Unit Tests
```python
class TestConfiguration(unittest.TestCase):
    def test_env_var_loading(self):
        # Set env vars
        # Load config
        # Verify precedence
        
    def test_file_loading(self):
        # Create test configs
        # Load from file
        # Verify parsing
        
    def test_validation(self):
        # Test valid/invalid configs
        # Verify error messages
```

### Integration Tests
- Test configuration precedence
- Test with real config files
- Verify environment handling
- Test reload functionality

## Dependencies
- YAML/JSON parsing libraries
- Environment variable access
- File system operations
- STORY-013: Integrates with persistence

## Related Stories
- Used by all connection stories
- Configured via STORY-006 (UI)
- Validated by connection attempts

## Definition of Done
- [ ] Multiple config sources working
- [ ] Precedence order correct
- [ ] Validation comprehensive
- [ ] Environment variables supported
- [ ] Config files loading
- [ ] Templates available
- [ ] Reload functionality working
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] DevOps Engineer
- [ ] QA Engineer
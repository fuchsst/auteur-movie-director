# User Story: Connection State Persistence

**Story ID:** STORY-013  
**Epic:** EPIC-001 (Backend Service Connectivity)  
**Component Type:** Data Model & Persistence  
**Story Points:** 3  
**Priority:** Medium (P2)  

---

## Story Description

**As a** Blender user  
**I want** my backend connection settings to persist across sessions  
**So that** I don't need to reconfigure services every time I open Blender  

## Acceptance Criteria

### Functional Requirements
- [ ] Save connection URLs and ports in .blend file
- [ ] Preserve service enable/disable states
- [ ] Store last successful connection info
- [ ] Remember custom configuration overrides
- [ ] Support project-specific settings
- [ ] Migrate settings between addon versions
- [ ] Import/export configuration profiles
- [ ] Reset to defaults option

### Technical Requirements
- [ ] Use Blender custom properties for storage
- [ ] Implement version migration system
- [ ] JSON serialization for complex data
- [ ] Atomic save operations
- [ ] Backward compatibility support
- [ ] Efficient property updates
- [ ] Type-safe property definitions
- [ ] Property change callbacks

### Quality Requirements
- [ ] Settings load instantly (<100ms)
- [ ] Zero data corruption
- [ ] Seamless version upgrades
- [ ] Clear property organization
- [ ] Minimal .blend file bloat
- [ ] Reliable save/load cycle
- [ ] Property validation
- [ ] Comprehensive defaults

## Implementation Notes

### Technical Approach

**Connection Properties Definition:**
```python
class ServiceConnectionProperties(PropertyGroup):
    """Properties for a single backend service connection"""
    
    # Basic connection info
    enabled: BoolProperty(
        name="Enabled",
        description="Enable this backend service",
        default=True,
        update=on_connection_settings_changed
    )
    
    url: StringProperty(
        name="Service URL",
        description="Backend service endpoint",
        default="",
        maxlen=1024,
        update=on_connection_settings_changed
    )
    
    # Connection state
    last_connected: StringProperty(
        name="Last Connected",
        description="Timestamp of last successful connection",
        default=""
    )
    
    connection_status: EnumProperty(
        name="Status",
        items=[
            ('unknown', "Unknown", "Connection not tested"),
            ('connected', "Connected", "Successfully connected"),
            ('disconnected', "Disconnected", "Not connected"),
            ('error', "Error", "Connection error")
        ],
        default='unknown'
    )
    
    # Advanced settings
    connection_timeout: FloatProperty(
        name="Connection Timeout",
        description="Timeout for connection attempts (seconds)",
        default=30.0,
        min=1.0,
        max=300.0
    )
    
    retry_count: IntProperty(
        name="Retry Count",
        description="Number of connection retry attempts",
        default=3,
        min=0,
        max=10
    )
    
    # Service-specific data (JSON)
    custom_data: StringProperty(
        name="Custom Data",
        description="Service-specific configuration (JSON)",
        default="{}"
    )

class MovieDirectorProperties(PropertyGroup):
    """Main property group for Movie Director addon"""
    
    # Connection properties for each service
    comfyui_connection: PointerProperty(type=ServiceConnectionProperties)
    wan2gp_connection: PointerProperty(type=ServiceConnectionProperties)
    litellm_connection: PointerProperty(type=ServiceConnectionProperties)
    rvc_connection: PointerProperty(type=ServiceConnectionProperties)
    audioldm_connection: PointerProperty(type=ServiceConnectionProperties)
    
    # Global settings
    auto_connect_on_startup: BoolProperty(
        name="Auto-Connect on Startup",
        description="Automatically connect to services when addon loads",
        default=True
    )
    
    connection_profile: StringProperty(
        name="Connection Profile",
        description="Active connection profile name",
        default="default"
    )
    
    # Version for migration
    config_version: IntProperty(
        name="Config Version",
        description="Configuration schema version",
        default=1
    )
```

**Property Registration:**
```python
def register_properties():
    """Register all property groups"""
    bpy.utils.register_class(ServiceConnectionProperties)
    bpy.utils.register_class(MovieDirectorProperties)
    
    # Add to scene
    bpy.types.Scene.movie_director_props = PointerProperty(
        type=MovieDirectorProperties
    )
    
def unregister_properties():
    """Unregister property groups"""
    del bpy.types.Scene.movie_director_props
    
    bpy.utils.unregister_class(MovieDirectorProperties)
    bpy.utils.unregister_class(ServiceConnectionProperties)
```

**Connection Settings Management:**
```python
class ConnectionSettingsManager:
    """Manage connection settings persistence"""
    
    def __init__(self):
        self.default_urls = {
            'comfyui': 'ws://localhost:8188',
            'wan2gp': 'http://localhost:7860',
            'litellm': 'http://localhost:8000',
            'rvc': 'http://localhost:7865',
            'audioldm': 'http://localhost:7863'
        }
        
    def initialize_defaults(self, scene):
        """Initialize default connection settings"""
        props = scene.movie_director_props
        
        # Set defaults for each service
        for service, default_url in self.default_urls.items():
            conn_prop = getattr(props, f"{service}_connection")
            if not conn_prop.url:
                conn_prop.url = default_url
                
    def save_profile(self, scene, profile_name: str):
        """Save current settings as a profile"""
        props = scene.movie_director_props
        profile_data = {
            'version': props.config_version,
            'services': {}
        }
        
        # Collect all service settings
        for service in BACKEND_SERVICES:
            conn_prop = getattr(props, f"{service}_connection")
            profile_data['services'][service] = {
                'enabled': conn_prop.enabled,
                'url': conn_prop.url,
                'timeout': conn_prop.connection_timeout,
                'retry_count': conn_prop.retry_count,
                'custom_data': json.loads(conn_prop.custom_data)
            }
            
        # Save to addon preferences
        prefs = get_addon_preferences()
        profiles = json.loads(prefs.connection_profiles)
        profiles[profile_name] = profile_data
        prefs.connection_profiles = json.dumps(profiles)
        
    def load_profile(self, scene, profile_name: str):
        """Load settings from a profile"""
        prefs = get_addon_preferences()
        profiles = json.loads(prefs.connection_profiles)
        
        if profile_name not in profiles:
            raise ValueError(f"Profile '{profile_name}' not found")
            
        profile_data = profiles[profile_name]
        
        # Check version compatibility
        if profile_data['version'] != scene.movie_director_props.config_version:
            profile_data = self.migrate_profile(profile_data)
            
        # Apply settings
        props = scene.movie_director_props
        for service, settings in profile_data['services'].items():
            conn_prop = getattr(props, f"{service}_connection")
            conn_prop.enabled = settings['enabled']
            conn_prop.url = settings['url']
            conn_prop.connection_timeout = settings['timeout']
            conn_prop.retry_count = settings['retry_count']
            conn_prop.custom_data = json.dumps(settings['custom_data'])
```

**Property Change Callbacks:**
```python
def on_connection_settings_changed(self, context):
    """Called when connection settings change"""
    # Mark service for reconnection
    service_name = self.name.replace('_connection', '')
    
    if connection_manager := get_connection_manager():
        connection_manager.mark_for_reconnection(service_name)
        
    # Update UI
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
```

**Version Migration System:**
```python
class ConfigMigration:
    """Handle configuration version migrations"""
    
    def migrate_to_version_2(self, old_data: Dict) -> Dict:
        """Migrate from v1 to v2 schema"""
        new_data = {
            'version': 2,
            'services': {}
        }
        
        # Example: Add new fields with defaults
        for service, settings in old_data.get('services', {}).items():
            new_settings = settings.copy()
            new_settings['health_check_enabled'] = True
            new_settings['health_check_interval'] = 30
            new_data['services'][service] = new_settings
            
        return new_data
        
    def migrate_profile(self, profile_data: Dict) -> Dict:
        """Migrate profile to current version"""
        current_version = 1  # Current schema version
        data_version = profile_data.get('version', 1)
        
        # Apply migrations sequentially
        if data_version < 2 and current_version >= 2:
            profile_data = self.migrate_to_version_2(profile_data)
            
        # Add more migrations as needed
        
        return profile_data
```

**Import/Export Functionality:**
```python
class MOVIE_DIRECTOR_OT_export_settings(Operator):
    bl_idname = "movie_director.export_settings"
    bl_label = "Export Connection Settings"
    
    filepath: StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        """Export settings to JSON file"""
        props = context.scene.movie_director_props
        
        export_data = {
            'addon': 'movie_director',
            'version': props.config_version,
            'timestamp': datetime.now().isoformat(),
            'settings': self.collect_all_settings(props)
        }
        
        with open(self.filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        self.report({'INFO'}, f"Settings exported to {self.filepath}")
        return {'FINISHED'}
```

### Blender Integration
- Properties stored in Scene data
- Saved automatically with .blend file
- Available in all scenes
- UI updates via property callbacks

### Default Values
```python
DEFAULT_CONNECTIONS = {
    'comfyui': {
        'url': 'ws://localhost:8188',
        'enabled': True,
        'timeout': 30.0
    },
    'litellm': {
        'url': 'http://localhost:8000',
        'enabled': True,
        'timeout': 60.0
    }
    # ... etc
}
```

## Testing Strategy

### Unit Tests
```python
class TestConnectionPersistence(unittest.TestCase):
    def test_property_registration(self):
        # Verify properties register
        # Check default values
        
    def test_save_load_cycle(self):
        # Save settings
        # Load in new scene
        # Verify persistence
        
    def test_profile_management(self):
        # Create profiles
        # Switch between them
        # Verify isolation
```

### Integration Tests
- Test with actual .blend files
- Verify cross-session persistence
- Test migration system
- Profile import/export

## Dependencies
- Blender property system
- JSON for complex data
- STORY-006: Configuration UI uses these properties

## Related Stories
- Properties displayed in STORY-005 (Status Panel)
- Modified by STORY-006 (Configuration UI)
- Used by STORY-011 (Reconnection) for URLs

## Definition of Done
- [ ] Properties defined and registered
- [ ] Settings persist in .blend file
- [ ] Default values initialized
- [ ] Profile system working
- [ ] Import/export functional
- [ ] Migration system tested
- [ ] No data corruption
- [ ] Documentation complete

---

**Sign-off:**
- [ ] Development Lead
- [ ] Technical Architect
- [ ] QA Engineer